#!/usr/bin/env python3
import argparse
import copy
from collections import deque
from dataclasses import dataclass, field
import hashlib
import logging
from pathlib import Path
import os
import posixpath
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile

import libbash
import libbash.bash_command as BashAST
import shasta.ast_node as AST

from shell_ast import parse_dash_script

sys.setrecursionlimit(10000)


# Commands that must retain shell state, live interactions or nondeterministic behavior.
IGNORE_COMMANDS = [
    # Built-in commands from `compgen -b`
    "alias",
    "bg",
    "bind",
    "break",
    "builtin",
    "caller",
    "cd",
    "command",
    "compgen",
    "complete",
    "compopt",
    "continue",
    "declare",
    "dirs",
    "disown",
    "echo",
    "enable",
    "eval",
    "exec",
    "exit",
    "export",
    "false",
    "fc",
    "fg",
    "getopts",
    "hash",
    "help",
    "history",
    "jobs",
    "kill",
    "let",
    "local",
    "logout",
    "mapfile",
    "popd",
    "printf",
    "pushd",
    "pwd",
    "read",
    "readarray",
    "readonly",
    "return",
    "set",
    "shift",
    "shopt",
    "source",
    "suspend",
    "test",
    "[",
    "times",
    "trap",
    "true",
    "type",
    "typeset",
    "ulimit",
    "umask",
    "unalias",
    "unset",
    "wait",
    ":", # no-op command
    ".", # source command
    # Additional untraced metadata commands
    "chgrp",
    "chmod",
    "chown",
    "env",
    "ln",
    "mount",
    "mktemp",
    "date",
    "shuf",
    "uuidgen",
    "printenv",
    "sleep",
    "stat",
    "stty",
    "sync",
    "touch",
    "mkdir",
    "umount",
    "yes",
    # Shell test helpers and commands whose live interaction must be retained.
    "strmatch",
    "cat",
    "cp",
    "mkfifo",
]
AVOID_SET = set(IGNORE_COMMANDS)


BASH_CTLESC = "\x01"
BASH_CTLNUL = "\x7f"


