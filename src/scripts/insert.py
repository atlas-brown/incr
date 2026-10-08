#!/usr/bin/env python3
import argparse
import shlex
import subprocess
import shutil
import libbash
import libbash.bash_command as BashAST
import libbash.ctypes_bash_command as c_bash
import libdash
import logging
import os
import shasta.ast_node as AST
from shasta.json_to_ast import to_ast_node
import sys
import tempfile
import copy
from dataclasses import dataclass, field
import re

sys.setrecursionlimit(10000)


# Ensure these match config.rs
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
    "fc",
    "set",
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
    "exec",
    # TODO: Remove
    "strmatch",
    "cat",
    "cp",
    "mkfifo",
    "_intl_normalize_spaces",
    "_cut_leading_spaces",
    "a",
    "/",
    r"/bin/sh",
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

# Monkey patch
# TODO: Fix this in libdash
old_pretty = AST.CommandNode.pretty
AST.CommandNode.pretty = lambda self, ignore_heredocs=False, quote_mode=None: old_pretty(self, ignore_heredocs)

INITIALIZE_LIBDASH = True
# Parses straight a shell script to an AST
# through python without calling it as an executable
def parse_shell_to_asts(input_script_path : str):
    global INITIALIZE_LIBDASH
    new_ast_objects = libdash.parser.parse(input_script_path,init=INITIALIZE_LIBDASH)
    INITIALIZE_LIBDASH = False
    # Transform the untyped ast objects to typed ones
    new_ast_objects = list(new_ast_objects)
    typed_ast_objects = []
    for (
        untyped_ast,
        original_text,
        linno_before,
        linno_after,
    ) in new_ast_objects:
        typed_ast = to_ast_node(untyped_ast)
        typed_ast_objects.append(
            (typed_ast, original_text, linno_before, linno_after)
        )
    return typed_ast_objects

def parse_bash_to_asts(input_script_path : str):
    return libbash.bash_to_ast(input_script_path)

def str_to_ast(s : str):
    return [AST.CArgChar(char=ord(c)) for c in s]

def transform_node(node, sys_path):
    match node:
        case AST.PipeNode():
            return AST.PipeNode(
            items=[transform_node(node, sys_path) for node in node.items],
            **{k: v for k, v in vars(node).items() if k != "items"}
            )
        case AST.CommandNode():
            if not node.arguments and not node.assignments:
                return node
            assignments = [transform_node(ass, sys_path) for ass in node.assignments]
            arguments = [transform_node(arg, sys_path) for arg in node.arguments]

            # ----- INCR -----
            if arguments and all(hasattr(c, "char") for c in arguments[0]): # Don't append sys to assignments
                command_name = "".join(chr(c.char) for c in arguments[0])
                if command_name not in AVOID_SET and shutil.which(command_name): # Let the shell diagnose unresolved commands
                    arguments = [str_to_ast(sys_path)] + arguments
            # ----- INCR -----

            return AST.CommandNode(
                    arguments=arguments,
                    assignments=assignments,
                    **{k: v for k, v in vars(node).items() if k not in ("arguments", "assignments")})
        case AST.AssignNode():
            val = [transform_node(v, sys_path) for v in node.val]
            return AST.AssignNode(
                    val=val,
                    **{k: v for k, v in vars(node).items() if k != "val"})
        case AST.BArgChar():
            return AST.BArgChar(
                    node=transform_node(node.node, sys_path),
                    **{k: v for k, v in vars(node).items() if k != "node"})
        case AST.QArgChar():
            return AST.QArgChar(
                    arg=[transform_node(n, sys_path) for n in node.arg],
                    **{k: v for k, v in vars(node).items() if k != "arg"})
        case AST.DefunNode():
            return AST.DefunNode(
                body=transform_node(node.body, sys_path),
                **{k: v for k, v in vars(node).items() if k != "body"}
            )
        case AST.ForNode():
            return AST.ForNode(
                body=transform_node(node.body, sys_path),
                argument=[transform_node(n, sys_path) for n in node.argument],
                **{k: v for k, v in vars(node).items() if k not in ("body", "argument")}
            )
        case AST.WhileNode():
            return AST.WhileNode(
                    test=transform_node(node.test, sys_path),
                    body=transform_node(node.body, sys_path),
                    **{k: v for k, v in vars(node).items() if k not in ("test", "body")})
        case AST.SemiNode():
            return AST.SemiNode(
                    left_operand=transform_node(node.left_operand, sys_path),
                    right_operand=transform_node(node.right_operand, sys_path),
                    **{k: v for k, v in vars(node).items() if k not in ("left_operand", "right_operand")})
        case AST.RedirNode():
            return AST.RedirNode(
                    node=transform_node(node.node, sys_path),
                    redir_list=[transform_node(n, sys_path) for n in node.redir_list],
                    **{k: v for k, v in vars(node).items() if k not in ("node", "redir_list")})
        case AST.FileRedirNode():
            return node
        case list() if all(isinstance(x, AST.ArgChar) for x in node):
            return [transform_node(n, sys_path) for n in node]
        case _:
            logging.debug(f"Leaving node unchanged: {type(node)} {node}")
            return node

