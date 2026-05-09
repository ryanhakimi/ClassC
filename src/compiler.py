import sys

from codegen import generate_c
from parser import parse, ParseError
from tokenizer import tokenize, TokenizerError
from typechecker import typecheck, TypecheckError
from codegen import CodegenError


USAGE = "Usage: python compiler.py <command> <source_file> [output_file]"


def main():
    if len(sys.argv) < 3:
        print(USAGE)
        sys.exit(1)

    command = sys.argv[1]
    source_file = sys.argv[2]

    try:
        with open(source_file, "r") as file:
            source = file.read()
    except FileNotFoundError:
        print(f"Error: File not found: {source_file}")
        sys.exit(1)

    try:
        if command == "tokens":
            for token in tokenize(source):
                print(token)
            return

        if command == "parse":
            print(parse(source))
            return

        if command == "typecheck":
            typed_program = typecheck(source)
            print("Typecheck succeeded")
            print(f"Classes: {', '.join(sorted(typed_program.classes.keys()))}")
            return

        if command == "compile":
            output = generate_c(source)
            if len(sys.argv) >= 4:
                with open(sys.argv[3], "w") as file:
                    file.write(output)
            else:
                print(output)
            return

        print(f"Unknown command: {command}")
        print(USAGE)
        sys.exit(1)

    except (TokenizerError, ParseError, TypecheckError, CodegenError) as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
