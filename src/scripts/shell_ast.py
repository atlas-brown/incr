"""Shared libdash parsing and Shasta compatibility."""
import libdash
import shasta.ast_node as ast
from shasta.json_to_ast import to_ast_node

_initialized = False

# Shasta 0.5 callers pass quote_mode to CommandNode.pretty, whose signature omits it.
_pretty = ast.CommandNode.pretty
_code = getattr(_pretty, '__code__', None)
if _code is not None and not hasattr(_pretty, '__wrapped__'):
    _parameters = _code.co_varnames[:_code.co_argcount + _code.co_kwonlyargcount]
else:
    # Keep compatibility with decorated or extension implementations without
    # importing Python's complete introspection stack for ordinary functions.
    import inspect
    _parameters = inspect.signature(_pretty).parameters
if 'quote_mode' not in _parameters:
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