def transform_ast(ast, sys_path):
    return [transform_node(node, sys_path) for node, _, _, _ in ast]

def transform_bash_node(node, sys_path, state):
    def contains_starred_positional_expansion(word: bytes) -> bool:
        return any(pattern in word for pattern in UNSAFE_STARRED_POSITIONAL_PATTERNS)

    def handle_command_node(node: BashAST.Command, sys_path):
        match node.type:
            case BashAST.CommandType.CM_SIMPLE:
                assert node.value.simple_com
                cmd = node.value.simple_com
                if not len(cmd.words): return node
                # ----- INCR -----
                cmd_name = str(cmd.words[0].word, "utf8", errors="surrogateescape")
                logging.debug(f"Handling simple command {cmd_name} {[str(word.word) for word in cmd.words]}")
                logging.debug(f"State: {state}")
                if cmd_name == 'alias' and len(cmd.words) > 1:
                    alias_name = str(cmd.words[1].word, "utf8", errors="surrogateescape").split('=')[0]
                    state.aliases.add(alias_name)
                if cmd_name in AVOID_SET or '=' in cmd_name: # Don't append sys to built-in commands or assignments
                    return node
                if cmd_name in state.functions or cmd_name in state.aliases:
                    return node
                if not shutil.which(cmd_name):
                    # Commands created or resolved later remain native shell
                    # calls, preserving command-not-found hooks and status.
                    return node
                if cmd_name[0] in ('$', '%'): # Don't append sys to variables or job identifiers
                    return node
                if any(contains_starred_positional_expansion(word.word) for word in cmd.words):
                    return node
                if any([b'<(' in word.word for word in cmd.words]):
                    return node
                words = [BashAST.WordDesc(c_bash.word_desc(bytes(sys_path, "utf8"), 0))] + cmd.words
                # ----- INCR -----
                state.modified = True
                node_copy = copy.deepcopy(node)
                node_copy.value.simple_com.words = words
                return node_copy
            case BashAST.CommandType.CM_CONNECTION:
                assert node.value.connection
                first = transform_bash_node(node.value.connection.first, sys_path, state)
                second = transform_bash_node(node.value.connection.second, sys_path, state)
                node_copy = copy.deepcopy(node)
                node_copy.value.connection.first = first
                node_copy.value.connection.second = second
                return node_copy
            case BashAST.CommandType.CM_GROUP:
                assert node.value.group_com
                command = transform_bash_node(node.value.group_com.command, sys_path, state)
                node_copy = copy.deepcopy(node)
                node_copy.value.group_com.command = command
                return node_copy
            case BashAST.CommandType.CM_IF:
                assert node.value.if_com
                test = transform_bash_node(node.value.if_com.test, sys_path, state)
                true_case = transform_bash_node(node.value.if_com.true_case, sys_path, state)
                false_case = transform_bash_node(node.value.if_com.false_case, sys_path, state) if node.value.if_com.false_case else None
                node_copy = copy.deepcopy(node)
                node_copy.value.if_com.test = test
                node_copy.value.if_com.true_case = true_case
                node_copy.value.if_com.false_case = false_case
                return node_copy
            case BashAST.CommandType.CM_WHILE:
                assert node.value.while_com
                test = transform_bash_node(node.value.while_com.test, sys_path, state)
                action = transform_bash_node(node.value.while_com.action, sys_path, state)
                node_copy = copy.deepcopy(node)
                node_copy.value.while_com.test = test
                node_copy.value.while_com.action = action
                return node_copy
            case BashAST.CommandType.CM_FOR:
                assert node.value.for_com
                action = transform_bash_node(node.value.for_com.action, sys_path, state)
                node_copy = copy.deepcopy(node)
                node_copy.value.for_com.action = action
                return node_copy
            case BashAST.CommandType.CM_COND:
                assert node.value.cond_com
                left = transform_bash_node(node.value.cond_com.left, sys_path, state)
                right = transform_bash_node(node.value.cond_com.right, sys_path, state)
                node_copy = copy.deepcopy(node)
                node_copy.value.cond_com.left = left
                node_copy.value.cond_com.right = right
                return node_copy
            case BashAST.CommandType.CM_FUNCTION_DEF:
                assert node.value.function_def
                name = str(node.value.function_def.name.word, "utf8")
                state.functions.add(name)
                body = transform_bash_node(node.value.function_def.command, sys_path, state)
                node_copy = copy.deepcopy(node)
                node_copy.value.function_def.command = body
                return node_copy
            case BashAST.CommandType.CM_SUBSHELL:
                assert node.value.subshell_com
                sub_command = transform_bash_node(node.value.subshell_com.command, sys_path, state)
                node_copy = copy.deepcopy(node)
                node_copy.value.subshell_com.command = sub_command
                return node_copy
            case BashAST.CommandType.CM_CASE:
                assert node.value.case_com
                def handle_pattern(pattern):
                    if not pattern.action: return pattern
                    action = transform_bash_node(pattern.action, sys_path, state)
                    pattern_copy = copy.deepcopy(pattern)
                    pattern_copy.action = action
                    return pattern_copy
                clauses = [handle_pattern(pat) for pat in node.value.case_com.clauses]
                node_copy = copy.deepcopy(node)
                node_copy.value.case_com.clauses = clauses
                return node_copy
            case _:
                logging.debug(f"Ignoring bash command node: {node} with type {node.type}")
                return node

    match node:
        case BashAST.Command():
            return handle_command_node(node, sys_path)
        case BashAST.CondCom():
            left = transform_bash_node(node.left, sys_path, state)
            right = transform_bash_node(node.right, sys_path, state)
            node_copy = copy.deepcopy(node)
            node_copy.left = left
            node_copy.right = right
            return node_copy
        case _:
            logging.debug(f"Leaving bash node unchanged: {node}")
            return node

