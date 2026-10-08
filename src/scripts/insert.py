#!/usr/bin/env python3
import argparse
import copy
from dataclasses import dataclass, field
import logging
from pathlib import Path
import os
import re
import shlex
import shutil
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
UNSAFE_STARRED_POSITIONAL_PATTERNS = (
    b"$@",
    b"$*",
    b"${@",
    b"${*",
)
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
    AST.PipeNode: ("items",),
    AST.CommandNode: ("arguments", "assignments"),
    AST.AssignNode: ("val",),
    AST.BArgChar: ("node",),
    AST.QArgChar: ("arg",),
    AST.DefunNode: ("body",),
    AST.ForNode: ("body", "argument"),
    AST.WhileNode: ("test", "body"),
    AST.SemiNode: ("left_operand", "right_operand"),
    AST.RedirNode: ("node", "redir_list"),
}


def transform_node(node, prefix_words):
    if isinstance(node, list):
        return [transform_node(child, prefix_words) for child in node]
    fields = DASH_CHILD_FIELDS.get(type(node))
    if fields is None:
        return node
    transformed = copy.copy(node)
    for field_name in fields:
        setattr(transformed, field_name, transform_node(getattr(node, field_name), prefix_words))
    if isinstance(transformed, AST.CommandNode) and transformed.arguments:
        first_word = transformed.arguments[0]
        if all(hasattr(character, "char") for character in first_word):
            command_name = "".join(chr(character.char) for character in first_word)
            if command_name not in AVOID_SET and shutil.which(command_name):
                transformed.arguments = [*copy.deepcopy(prefix_words), *transformed.arguments]
    return transformed


def transform_ast(ast, prefix_words):
    return [transform_node(node, prefix_words) for node, _, _, _ in ast]


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


def transform_bash_node(node, prefix_words, state):
    if isinstance(node, BashAST.CondCom):
        transformed = copy.copy(node)
        transformed.left = transform_bash_node(node.left, prefix_words, state)
        transformed.right = transform_bash_node(node.right, prefix_words, state)
        return transformed
    if not isinstance(node, BashAST.Command):
        return node
    if node.type == BashAST.CommandType.CM_SIMPLE:
        command = node.value.simple_com
        if not command.words:
            return node
        name = command.words[0].word.decode("utf8", errors="surrogateescape")
        if (not name or name in AVOID_SET or "=" in name
                or name in state.functions or name in state.aliases
                or name.startswith(("$", "%")) or not shutil.which(name)):
            return node
        if any(pattern in word.word for word in command.words
               for pattern in (*UNSAFE_STARRED_POSITIONAL_PATTERNS, b"<(")):
            return node
        transformed = copy.deepcopy(node)
        transformed.value.simple_com.words = [
            *copy.deepcopy(prefix_words), *transformed.value.simple_com.words,
        ]
        state.modified = True
        return transformed
    if node.type == BashAST.CommandType.CM_CASE:
        transformed = copy.deepcopy(node)
        for clause in transformed.value.case_com.clauses:
            clause.action = transform_bash_node(clause.action, prefix_words, state)
        return transformed
    fields = BASH_CHILD_FIELDS.get(node.type.value)
    if fields is None:
        return node
    attribute, children = fields
    transformed = copy.deepcopy(node)
    command = getattr(transformed.value, attribute)
    for child in children:
        setattr(command, child, transform_bash_node(getattr(command, child), prefix_words, state))
    return transformed


@dataclass
class TransformState:
    functions: set[str] = field(default_factory=set)
    aliases: set[str] = field(default_factory=set)
    modified: bool = False
    dynamic_aliases: bool = False


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


def transform_bash_ast(ast, prefix_words, state):
    nodes = []
    for node in ast:
        transformed = transform_bash_node(node, prefix_words, state)
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


def transform_bash_script(arguments, prefix_words, source_bytes):
    original_ast = libbash.bash_to_ast(arguments.path)
    state = collect_bash_bindings(original_ast)
    if state.dynamic_aliases and not arguments.identity:
        return source_bytes
    if arguments.identity:
        transformed_ast = original_ast
    else:
        transformed_ast = transform_bash_ast(original_ast, prefix_words, state)
    if not arguments.identity and not state.modified:
        return source_bytes
    with tempfile.NamedTemporaryFile(mode="wb+", suffix=".sh") as temp_file:
        libbash.ast_to_bash(transformed_ast, temp_file.name)
        temp_file.flush()
        raw_bytes = temp_file.read()
        transformed_code = raw_bytes.decode("utf-8", errors="surrogateescape")
        transformed_code = dequote_bash_internal_escapes(transformed_code)
    if not transformed_code.endswith("\n"):
        transformed_code += "\n"
    return transformed_code.encode("utf-8", errors="surrogateescape")


def transform_script(arguments):
    source_bytes = Path(arguments.path).read_bytes()
    # Let the executing shell diagnose incomplete input exactly once.
    checked = subprocess.run([os.environ.get("INCR_SHELL", "bash"), "-n", arguments.path],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    if requires_original_source(source_bytes) or checked.returncode != 0 or checked.stderr:
        return source_bytes

    prefix_words = parse_prefix(command_prefix(arguments), arguments.bash) if not arguments.identity else []
    if arguments.bash:
        return transform_bash_script(arguments, prefix_words, source_bytes)
    original_ast = parse_dash_script(arguments.path)
    transformed = ([node for node, *_ in original_ast] if arguments.identity
                   else transform_ast(original_ast, prefix_words))
    code = ast_to_code(transformed)
    if not code.endswith("\n"):
        code += "\n"
    return code.encode("utf-8", errors="surrogateescape")


def main():
    arguments = parse_arguments()
    logging.basicConfig(level=logging.DEBUG if arguments.debug else logging.INFO)
    try:
        output = transform_script(arguments)
    except Exception as error:
        print(f"Error transforming {arguments.path}: {error}", file=sys.stderr)
        if arguments.debug:
            raise RuntimeError(f"Error transforming {arguments.path}") from error
        raise SystemExit(1)

    if arguments.output:
        Path(arguments.output).write_bytes(output)
    else:
        sys.stdout.buffer.write(output)
    if arguments.execute and arguments.output is not None:
        raise SystemExit(subprocess.run([os.environ.get("INCR_SHELL", "bash"), arguments.output]).returncode)


if __name__ == "__main__":
    main()
