from dataclasses import dataclass, field
from typing import List, Optional
from tokenizer import Token, TokenType, tokenize


@dataclass(frozen=True)
class Pos:
    line: int
    col: int


# AST node types for representing types in the language
@dataclass
class IntType:
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class BooleanType:
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class VoidType:
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class ClassType:
    name: str
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass(frozen=True)
class PlusOp:
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass(frozen=True)
class MinusOp:
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass(frozen=True)
class MultiplyOp:
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass(frozen=True)
class DivideOp:
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass(frozen=True)
class LessThanOp:
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass(frozen=True)
class DoubleEqualsOp:
    pos: Optional[Pos] = field(default=None, compare=False)


# AST node types for expressions
@dataclass
class IntLiteralExp:
    value: int
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class StringLiteralExp:
    value: str
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class VarExp:
    name: str
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class ThisExp:
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class TrueExp:
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class FalseExp:
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class PrintlnExp:
    expression: object
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class BinOpExp:
    op: object
    left: object
    right: object
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class CallExp:
    obj: object
    method_name: str
    args: list
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class NewExp:
    class_name: str
    args: list
    pos: Optional[Pos] = field(default=None, compare=False)


# AST node types for statements
@dataclass
class VarDecStmt:
    var_type: object
    var_name: str
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class AssignStmt:
    var_name: str
    expression: object
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class WhileStmt:
    condition: object
    body: list
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class BreakStmt:
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class IfStmt:
    condition: object
    then_stmt: object
    else_stmt: object
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class ReturnStmt:
    expression: object
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class ExpStmt:
    expression: object
    pos: Optional[Pos] = field(default=None, compare=False)


# AST node types for top-level definitions
@dataclass
class MethodDef:
    name: str
    params: list
    return_type: object
    body: list
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class Constructor:
    params: list
    super_args: object
    body: list
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class ClassDef:
    name: str
    parent: object
    fields: list
    constructor: object
    methods: list
    pos: Optional[Pos] = field(default=None, compare=False)