@dataclass
class State:
    functions: set[str] = field(default_factory=set)
    aliases: set[str] = field(default_factory=set)
    modified: bool = False

def transform_bash_ast(ast, sys_path, state):
    nodes = []
    for node in ast:
        t_node = transform_bash_node(node, sys_path, state)
        nodes.append(t_node)
    return nodes


def ast_to_code(ast):
    return "\n".join([node.pretty() for node in ast])

def preserve_line_numbers(path: str):
    lines = []
    with open(path) as file:
        # check for empty or comment-only lines and preserve them
        empty_re = re.compile(r"^[ \t]*(#.*)?\s*$")
        for line in file:
            if empty_re.match(line):
                line = f"incr__no_op\n"
            lines.append(line)
    return "".join(lines)

def strip_no_op_lines(code: str):
    lines = []
    for line in code.splitlines(keepends=True):
        if "incr__no_op" in line:
            line = "\n"
        lines.append(line)
    return "".join(lines)


def dequote_bash_internal_escapes(code: str):
    result = []
    i = 0
    while i < len(code):
        if (
            code[i] == BASH_CTLESC
            and i + 1 < len(code)
            and code[i + 1] in (BASH_CTLESC, BASH_CTLNUL)
        ):
            result.append(code[i + 1])
            i += 2
            continue
        result.append(code[i])
        i += 1
    return "".join(result)

