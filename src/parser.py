from dataclasses import dataclass, field
from typing import List, Optional, Union
from tokenizer import Token, TokenType, tokenize


# Source position attached to AST nodes for downstream error messages.
# compare=False keeps `==` comparisons in tests independent of position.
@dataclass
class Pos:
    line: int
    col: int

    @classmethod
    def from_token(cls, token: Token) -> "Pos":
        return cls(token.line, token.col)


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


Type = Union[IntType, BooleanType, VoidType, ClassType]


# Op sum type — replaces raw string ops so the typechecker can pattern-match
# exhaustively instead of relying on string equality.
@dataclass
class PlusOp:
    pass

@dataclass
class MinusOp:
    pass

@dataclass
class MultiplyOp:
    pass

@dataclass
class DivideOp:
    pass

@dataclass
class LessThanOp:
    pass

@dataclass
class EqualsOp:
    pass


Op = Union[PlusOp, MinusOp, MultiplyOp, DivideOp, LessThanOp, EqualsOp]


_OP_TOKEN_TO_NODE = {
    TokenType.PLUS: PlusOp,
    TokenType.MINUS: MinusOp,
    TokenType.MULTIPLY: MultiplyOp,
    TokenType.DIVIDE: DivideOp,
    TokenType.LESS_THAN: LessThanOp,
    TokenType.DOUBLE_EQUALS: EqualsOp,
}


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
    expression: "Expression"
    pos: Optional[Pos] = field(default=None, compare=False)

@dataclass
class BinOpExp:
    op: Op
    left: "Expression"
    right: "Expression"
    pos: Optional[Pos] = field(default=None, compare=False)

@dataclass
class CallExp:
    obj: "Expression"
    method_name: str
    args: List["Expression"]
    pos: Optional[Pos] = field(default=None, compare=False)

@dataclass
class NewExp:
    class_name: str
    args: List["Expression"]
    pos: Optional[Pos] = field(default=None, compare=False)


Expression = Union[
    IntLiteralExp, StringLiteralExp, VarExp, ThisExp,
    TrueExp, FalseExp, PrintlnExp, BinOpExp, CallExp, NewExp,
]


# AST node types for statements
@dataclass
class VarDecStmt:
    var_type: Type
    var_name: str
    pos: Optional[Pos] = field(default=None, compare=False)

@dataclass
class AssignStmt:
    var_name: str
    expression: Expression
    pos: Optional[Pos] = field(default=None, compare=False)

@dataclass
class WhileStmt:
    condition: Expression
    body: List["Statement"]
    pos: Optional[Pos] = field(default=None, compare=False)

@dataclass
class BreakStmt:
    pos: Optional[Pos] = field(default=None, compare=False)

@dataclass
class IfStmt:
    condition: Expression
    then_stmt: "Statement"
    else_stmt: Optional["Statement"]
    pos: Optional[Pos] = field(default=None, compare=False)

@dataclass
class ReturnStmt:
    expression: Optional[Expression]
    pos: Optional[Pos] = field(default=None, compare=False)

@dataclass
class ExpStmt:
    expression: Expression
    pos: Optional[Pos] = field(default=None, compare=False)


Statement = Union[
    VarDecStmt, AssignStmt, WhileStmt, BreakStmt,
    IfStmt, ReturnStmt, ExpStmt,
]


# AST node types for top-level definitions
@dataclass
class MethodDef:
    name: str
    params: List[VarDecStmt]
    return_type: Type
    body: List[Statement]
    pos: Optional[Pos] = field(default=None, compare=False)

@dataclass
class Constructor:
    params: List[VarDecStmt]
    # None means no super call was written; [] means `(super)` with no args.
    # The typechecker uses this distinction to enforce that subclasses must
    # explicitly call super.
    super_args: Optional[List[Expression]]
    body: List[Statement]
    pos: Optional[Pos] = field(default=None, compare=False)

@dataclass
class ClassDef:
    name: str
    parent: Optional[str]
    fields: List[VarDecStmt]
    constructor: Constructor
    methods: List[MethodDef]
    pos: Optional[Pos] = field(default=None, compare=False)

@dataclass
class Program:
    classes: List[ClassDef]
    statements: List[Statement]


