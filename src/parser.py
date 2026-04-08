from dataclasses import dataclass
from typing import List, Optional
from tokenizer import Token, TokenType, tokenize


# AST node types for representing types in the language
@dataclass
class IntType:
    pass

@dataclass
class BooleanType:
    pass

@dataclass
class VoidType:
    pass

@dataclass
class ClassType:
    name: str

# AST node types for expressions
@dataclass
class IntLiteralExp:
    value: int

@dataclass
class VarExp:
    name: str

@dataclass
class ThisExp:
    pass

@dataclass
class TrueExp:
    pass

@dataclass
class FalseExp:
    pass

@dataclass
class PrintlnExp:
    expression: object

@dataclass
class BinOpExp:
    op: str
    left: object
    right: object

@dataclass
class CallExp:
    obj: object
    method_name: str
    args: list

@dataclass
class NewExp:
    class_name: str
    args: list

# AST node types for statements
@dataclass
class VarDecStmt:
    var_type: object
    var_name: str

@dataclass
class AssignStmt:
    var_name: str
    expression: object

@dataclass
class WhileStmt:
    condition: object
    body: list

@dataclass
class BreakStmt:
    pass

@dataclass
class IfStmt:
    condition: object
    then_stmt: object
    else_stmt: object  # None if no else

@dataclass
class ReturnStmt:
    expression: object  # None for void return

@dataclass
class ExpStmt:
    expression: object

# AST node types for top-level definitions
@dataclass
class MethodDef:
    name: str
    params: list
    return_type: object
    body: list

@dataclass
class Constructor:
    params: list
    super_args: object  # None if no super call, list if present
    body: list

@dataclass
class ClassDef:
    name: str
    parent: object  # None or str
    fields: list
    constructor: object
    methods: list

@dataclass
class Program:
    classes: list
    statements: list


class ParseError(Exception):
    def __init__(self, message: str, token: Token = None):
        if token:
            super().__init__(
                f"Parse error at line {token.line}, col {token.col}: {message}"
            )
        else:
            super().__init__(f"Parse error: {message}")
        self.token = token


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self) -> Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        token = self.peek()
        if token is None:
            raise ParseError(f"Expected {token_type.name} but reached end of input")
        if token.token_type != token_type:
            raise ParseError(
                f"Expected {token_type.name} but got {token.token_type.name}", token
            )
        return self.advance()

    def at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def parse_type(self):
        token = self.peek()
        if token is None:
            raise ParseError("Expected type but reached end of input")
        if token.token_type == TokenType.INT_TYPE:
            self.advance()
            return IntType()
        elif token.token_type == TokenType.BOOLEAN_TYPE:
            self.advance()
            return BooleanType()
        elif token.token_type == TokenType.VOID_TYPE:
            self.advance()
            return VoidType()
        elif token.token_type == TokenType.IDENTIFIER:
            self.advance()
            return ClassType(token.value)
        else:
            raise ParseError(
                f"Expected type but got {token.token_type.name}", token
            )

    def parse_expression(self):
        token = self.peek()
        if token is None:
            raise ParseError("Expected expression but reached end of input")

        if token.token_type == TokenType.INTEGER_LITERAL:
            self.advance()
            return IntLiteralExp(int(token.value))
        elif token.token_type == TokenType.IDENTIFIER:
            self.advance()
            return VarExp(token.value)
        elif token.token_type == TokenType.THIS:
            self.advance()
            return ThisExp()
        elif token.token_type == TokenType.TRUE:
            self.advance()
            return TrueExp()
        elif token.token_type == TokenType.FALSE:
            self.advance()
            return FalseExp()
        elif token.token_type == TokenType.LEFT_PAREN:
            return self._parse_paren_expression()
        else:
            raise ParseError(
                f"Expected expression but got {token.token_type.name}", token
            )

    def _parse_paren_expression(self):
        self.expect(TokenType.LEFT_PAREN)
        token = self.peek()
        if token is None:
            raise ParseError(
                "Expected expression content after '(' but reached end of input"
            )

        if token.token_type == TokenType.PRINTLN:
            self.advance()
            exp = self.parse_expression()
            self.expect(TokenType.RIGHT_PAREN)
            return PrintlnExp(exp)

        elif token.token_type == TokenType.CALL:
            self.advance()
            obj = self.parse_expression()
            method_name = self.expect(TokenType.IDENTIFIER).value
            args = []
            while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
                args.append(self.parse_expression())
            self.expect(TokenType.RIGHT_PAREN)
            return CallExp(obj, method_name, args)

        elif token.token_type == TokenType.NEW:
            self.advance()
            class_name = self.expect(TokenType.IDENTIFIER).value
            args = []
            while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
                args.append(self.parse_expression())
            self.expect(TokenType.RIGHT_PAREN)
            return NewExp(class_name, args)

        elif token.token_type in (
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.MULTIPLY,
            TokenType.DIVIDE,
            TokenType.LESS_THAN,
            TokenType.DOUBLE_EQUALS,
        ):
            op = self.advance().value
            left = self.parse_expression()
            right = self.parse_expression()
            self.expect(TokenType.RIGHT_PAREN)
            return BinOpExp(op, left, right)

        else:
            raise ParseError(
                f"Expected println, call, new, or operator after '(' "
                f"but got {token.token_type.name}",
                token,
            )
