"""Shared libdash parsing and Shasta compatibility."""
import inspect

import libdash
import shasta.ast_node as ast
from shasta.json_to_ast import to_ast_node

_initialized = False

# Shasta 0.5 callers pass quote_mode to CommandNode.pretty, whose signature omits it.
if 'quote_mode' not in inspect.signature(ast.CommandNode.pretty).parameters:
    _command_pretty = ast.CommandNode.pretty

    def _pretty_command(command, ignore_heredocs=False, quote_mode=None):
        return _command_pretty(command, ignore_heredocs)

    ast.CommandNode.pretty = _pretty_command


def parse_dash_script(path):
    global _initialized
    parsed = libdash.parser.parse(path, init=not _initialized)
    _initialized = True
    return [(to_ast_node(node), source, first_line, last_line)
            for node, source, first_line, last_line in parsed]