class ParseError(Exception):
    def __init__(self, message: str, token: Optional[Token] = None):
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

    def parse_type(self) -> Type:
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

    def parse_expression(self) -> Expression:
        token = self.peek()
        if token is None:
            raise ParseError("Expected expression but reached end of input")
        pos = Pos.from_token(token)

        if token.token_type == TokenType.INTEGER_LITERAL:
            self.advance()
            return IntLiteralExp(int(token.value), pos=pos)
        elif token.token_type == TokenType.STRING_LITERAL:
            self.advance()
            return StringLiteralExp(token.value, pos=pos)
        elif token.token_type == TokenType.IDENTIFIER:
            self.advance()
            return VarExp(token.value, pos=pos)
        elif token.token_type == TokenType.THIS:
            self.advance()
            return ThisExp(pos=pos)
        elif token.token_type == TokenType.TRUE:
            self.advance()
            return TrueExp(pos=pos)
        elif token.token_type == TokenType.FALSE:
            self.advance()
            return FalseExp(pos=pos)
        elif token.token_type == TokenType.LEFT_PAREN:
            return self._parse_paren_expression(pos)
        else:
            raise ParseError(
                f"Expected expression but got {token.token_type.name}", token
            )

    def _parse_paren_expression(self, pos: Pos) -> Expression:
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
            return PrintlnExp(exp, pos=pos)

        elif token.token_type == TokenType.CALL:
            self.advance()
            obj = self.parse_expression()
            method_name = self.expect(TokenType.IDENTIFIER).value
            args: List[Expression] = []
            while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
                args.append(self.parse_expression())
            self.expect(TokenType.RIGHT_PAREN)
            return CallExp(obj, method_name, args, pos=pos)

        elif token.token_type == TokenType.NEW:
            self.advance()
            class_name = self.expect(TokenType.IDENTIFIER).value
            args = []
            while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
                args.append(self.parse_expression())
            self.expect(TokenType.RIGHT_PAREN)
            return NewExp(class_name, args, pos=pos)

        elif token.token_type in _OP_TOKEN_TO_NODE:
            op_node = _OP_TOKEN_TO_NODE[self.advance().token_type]()
            left = self.parse_expression()
            right = self.parse_expression()
            self.expect(TokenType.RIGHT_PAREN)
            return BinOpExp(op_node, left, right, pos=pos)

        else:
            raise ParseError(
                f"Expected println, call, new, or operator after '(' "
                f"but got {token.token_type.name}",
                token,
            )

 # Vardec parsing

    def parse_vardec(self) -> VarDecStmt:
        open_paren = self.expect(TokenType.LEFT_PAREN)
        pos = Pos.from_token(open_paren)
        self.expect(TokenType.VARDEC)
        var_type = self.parse_type()
        var_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.RIGHT_PAREN)
        return VarDecStmt(var_type, var_name, pos=pos)

 # Statement parsing

    def parse_statement(self) -> Statement:
        token = self.peek()
        if token is None:
            raise ParseError("Expected statement but reached end of input")
        pos = Pos.from_token(token)

        if token.token_type == TokenType.BREAK:
            self.advance()
            return BreakStmt(pos=pos)

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
                return self._parse_assignment(pos)
            elif next_token.token_type == TokenType.WHILE:
                return self._parse_while(pos)
            elif next_token.token_type == TokenType.IF:
                return self._parse_if(pos)
            elif next_token.token_type == TokenType.RETURN:
                return self._parse_return(pos)
            else:
                exp = self.parse_expression()
                return ExpStmt(exp, pos=pos)
        else:
            raise ParseError(
                f"Expected statement but got {token.token_type.name}", token
            )

    def _parse_assignment(self, pos: Pos) -> AssignStmt:
        self.expect(TokenType.LEFT_PAREN)
        self.expect(TokenType.ASSIGN)
        var_name = self.expect(TokenType.IDENTIFIER).value
        exp = self.parse_expression()
        self.expect(TokenType.RIGHT_PAREN)
        return AssignStmt(var_name, exp, pos=pos)

    def _parse_while(self, pos: Pos) -> WhileStmt:
        self.expect(TokenType.LEFT_PAREN)
        self.expect(TokenType.WHILE)
        condition = self.parse_expression()
        body: List[Statement] = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            body.append(self.parse_statement())
        self.expect(TokenType.RIGHT_PAREN)
        return WhileStmt(condition, body, pos=pos)

    def _parse_if(self, pos: Pos) -> IfStmt:
        self.expect(TokenType.LEFT_PAREN)
        self.expect(TokenType.IF)
        condition = self.parse_expression()
        then_stmt = self.parse_statement()
        else_stmt: Optional[Statement] = None
        if self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            else_stmt = self.parse_statement()
        self.expect(TokenType.RIGHT_PAREN)
        return IfStmt(condition, then_stmt, else_stmt, pos=pos)

    def _parse_return(self, pos: Pos) -> ReturnStmt:
        self.expect(TokenType.LEFT_PAREN)
        self.expect(TokenType.RETURN)
        exp: Optional[Expression] = None
        if self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            exp = self.parse_expression()
        self.expect(TokenType.RIGHT_PAREN)
        return ReturnStmt(exp, pos=pos)

    def parse_method(self) -> MethodDef:
        open_paren = self.expect(TokenType.LEFT_PAREN)
        pos = Pos.from_token(open_paren)
        self.expect(TokenType.METHOD)
        method_name = self.expect(TokenType.IDENTIFIER).value
        # Parameter list: ( vardec* )
        self.expect(TokenType.LEFT_PAREN)
        params: List[VarDecStmt] = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            params.append(self.parse_vardec())
        self.expect(TokenType.RIGHT_PAREN)
        # Return type
        return_type = self.parse_type()
        # Body: stmt*
        body: List[Statement] = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            body.append(self.parse_statement())
        self.expect(TokenType.RIGHT_PAREN)
        return MethodDef(method_name, params, return_type, body, pos=pos)

    def parse_constructor(self) -> Constructor:
        open_paren = self.expect(TokenType.LEFT_PAREN)
        pos = Pos.from_token(open_paren)
        self.expect(TokenType.INIT)
        # Parameter list: ( vardec* )
        self.expect(TokenType.LEFT_PAREN)
        params: List[VarDecStmt] = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            params.append(self.parse_vardec())
        self.expect(TokenType.RIGHT_PAREN)
        # Optional super call: ( super exp* )
        super_args: Optional[List[Expression]] = None
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
        # Body: stmt*
        body: List[Statement] = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            body.append(self.parse_statement())
        self.expect(TokenType.RIGHT_PAREN)
        return Constructor(params, super_args, body, pos=pos)

    def parse_class(self) -> ClassDef:
        open_paren = self.expect(TokenType.LEFT_PAREN)
        pos = Pos.from_token(open_paren)
        self.expect(TokenType.CLASS)
        class_name = self.expect(TokenType.IDENTIFIER).value
        # Optional parent class
        parent: Optional[str] = None
        if self.peek() and self.peek().token_type == TokenType.IDENTIFIER:
            parent = self.advance().value
        # Field list: ( vardec* )
        self.expect(TokenType.LEFT_PAREN)
        fields: List[VarDecStmt] = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            fields.append(self.parse_vardec())
        self.expect(TokenType.RIGHT_PAREN)
        # Constructor
        constructor = self.parse_constructor()
        # Methods: methoddef*
        methods: List[MethodDef] = []
        while self.peek() and self.peek().token_type != TokenType.RIGHT_PAREN:
            methods.append(self.parse_method())
        self.expect(TokenType.RIGHT_PAREN)
        return ClassDef(class_name, parent, fields, constructor, methods, pos=pos)

    def parse_program(self) -> Program:
        classes: List[ClassDef] = []
        while (
            self.peek()
            and self.peek().token_type == TokenType.LEFT_PAREN
            and self.pos + 1 < len(self.tokens)
            and self.tokens[self.pos + 1].token_type == TokenType.CLASS
        ):
            classes.append(self.parse_class())
        statements: List[Statement] = []
        while not self.at_end():
            statements.append(self.parse_statement())
        if not statements:
            raise ParseError("Program must have at least one statement")
        return Program(classes, statements)


def parse(source: str) -> Program:
    tokens = tokenize(source)
    return Parser(tokens).parse_program()