@dataclass
class Program:
    classes: list
    statements: list
    pos: Optional[Pos] = field(default=None, compare=False)


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

    def _pos_from_token(self, token: Token) -> Pos:
        return Pos(token.line, token.col)

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

        pos = self._pos_from_token(token)
        if token.token_type == TokenType.INT_TYPE:
            self.advance()
            return IntType(pos)
        elif token.token_type == TokenType.BOOLEAN_TYPE:
            self.advance()
            return BooleanType(pos)
        elif token.token_type == TokenType.VOID_TYPE:
            self.advance()
            return VoidType(pos)
        elif token.token_type == TokenType.IDENTIFIER:
            self.advance()
            return ClassType(token.value, pos)
        else:
            raise ParseError(
                f"Expected type but got {token.token_type.name}", token
            )

    def parse_expression(self):
        token = self.peek()
        if token is None:
            raise ParseError("Expected expression but reached end of input")

        pos = self._pos_from_token(token)
        if token.token_type == TokenType.INTEGER_LITERAL:
            self.advance()
            return IntLiteralExp(int(token.value), pos)
        elif token.token_type == TokenType.STRING_LITERAL:
            self.advance()
            return StringLiteralExp(token.value, pos)
        elif token.token_type == TokenType.IDENTIFIER:
            self.advance()
            return VarExp(token.value, pos)
        elif token.token_type == TokenType.THIS:
            self.advance()
            return ThisExp(pos)
        elif token.token_type == TokenType.TRUE:
            self.advance()
            return TrueExp(pos)
        elif token.token_type == TokenType.FALSE:
            self.advance()
            return FalseExp(pos)
        elif token.token_type == TokenType.LEFT_PAREN:
            return self._parse_paren_expression()
        else:
            raise ParseError(
                f"Expected expression but got {token.token_type.name}", token
            )

    def _parse_paren_expression(self):
        start_token = self.expect(TokenType.LEFT_PAREN)
        start_pos = self._pos_from_token(start_token)
        token = self.peek()
        if token is None:
            raise ParseError(
                "Expected expression content after '(' but reached end of input"
            )

        if token.token_type == TokenType.PRINTLN:
            self.advance()
            exp = self.parse_expression()
            self.expect(TokenType.RIGHT_PAREN)
            return PrintlnExp(exp, start_pos)
        elif token.token_type == TokenType.CALL:
            self.advance()
            obj = self.parse_expression()
            method_name = self.expect(TokenType.IDENTIFIER).value
            args = []
            while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
                args.append(self.parse_expression())
            self.expect(TokenType.RIGHT_PAREN)
            return CallExp(obj, method_name, args, start_pos)
        elif token.token_type == TokenType.NEW:
            self.advance()
            class_name = self.expect(TokenType.IDENTIFIER).value
            args = []
            while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
                args.append(self.parse_expression())
            self.expect(TokenType.RIGHT_PAREN)
            return NewExp(class_name, args, start_pos)
        elif token.token_type in (
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.MULTIPLY,
            TokenType.DIVIDE,
            TokenType.LESS_THAN,
            TokenType.DOUBLE_EQUALS,
        ):
            operator_token = self.advance()
            operator_pos = self._pos_from_token(operator_token)
            operators = {
                TokenType.PLUS: PlusOp(operator_pos),
                TokenType.MINUS: MinusOp(operator_pos),
                TokenType.MULTIPLY: MultiplyOp(operator_pos),
                TokenType.DIVIDE: DivideOp(operator_pos),
                TokenType.LESS_THAN: LessThanOp(operator_pos),
                TokenType.DOUBLE_EQUALS: DoubleEqualsOp(operator_pos),
            }
            left = self.parse_expression()
            right = self.parse_expression()
            self.expect(TokenType.RIGHT_PAREN)
            return BinOpExp(operators[operator_token.token_type], left, right, start_pos)
        else:
            raise ParseError(
                f"Expected println, call, new, or operator after '(' "
                f"but got {token.token_type.name}",
                token,
            )

    def parse_vardec(self) -> VarDecStmt:
        start_token = self.expect(TokenType.LEFT_PAREN)
        start_pos = self._pos_from_token(start_token)
        self.expect(TokenType.VARDEC)
        var_type = self.parse_type()
        var_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.RIGHT_PAREN)
        return VarDecStmt(var_type, var_name, start_pos)

    def parse_statement(self):
        token = self.peek()
        if token is None:
            raise ParseError("Expected statement but reached end of input")

        if token.token_type == TokenType.BREAK:
            self.advance()
            return BreakStmt(self._pos_from_token(token))
        elif token.token_type == TokenType.LEFT_PAREN:
            if self.pos + 1 >= len(self.tokens):
                raise ParseError(
                    "Expected statement content after '(' but reached end of input",
                    token,
                )
            next_token = self.tokens[self.pos + 1]

            if next_token.token_type == TokenType.VARDEC:
                return self.parse_vardec()
            elif next_token.token_type == TokenType.ASSIGN:
                return self._parse_assignment()
            elif next_token.token_type == TokenType.WHILE:
                return self._parse_while()
            elif next_token.token_type == TokenType.IF:
                return self._parse_if()
            elif next_token.token_type == TokenType.RETURN:
                return self._parse_return()
            else:
                exp = self.parse_expression()
                return ExpStmt(exp, exp.pos)
        else:
            raise ParseError(
                f"Expected statement but got {token.token_type.name}", token
            )

    def _parse_assignment(self) -> AssignStmt:
        start_token = self.expect(TokenType.LEFT_PAREN)
        start_pos = self._pos_from_token(start_token)
        self.expect(TokenType.ASSIGN)
        var_name = self.expect(TokenType.IDENTIFIER).value
        exp = self.parse_expression()
        self.expect(TokenType.RIGHT_PAREN)
        return AssignStmt(var_name, exp, start_pos)

    def _parse_while(self) -> WhileStmt:
        start_token = self.expect(TokenType.LEFT_PAREN)
        start_pos = self._pos_from_token(start_token)
        self.expect(TokenType.WHILE)
        condition = self.parse_expression()
        body = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            body.append(self.parse_statement())
        self.expect(TokenType.RIGHT_PAREN)
        return WhileStmt(condition, body, start_pos)

    def _parse_if(self) -> IfStmt:
        start_token = self.expect(TokenType.LEFT_PAREN)
        start_pos = self._pos_from_token(start_token)
        self.expect(TokenType.IF)
        condition = self.parse_expression()
        then_stmt = self.parse_statement()
        else_stmt = None
        if self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            else_stmt = self.parse_statement()
        self.expect(TokenType.RIGHT_PAREN)
        return IfStmt(condition, then_stmt, else_stmt, start_pos)

    def _parse_return(self) -> ReturnStmt:
        start_token = self.expect(TokenType.LEFT_PAREN)
        start_pos = self._pos_from_token(start_token)
        self.expect(TokenType.RETURN)
        exp = None
        if self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            exp = self.parse_expression()
        self.expect(TokenType.RIGHT_PAREN)
        return ReturnStmt(exp, start_pos)

    def parse_method(self) -> MethodDef:
        start_token = self.expect(TokenType.LEFT_PAREN)
        start_pos = self._pos_from_token(start_token)
        self.expect(TokenType.METHOD)
        method_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LEFT_PAREN)
        params = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            params.append(self.parse_vardec())
        self.expect(TokenType.RIGHT_PAREN)
        return_type = self.parse_type()
        body = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            body.append(self.parse_statement())
        self.expect(TokenType.RIGHT_PAREN)
        return MethodDef(method_name, params, return_type, body, start_pos)

    def parse_constructor(self) -> Constructor:
        start_token = self.expect(TokenType.LEFT_PAREN)
        start_pos = self._pos_from_token(start_token)
        self.expect(TokenType.INIT)
        self.expect(TokenType.LEFT_PAREN)
        params = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            params.append(self.parse_vardec())
        self.expect(TokenType.RIGHT_PAREN)
        super_args = None
        if (
            self.peek()
            and self.peek().token_type == TokenType.LEFT_PAREN
            and self.pos + 1 < len(self.tokens)
            and self.tokens[self.pos + 1].token_type == TokenType.SUPER
        ):
            self.expect(TokenType.LEFT_PAREN)
            self.expect(TokenType.SUPER)
            super_args = []
            while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
                super_args.append(self.parse_expression())
            self.expect(TokenType.RIGHT_PAREN)
        body = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            body.append(self.parse_statement())
        self.expect(TokenType.RIGHT_PAREN)
        return Constructor(params, super_args, body, start_pos)

    def parse_class(self) -> ClassDef:
        start_token = self.expect(TokenType.LEFT_PAREN)
        start_pos = self._pos_from_token(start_token)
        self.expect(TokenType.CLASS)
        class_name = self.expect(TokenType.IDENTIFIER).value
        parent = None
        if self.peek() and self.peek().token_type == TokenType.IDENTIFIER:
            parent = self.advance().value
        self.expect(TokenType.LEFT_PAREN)
        fields = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            fields.append(self.parse_vardec())
        self.expect(TokenType.RIGHT_PAREN)
        constructor = self.parse_constructor()
        methods = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            methods.append(self.parse_method())
        self.expect(TokenType.RIGHT_PAREN)
        return ClassDef(class_name, parent, fields, constructor, methods, start_pos)

    def parse_program(self) -> Program:
        start_token = self.peek()
        classes = []
        while (
            self.peek()
            and self.peek().token_type == TokenType.LEFT_PAREN
            and self.pos + 1 < len(self.tokens)
            and self.tokens[self.pos + 1].token_type == TokenType.CLASS
        ):
            classes.append(self.parse_class())
        statements = []
        while not self.at_end():
            statements.append(self.parse_statement())
        if not statements:
            raise ParseError("Program must have at least one statement")
        program_pos = self._pos_from_token(start_token) if start_token else None
        return Program(classes, statements, program_pos)


def parse(source: str) -> Program:
    tokens = tokenize(source)
    return Parser(tokens).parse_program()
