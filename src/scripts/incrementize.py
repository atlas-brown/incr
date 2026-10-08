import argparse
import copy
import logging
from pathlib import Path

import shasta.ast_node as ast

from shell_ast import parse_dash_script


def flatten_sequence(command):
    if isinstance(command, ast.SemiNode):
        return flatten_sequence(command.left_operand) + flatten_sequence(command.right_operand)
    return [command]


def rebuild_sequence(commands):
    if not commands:
        raise ValueError('cannot build an empty command sequence')
    sequence = commands[0]
    for command in commands[1:]:
        sequence = ast.SemiNode(sequence, command)
    return sequence


def incremental_nodes(node):
    if isinstance(node, ast.PipeNode):
        for length in range(1, len(node.items) + 1):
            partial = copy.deepcopy(node)
            partial.items = partial.items[:length]
            yield partial
    elif isinstance(node, (ast.ForNode, ast.WhileNode)):
        commands = flatten_sequence(node.body)
        for length in range(1, len(commands) + 1):
            partial = copy.deepcopy(node)
            partial.body = rebuild_sequence(commands[:length])
            yield partial
    else:
        yield copy.deepcopy(node)


def incremental_scripts(parsed):
    """Yield complete preceding commands followed by each prefix of the next node."""
    preceding = []
    for node, *_ in parsed:
        for partial in incremental_nodes(node):
            yield [*preceding, partial]
        preceding.append(node)


def main():
    parser = argparse.ArgumentParser(description='Generate scripts with incremental changes.')
    parser.add_argument('path', type=Path, help='Input script')
    parser.add_argument('output', type=Path, help='Output directory')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if arguments.debug else logging.INFO)
    arguments.output.mkdir(parents=True, exist_ok=True)
    parsed = parse_dash_script(str(arguments.path))
    for index, nodes in enumerate(incremental_scripts(parsed)):
        output = arguments.output / f'{index}_{arguments.path.stem}'
        output.write_text('\n'.join(node.pretty() for node in nodes) + '\n')


if __name__ == '__main__':
    main()