def main():
    sys_name = "incr"
    sys_path = "~/incr/target/release/incr"
    arg_parser = argparse.ArgumentParser(
        description=f"Inserts {sys_name} into a shell script and outputs the modified script"
    )
    arg_parser.add_argument("path", help="Path to the script")
    arg_parser.add_argument("-o", "--output", help="Path to save the transformed script (stdout if empty)", default=None)
    arg_parser.add_argument("-e", "--execute", action="store_true", help="Execute the transformed script")
    arg_parser.add_argument("--sys-path", help=f"Path to the {sys_name} executable", default=sys_path)
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
    arg_parser.add_argument("--identity", action="store_true", help=f"Output parsed script without inserting {sys_name}")
    args = arg_parser.parse_args()
    
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    prefix = [args.sys_path]
    if args.try_path:
        prefix.extend(["--try", args.try_path])
    if args.cache_path:
        prefix.extend(["--cache", args.cache_path])
    if args.observe_path:
        prefix.extend(["--observe", args.observe_path])
    sys_path = shlex.join(prefix)

    state = State()
    script_path = args.path

    with open(args.path, "rb") as source_file:
        source_bytes = source_file.read()
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

    # Parsing an incomplete here-document can print warnings and then rewrite
    # its contents. Let the executing shell handle such input exactly once.
    checked = subprocess.run([os.environ.get("INCR_SHELL", "bash"), "-n", args.path],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    if source_sensitive or checked.returncode != 0 or checked.stderr:
        original = source_bytes
        if args.output:
            with open(args.output, "wb") as output_file:
                output_file.write(original)
        else:
            sys.stdout.buffer.write(original)
        return

    try:
        if args.bash:
            original_ast = parse_bash_to_asts(args.path)
            if args.identity:
                transformed_ast = original_ast
            else:
                # Do transform_bash_ast twice to populate function definitions
                _ = transform_bash_ast(original_ast, sys_path, state)
                transformed_ast = transform_bash_ast(original_ast, sys_path, state)
            if not args.identity and not state.modified:
                with open(args.path, "rb") as file:
                    raw_bytes = file.read()
                transformed_code = raw_bytes.decode("utf-8", errors="surrogateescape")
            else:
                with tempfile.NamedTemporaryFile(mode="wb+", suffix=".sh") as temp_file:
                    libbash.ast_to_bash(transformed_ast, temp_file.name)
                    temp_file.flush()
                    raw_bytes = temp_file.read()
                    transformed_code = raw_bytes.decode("utf-8", errors="surrogateescape")
                    transformed_code = dequote_bash_internal_escapes(transformed_code)
                    transformed_code = strip_no_op_lines(transformed_code)
        else:
            original_ast = parse_shell_to_asts(args.path)
            transformed_ast = transform_ast(original_ast, sys_path)
            transformed_code = ast_to_code(transformed_ast)
    except Exception as e:
        print(f"Error inserting {sys_name} into script {script_path}: {e}", file=sys.stderr)
        with open(args.path, "rb") as file:
            raw_bytes = file.read()
            transformed_code = raw_bytes.decode("utf-8", errors="surrogateescape")
        if args.debug:
            raise Exception(f"Error inserting {sys_name} into script {script_path}: {e}")
        sys.exit(1)

    if not transformed_code.endswith("\n") and (args.identity or state.modified or not args.bash):
        transformed_code += "\n"
    output = args.output or sys.stdout

    if args.output:
        with open(output, "w", encoding="utf-8", errors="surrogateescape") as f:
            f.write(transformed_code)
    else:
        sys.stdout.buffer.write(transformed_code.encode("utf-8", errors="surrogateescape"))
    if args.execute and args.output is not None:
        raise SystemExit(subprocess.run([os.environ.get("INCR_SHELL", "bash"), args.output]).returncode)

if __name__ == "__main__":
    main()
