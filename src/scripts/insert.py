import argparse
import libdash
import logging
import os
import shasta.ast_node as AST
from shasta.json_to_ast import to_ast_node

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
    logging.debug(f"Transforming node: {type(node)} {node}")
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
            if arguments: # Don't append sys to assignments
                arguments = [str_to_ast(sys_path)] + arguments
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
        case list() if all(isinstance(x, AST.ArgChar) for x in node):
            return [transform_node(n, sys_path) for n in node]
        case _:
            logging.debug(f"Leaving node unchanged: {type(node)} {node}")
            return node

def transform_ast(ast, sys_path):
    logging.debug(f"Transforming {ast=}")
    return [transform_node(node, sys_path) for node, _, _, _ in ast]

def ast_to_code(ast):
    return "\n".join([node.pretty() for node in ast])

def main():
    sys_name = "incr"
    sys_path = "/users/jxia3/incr/target/release/incr"
    arg_parser = argparse.ArgumentParser(
        description=f"Inserts {sys_name} into a shell script and outputs the modified script"
    )
    arg_parser.add_argument("path", help="Path to the script")
    arg_parser.add_argument("-o", "--output", help="Path to save the transformed script (stdout if empty)", default=None)
    arg_parser.add_argument("-e", "--execute", action="store_true", help="Execute the transformed script")
    arg_parser.add_argument("--sys-path", help=f"Path to the {sys_name} executable", default=sys_path)
    arg_parser.add_argument("--try-path", help=f"Path to the try.sh script", default=None)
    arg_parser.add_argument("--cache-path", help="Path to the cache directory", default=None)
    arg_parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    args = arg_parser.parse_args()
    
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    sys_path = f"{args.sys_path} --try-path {args.try_path} --cache-dir {args.cache_path}" if args.try_path and args.cache_path else args.sys_path
    original_ast = parse_shell_to_asts(args.path)
    transformed_ast = transform_ast(original_ast, sys_path)
    transformed_code = ast_to_code(transformed_ast)

    if args.output:
        with open(args.output, "w") as f:
            f.write(transformed_code)
    else:
        print(transformed_code)
    if args.execute and args.output is not None:
        os.system(f"bash {args.output}")

if __name__ == "__main__":
    main()
