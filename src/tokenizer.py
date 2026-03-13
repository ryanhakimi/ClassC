from enum import Enum, auto
from dataclasses import dataclass
from typing import List

class TokenType(Enum):
    # Symbols
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    LESS_THAN = auto()
    DOUBLE_EQUALS = auto()
    ASSIGN = auto()

    # Type keywords
    INT_TYPE = auto()
    BOOLEAN_TYPE = auto()
    VOID_TYPE = auto()

    # Boolean literals
    TRUE = auto()
    FALSE = auto()

    # Other keywords
    THIS = auto()
    BREAK = auto()
    PRINTLN = auto()
    WHILE = auto()
    IF = auto()
    RETURN = auto()
    VARDEC = auto()
    METHOD = auto()
    INIT = auto()
    SUPER = auto()
    CLASS = auto()
    NEW = auto()
    CALL = auto()

    # Literals
    INTEGER_LITERAL = auto()

    # Identifiers (variables, class names, method names)
    IDENTIFIER = auto()

KEYWORDS = {
    "Int": TokenType.INT_TYPE,
    "Boolean": TokenType.BOOLEAN_TYPE,
    "Void": TokenType.VOID_TYPE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "this": TokenType.THIS,
    "break": TokenType.BREAK,
    "println": TokenType.PRINTLN,
    "while": TokenType.WHILE,
    "if": TokenType.IF,
    "return": TokenType.RETURN,
    "vardec": TokenType.VARDEC,
    "method": TokenType.METHOD,
    "init": TokenType.INIT,
    "super": TokenType.SUPER,
    "class": TokenType.CLASS,
    "new": TokenType.NEW,
    "call": TokenType.CALL,
}

@dataclass
class Token:
    token_type: TokenType
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.token_type.name}, {self.value!r}, line={self.line}, col={self.col})"

class TokenizerError(Exception):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"Tokenizer error at line {line}, col {col}: {message}")
        self.line = line
        self.col = col

class Tokenizer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def peek(self) -> str | None:
        return self.source[self.pos] if self.pos < len(self.source) else None

    def match(self, expected: str) -> bool:
        if self.peek() == expected:
            self.advance()
            return True
        return False

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in " \t\n\r":
            self.advance()

    def read_integer(self) -> Token:
        start_line = self.line
        start_col = self.col
        digits = []
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            digits.append(self.advance())
        if self.pos < len(self.source) and (self.source[self.pos].isalpha() or self.source[self.pos] == "_"):
            raise TokenizerError(
                f"Invalid character '{self.source[self.pos]}' after integer literal",
                self.line, self.col,
            )
        return Token(TokenType.INTEGER_LITERAL, "".join(digits), start_line, start_col)

    def read_identifier_or_keyword(self) -> Token:
        start_line = self.line
        start_col = self.col
        chars = []
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == "_"):
            chars.append(self.advance())
        word = "".join(chars)
        token_type = KEYWORDS.get(word, TokenType.IDENTIFIER)
        return Token(token_type, word, start_line, start_col)

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self.skip_whitespace()
            if self.pos >= len(self.source):
                break

            ch = self.source[self.pos]
            start_line = self.line
            start_col = self.col

            if ch == "(":
                self.advance()
                self.tokens.append(Token(TokenType.LEFT_PAREN, "(", start_line, start_col))
            elif ch == ")":
                self.advance()
                self.tokens.append(Token(TokenType.RIGHT_PAREN, ")", start_line, start_col))
            elif ch == "+":
                self.advance()
                self.tokens.append(Token(TokenType.PLUS, "+", start_line, start_col))
            elif ch == "-":
                self.advance()
                self.tokens.append(Token(TokenType.MINUS, "-", start_line, start_col))
            elif ch == "*":
                self.advance()
                self.tokens.append(Token(TokenType.MULTIPLY, "*", start_line, start_col))
            elif ch == "/":
                self.advance()
                self.tokens.append(Token(TokenType.DIVIDE, "/", start_line, start_col))
            elif ch == "<":
                self.advance()
                self.tokens.append(Token(TokenType.LESS_THAN, "<", start_line, start_col))
            elif ch == "=":
                self.advance()
                if self.match("="):
                    self.tokens.append(Token(TokenType.DOUBLE_EQUALS, "==", start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, "=", start_line, start_col))
            elif ch.isdigit():
                self.tokens.append(self.read_integer())
            elif ch.isalpha() or ch == "_":
                self.tokens.append(self.read_identifier_or_keyword())
            else:
                raise TokenizerError(f"Unexpected character: {ch!r}", start_line, start_col)

        return self.tokens

def tokenize(source: str) -> List[Token]:
    return Tokenizer(source).tokenize()

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python tokenizer.py <source_file>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        source = f.read()

    tokens = tokenize(source)
    for token in tokens:
        print(token)
