import shasta.ast_node as AST
import argparse
import libdash
from shasta.json_to_ast import to_ast_node
import logging

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
            arguments = [transform_node(arg, sys_path) for arg in node.arguments]
            arguments = [str_to_ast(sys_path)] + arguments
            return AST.CommandNode(
                    arguments=arguments,
                    **{k: v for k, v in vars(node).items() if k != "arguments"})
        case AST.BArgChar():
            return AST.BArgChar(
                    node=transform_node(node.node, sys_path),
                    **{k: v for k, v in vars(node).items() if k != "node"})
        case AST.QArgChar():
            return AST.QArgChar(
                    arg=[transform_node(n, sys_path) for n in node.arg],
                    **{k: v for k, v in vars(node).items() if k != "arg"})
        case list() if all(isinstance(x, AST.ArgChar) for x in node):
            return [transform_node(n, sys_path) for n in node]
        case _:
            logging.debug(f"No transformation for node: {node}")
            return node

def transform_ast(ast, sys_path):
    return [transform_node(node, sys_path) for node, _, _, _ in ast]

def ast_to_code(ast):
    return "\n".join([node.pretty() for node in ast])

def main():
    sys_name = "incr"
    sys_path = "path/to/incr"
    arg_parser = argparse.ArgumentParser(
        description=f"Inserts {sys_name} into a shell script and outputs the modified script"
    )
    arg_parser.add_argument("path", help="Path to the script")
    arg_parser.add_argument("-o", "--output", help="Path to save the transformed script (stdout if empty)", default=None)
    arg_parser.add_argument("--sys-path", help=f"Path to the {sys_name} executable", default=sys_path)
    arg_parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    args = arg_parser.parse_args()
    
    sys_path = args.sys_path
    original_ast = parse_shell_to_asts(args.path)
    transformed_ast = transform_ast(original_ast, sys_path)
    transformed_code = ast_to_code(transformed_ast)
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.ERROR)
    if args.output:
        with open(args.output, "w") as f:
            f.write(transformed_code)
    else:
        print(transformed_code)

if __name__ == "__main__":
    main()