def parse_prefix(arguments, use_bash):
    """Build real argument nodes with the same parser used for the source script."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", encoding="utf-8") as source:
        source.write(shlex.join(arguments) + "\n")
        source.flush()
        if use_bash:
            return libbash.bash_to_ast(source.name)[0].value.simple_com.words
        return parse_dash_script(source.name)[0][0].arguments


DASH_CHILD_FIELDS = {
    AST.AndNode: ("left_operand", "right_operand"),
    AST.OrNode: ("left_operand", "right_operand"),
    AST.PipeNode: ("items",),
    AST.CommandNode: ("arguments", "assignments"),
    AST.AssignNode: ("val",),
    AST.BArgChar: ("node",),
    AST.QArgChar: ("arg",),
    AST.DefunNode: ("body",),
    AST.ForNode: ("body", "argument"),
    AST.IfNode: ("cond", "then_b", "else_b"),
    AST.WhileNode: ("test", "body"),
    AST.SemiNode: ("left_operand", "right_operand"),
    AST.RedirNode: ("node", "redir_list"),
}


def transform_node(node, prefix_words, state, plan=None, relative_paths=True):
    if isinstance(node, list):
        return [
            transform_node(child, prefix_words, state, plan, relative_paths)
            for child in node
        ]
    fields = DASH_CHILD_FIELDS.get(type(node))
    transformed = copy.copy(node) if fields is not None else node
    if fields is not None:
        for field_name in fields:
            setattr(
                transformed,
                field_name,
                transform_node(
                    getattr(node, field_name), prefix_words, state, plan, relative_paths
                ),
            )
    if isinstance(transformed, AST.CommandNode) and transformed.arguments:
        first_word = transformed.arguments[0]
        if all(hasattr(character, "char") for character in first_word):
            command_name = "".join(chr(character.char) for character in first_word)
            available = shutil.which(command_name) or (
                plan is not None
                and plan.resolve_executable(command_name, relative_paths) is not None
            )
            if command_name not in AVOID_SET and available:
                nested = None
                if plan is not None:
                    nested = plan.instrumented_script_command(
                        command_name,
                        transformed.arguments[1:],
                        False,
                        relative_paths,
                    )
                if nested is None:
                    transformed.arguments = [
                        *copy.deepcopy(prefix_words), *transformed.arguments
                    ]
                else:
                    fixed_args, remaining = nested
                    transformed.arguments = [
                        *parse_prefix(fixed_args, False),
                        *copy.deepcopy(remaining),
                    ]
                state.modified = True
    return transformed


def transform_ast(ast, prefix_words, state, plan=None, relative_paths=True):
    return [
        transform_node(node, prefix_words, state, plan, relative_paths)
        for node, _, _, _ in ast
    ]


BASH_CHILD_FIELDS = {
    BashAST.CommandType.CM_CONNECTION.value: ("connection", ("first", "second")),
    BashAST.CommandType.CM_GROUP.value: ("group_com", ("command",)),
    BashAST.CommandType.CM_IF.value: ("if_com", ("test", "true_case", "false_case")),
    BashAST.CommandType.CM_WHILE.value: ("while_com", ("test", "action")),
    BashAST.CommandType.CM_UNTIL.value: ("while_com", ("test", "action")),
    BashAST.CommandType.CM_FOR.value: ("for_com", ("action",)),
    BashAST.CommandType.CM_COND.value: ("cond_com", ("left", "right")),
    BashAST.CommandType.CM_FUNCTION_DEF.value: ("function_def", ("command",)),
    BashAST.CommandType.CM_SUBSHELL.value: ("subshell_com", ("command",)),
}


def transform_bash_node(node, prefix_words, state, plan=None, relative_paths=True):
    if isinstance(node, BashAST.CondCom):
        transformed = copy.copy(node)
        transformed.left = transform_bash_node(
            node.left, prefix_words, state, plan, relative_paths
        )
        transformed.right = transform_bash_node(
            node.right, prefix_words, state, plan, relative_paths
        )
        return transformed
    if not isinstance(node, BashAST.Command):
        return node
    if node.type == BashAST.CommandType.CM_SIMPLE:
        command = node.value.simple_com
        if not command.words:
            return node
        name = command.words[0].word.decode("utf8", errors="surrogateescape")
        available = shutil.which(name) or (
            plan is not None
            and plan.resolve_executable(name, relative_paths) is not None
        )
        if (not name or name in AVOID_SET or "=" in name
                or name in state.functions or name in state.aliases
                or name.startswith(("$", "%")) or not available):
            return node
        transformed = copy.deepcopy(node)
        nested = None
        if plan is not None:
            nested = plan.instrumented_script_command(
                name,
                transformed.value.simple_com.words[1:],
                True,
                relative_paths,
            )
        if nested is None:
            transformed.value.simple_com.words = [
                *copy.deepcopy(prefix_words), *transformed.value.simple_com.words,
            ]
        else:
            fixed_args, remaining = nested
            transformed.value.simple_com.words = [
                *parse_prefix(fixed_args, True),
                *copy.deepcopy(remaining),
            ]
        state.modified = True
        return transformed
    if node.type == BashAST.CommandType.CM_CASE:
        transformed = copy.deepcopy(node)
        for clause in transformed.value.case_com.clauses:
            clause.action = transform_bash_node(
                clause.action, prefix_words, state, plan, relative_paths
            )
        return transformed
    fields = BASH_CHILD_FIELDS.get(node.type.value)
    if fields is None:
        return node
    attribute, children = fields
    transformed = copy.deepcopy(node)
    command = getattr(transformed.value, attribute)
    for child in children:
        setattr(
            command,
            child,
            transform_bash_node(
                getattr(command, child), prefix_words, state, plan, relative_paths
            ),
        )
    return transformed


@dataclass
class TransformState:
    functions: set[str] = field(default_factory=set)
    aliases: set[str] = field(default_factory=set)
    modified: bool = False
    dynamic_aliases: bool = False


class RecursivePlan:
    def __init__(self, arguments):
        self.arguments = arguments
        self.rootfs = arguments.rootfs
        self.cwd = arguments.cwd
        self.path = arguments.target_path.split(os.pathsep) if arguments.target_path else []
        self.output_dir = Path(arguments.recursive_dir) if arguments.recursive_dir else None
        self.container_dir = arguments.recursive_dest
        self.active = set()
        self.outputs = {}

    def rootfs_path(self, path):
        if not self.rootfs or not path.startswith("/"):
            return None
        pending = deque(path.split("/"))
        resolved = []
        links = 0
        while pending:
            part = pending.popleft()
            if part in ("", "."):
                continue
            if part == "..":
                if resolved:
                    resolved.pop()
                continue
            candidate = Path(self.rootfs, *resolved, part)
            try:
                metadata = os.lstat(candidate)
            except OSError:
                return None
            if stat.S_ISLNK(metadata.st_mode):
                links += 1
                if links > 40:
                    return None
                target = os.readlink(candidate)
                if target.startswith("/"):
                    resolved.clear()
                pending.extendleft(reversed(target.split("/")))
            else:
                resolved.append(part)
        return "/" + "/".join(resolved)

    def resolve_executable(self, command, relative_paths):
        if not self.rootfs:
            return None
        if "/" in command:
            candidates = [
                command if command.startswith("/") else
                posixpath.join(self.cwd, command) if relative_paths else ""
            ]
        else:
            candidates = [
                posixpath.join(directory or self.cwd, command)
                for directory in self.path
                if directory.startswith("/") or relative_paths
            ]
        for candidate in candidates:
            if not candidate:
                continue
            resolved = self.rootfs_path(posixpath.normpath(candidate))
            if not resolved:
                continue
            host_path = Path(self.rootfs, resolved.lstrip("/"))
            try:
                metadata = os.stat(host_path)
            except OSError:
                continue
            if stat.S_ISREG(metadata.st_mode) and metadata.st_mode & 0o111:
                return resolved, host_path
        return None

    @staticmethod
    def literal_word(word, use_bash):
        if use_bash:
            value = word.word.decode("utf8", errors="surrogateescape")
        else:
            if not all(hasattr(character, "char") for character in word):
                return None
            value = "".join(chr(character.char) for character in word)
        if not re.fullmatch(r"[A-Za-z0-9_./+@:-]+", value):
            return None
        return value

    def script_interpreter(self, script_path):
        host_path = Path(self.rootfs, script_path.lstrip("/"))
        try:
            with host_path.open("rb") as script:
                first_line = script.readline(256).decode("utf-8", errors="replace").strip()
        except OSError:
            return None
        if first_line not in ("#!/bin/sh", "#!/bin/bash"):
            return None
        interpreter = first_line[2:]
        resolved = self.rootfs_path(interpreter)
        if not resolved:
            return None
        mode = "bash" if interpreter.endswith("/bash") else "sh"
        if mode == "sh" and not interpreter.endswith("/sh"):
            return None
        return interpreter, mode

    def transform_file(self, script_path, mode):
        if self.output_dir is None or script_path in self.active:
            return None
        output_key = (script_path, mode)
        if output_key in self.outputs:
            return self.outputs[output_key]
        source_path = Path(self.rootfs, script_path.lstrip("/"))
        try:
            source_bytes = source_path.read_bytes()
        except OSError:
            return None
        if requires_original_source(source_bytes):
            return None

        self.active.add(script_path)
        try:
            child_args = copy.copy(self.arguments)
            child_args.path = str(source_path)
            child_args.bash = mode == "bash"
            transformed, modified = transform_script_bytes(
                child_args,
                source_bytes,
                self,
                not re.search(rb"\b(?:cd|pushd|popd)\b", source_bytes),
            )
        finally:
            self.active.remove(script_path)
        if not modified:
            return None

        self.output_dir.mkdir(parents=True, exist_ok=True)
        name = hashlib.sha256(f"{script_path}\0{mode}".encode()).hexdigest() + ".sh"
        output_path = self.output_dir / name
        output_path.write_bytes(transformed)
        container_path = posixpath.join(self.container_dir, name)
        self.outputs[output_key] = container_path
        return container_path

    def instrumented_script_command(self, command, argument_words, use_bash, relative_paths):
        command_executable = self.resolve_executable(command, relative_paths)
        if not command_executable:
            return None

        interpreter = None
        mode = None
        script_argument_index = 0
        script_argument = command
        if command_executable[0].endswith(("/bash", "/sh")):
            words = [self.literal_word(word, use_bash) for word in argument_words]
            if words and words[0] == "--":
                script_argument_index = 1
            if len(words) <= script_argument_index or words[script_argument_index] is None:
                return None
            if script_argument_index > 0 and len(words) < 2:
                return None
            script_argument = words[script_argument_index]
            interpreter = command
            mode = "bash" if command_executable[0].endswith("/bash") else "sh"
        else:
            interpreter_info = self.script_interpreter(command_executable[0])
            if interpreter_info is None:
                return None
            interpreter, mode = interpreter_info

        if "/" in script_argument:
            if script_argument.startswith("/"):
                target = script_argument
            elif relative_paths:
                target = posixpath.join(self.cwd, script_argument)
            else:
                return None
        else:
            target = None
            for directory in self.path:
                if directory.startswith("/") or relative_paths:
                    candidate = posixpath.join(directory or self.cwd, script_argument)
                    if self.rootfs_path(posixpath.normpath(candidate)):
                        target = candidate
                        break
            if target is None:
                return None
        resolved_script = self.rootfs_path(posixpath.normpath(target))
        if not resolved_script:
            return None
        transformed_path = self.transform_file(resolved_script, mode)
        if transformed_path is None:
            return None

        if command_executable[0].endswith(("/bash", "/sh")):
            remaining = argument_words[script_argument_index + 1:]
            script_argv0 = script_argument
        else:
            remaining = argument_words
            script_argv0 = command
        launch_script = 'script=$1; shift; . "$script" "$@"'
        # Cache the transformed commands inside the script, not this whole call.
        fixed_args = [
            interpreter,
            "-c",
            launch_script,
            script_argv0,
            transformed_path,
        ]
        return fixed_args, remaining


def record_aliases(words, state):
    if not words:
        return
    try:
        command = shlex.split(words[0].word.decode("utf8", errors="surrogateescape"))
        offset = 1
        if command in (["builtin"], ["command"]) and len(words) > 1:
            command = shlex.split(words[1].word.decode("utf8", errors="surrogateescape"))
            offset = 2
    except ValueError:
        return
    if command != ["alias"]:
        return
    for word in words[offset:]:
        try:
            assignments = shlex.split(word.word.decode("utf8", errors="surrogateescape"))
        except ValueError:
            state.dynamic_aliases = True
            continue
        for assignment in assignments:
            name, separator, _ = assignment.partition("=")
            if "$" in name or "`" in name:
                state.dynamic_aliases = True
            elif separator:
                state.aliases.add(name)


def collect_bash_bindings(nodes):
    """Collect shell-local names without constructing a discarded transformed tree."""
    state = TransformState()
    pending = list(nodes)
    while pending:
        node = pending.pop()
        if isinstance(node, BashAST.CondCom):
            pending.extend([node.left, node.right])
            continue
        if not isinstance(node, BashAST.Command):
            continue
        if node.type == BashAST.CommandType.CM_FUNCTION_DEF:
            state.functions.add(node.value.function_def.name.word.decode("utf8", errors="surrogateescape"))
        elif node.type == BashAST.CommandType.CM_SIMPLE:
            words = node.value.simple_com.words
            record_aliases(words, state)
        if node.type == BashAST.CommandType.CM_CASE:
            pending.extend(clause.action for clause in node.value.case_com.clauses)
        else:
            fields = BASH_CHILD_FIELDS.get(node.type.value)
            if fields:
                attribute, children = fields
                command = getattr(node.value, attribute)
                pending.extend(getattr(command, child) for child in children)
    return state


def transform_bash_ast(ast, prefix_words, state, plan=None, relative_paths=True):
    nodes = []
    for node in ast:
        transformed = transform_bash_node(
            node, prefix_words, state, plan, relative_paths
        )
        nodes.append(transformed)
    return nodes


def ast_to_code(ast):
    return "\n".join([node.pretty() for node in ast])


def dequote_bash_internal_escapes(code: str):
    result = []
    index = 0
    while index < len(code):
        if (
            code[index] == BASH_CTLESC
            and index + 1 < len(code)
            and code[index + 1] in (BASH_CTLESC, BASH_CTLNUL)
        ):
            result.append(code[index + 1])
            index += 2
            continue
        result.append(code[index])
        index += 1
    return "".join(result)

def parse_arguments():
    program_name = "incr"
    incr_command = "~/incr/target/release/incr"
    arg_parser = argparse.ArgumentParser(
        description=f"Inserts {program_name} into a shell script and outputs the modified script"
    )
    arg_parser.add_argument("path", help="Path to the script")
    arg_parser.add_argument("-o", "--output", help="Path to save the transformed script (stdout if empty)", default=None)
    arg_parser.add_argument("-e", "--execute", action="store_true", help="Execute the transformed script")
    arg_parser.add_argument("--sys-path", dest="incr_command", help=f"Path to the {program_name} executable", default=incr_command)
    arg_parser.add_argument("--try-path", help=f"Path to the try.sh script", default=None)
    arg_parser.add_argument(
        "--cache-path",
        nargs="?",
        const="/tmp/incr_cache",
        default="/tmp/incr_cache",
        help="Path to the cache directory",
    )
    arg_parser.add_argument("--observe-path", help="Observe binary path", default=None)
    arg_parser.add_argument("--status-path", help="Write whether commands were instrumented")
    arg_parser.add_argument("--rootfs", help="Target rootfs used for script discovery")
    arg_parser.add_argument("--cwd", default="/", help="RUN working directory in the target rootfs")
    arg_parser.add_argument("--target-path", default=os.environ.get("PATH", ""))
    arg_parser.add_argument("--recursive-dir", help="Host directory for transformed child scripts")
    arg_parser.add_argument("--recursive-dest", default="/incrd-trace/recursive")
    arg_parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    arg_parser.add_argument("--bash", action="store_true", help="Use bash parser (experimental)")
    arg_parser.add_argument("--identity", action="store_true", help=f"Output parsed script without inserting {program_name}")
    return arg_parser.parse_args()


def command_prefix(arguments):
    prefix = [arguments.incr_command]
    if arguments.try_path:
        prefix.extend(["--try", arguments.try_path])
    if arguments.cache_path:
        prefix.extend(["--cache", arguments.cache_path])
    if arguments.observe_path:
        prefix.extend(["--observe", arguments.observe_path])

    return prefix


def requires_original_source(source_bytes):
    """Conservatively preserve constructs whose behavior depends on source text."""
    # AST pretty-printing cannot preserve history's source text or the timing
    # of locale-sensitive ANSI-C quote expansion. Keep these native to Bash.
    source_sensitive = (re.search(rb"(?:^|[;\n])\s*(?:history|fc)(?:\s|$)", source_bytes) is not None
                        or b"$'" in source_bytes and re.search(rb"\\(?:[uUxX]|[0-7])", source_bytes) is not None
                        or re.search(rb"(?:^|[;\n])\s*set\s+(?:-r|-H|-o\s+(?:restricted|history|histexpand))(?:\s|$)", source_bytes) is not None
                        or re.search(rb"(?:<|\bcat\s+)[^\n;]*\$[\{]?0", source_bytes) is not None)

    source_sensitive = source_sensitive or any(name in source_bytes for name in
        (b"LINENO", b"BASH_SOURCE", b"BASH_EXECUTION_STRING", b"BASH_ARGV", b"BASH_COMMAND", b"FUNCNAME"))
    source_sensitive = source_sensitive or bool(os.environ.get("BASH_ENV"))
    # Variable listings include source-stack arrays even without naming them.
    source_sensitive = source_sensitive or re.search(
        rb"(?:^|[;\n])\s*(?:declare|typeset)(?:\s+-[a-zA-Z]+)*\s*(?:[;|\n]|$)", source_bytes) is not None

    return source_sensitive


def transform_bash_script(
    arguments, prefix_words, source_bytes, plan=None, relative_paths=True
):
    original_ast = libbash.bash_to_ast(arguments.path)
    state = collect_bash_bindings(original_ast)
    if state.dynamic_aliases and not arguments.identity:
        return source_bytes, False
    if arguments.identity:
        transformed_ast = original_ast
    else:
        transformed_ast = transform_bash_ast(
            original_ast, prefix_words, state, plan, relative_paths
        )
    if not arguments.identity and not state.modified:
        return source_bytes, False
    with tempfile.NamedTemporaryFile(mode="wb+", suffix=".sh") as temp_file:
        libbash.ast_to_bash(transformed_ast, temp_file.name)
        temp_file.flush()
        raw_bytes = temp_file.read()
        transformed_code = raw_bytes.decode("utf-8", errors="surrogateescape")
        transformed_code = dequote_bash_internal_escapes(transformed_code)
    if not transformed_code.endswith("\n"):
        transformed_code += "\n"
    output = transformed_code.encode("utf-8", errors="surrogateescape")
    return output, state.modified


def transform_script_bytes(arguments, source_bytes, plan=None, relative_paths=True):
    # Let the executing shell diagnose incomplete input exactly once.
    checked = subprocess.run([os.environ.get("INCR_SHELL", "bash"), "-n", arguments.path],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    if requires_original_source(source_bytes) or checked.returncode != 0 or checked.stderr:
        return source_bytes, False

    prefix_words = parse_prefix(command_prefix(arguments), arguments.bash) if not arguments.identity else []
    if arguments.bash:
        return transform_bash_script(
            arguments, prefix_words, source_bytes, plan, relative_paths
        )
    original_ast = parse_dash_script(arguments.path)
    state = TransformState()
    transformed = ([node for node, *_ in original_ast] if arguments.identity
                   else transform_ast(
                       original_ast, prefix_words, state, plan, relative_paths
                   ))
    code = ast_to_code(transformed)
    if not code.endswith("\n"):
        code += "\n"
    output = code.encode("utf-8", errors="surrogateescape")
    return output, state.modified


def transform_script(arguments):
    source_bytes = Path(arguments.path).read_bytes()
    plan = RecursivePlan(arguments) if arguments.rootfs and arguments.recursive_dir else None
    relative_paths = not re.search(rb"\b(?:cd|pushd|popd)\b", source_bytes)
    return transform_script_bytes(arguments, source_bytes, plan, relative_paths)


def main():
    arguments = parse_arguments()
    logging.basicConfig(level=logging.DEBUG if arguments.debug else logging.INFO)
    try:
        output, modified = transform_script(arguments)
    except Exception as error:
        print(f"Error transforming {arguments.path}: {error}", file=sys.stderr)
        if arguments.debug:
            raise RuntimeError(f"Error transforming {arguments.path}") from error
        raise SystemExit(1)

    if arguments.output:
        Path(arguments.output).write_bytes(output)
    else:
        sys.stdout.buffer.write(output)
    if arguments.status_path:
        Path(arguments.status_path).write_text(
            "transformed\n" if modified else "unchanged\n",
            encoding="utf-8",
        )
    if arguments.execute and arguments.output is not None:
        raise SystemExit(subprocess.run([os.environ.get("INCR_SHELL", "bash"), arguments.output]).returncode)


if __name__ == "__main__":
    main()
