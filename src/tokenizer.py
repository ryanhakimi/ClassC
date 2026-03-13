from enum import Enum, auto
from dataclasses import dataclass
from typing import List


class TokenType(Enum):
    # Symbols
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()

    # Operators
    PLUS = auto()          # +
    MINUS = auto()         # -
    MULTIPLY = auto()      # *
    DIVIDE = auto()        # /
    LESS_THAN = auto()     # <
    DOUBLE_EQUALS = auto() # ==
    ASSIGN = auto()        # =

    # Type keywords
    INT_TYPE = auto()      # Int
    BOOLEAN_TYPE = auto()  # Boolean
    VOID_TYPE = auto()     # Void

    # Boolean literals
    TRUE = auto()          # true
    FALSE = auto()         # false

    # Other keywords
    THIS = auto()          # this
    BREAK = auto()         # break
    PRINTLN = auto()       # println
    WHILE = auto()         # while
    IF = auto()            # if
    RETURN = auto()        # return
    VARDEC = auto()        # vardec
    METHOD = auto()        # method
    INIT = auto()          # init
    SUPER = auto()         # super
    CLASS = auto()         # class
    NEW = auto()           # new
    CALL = auto()          # call

    # Literals
    INTEGER_LITERAL = auto()
    STRING_LITERAL = auto()

    # Identifiers (variables, class names, method names)
    IDENTIFIER = auto()


# Maps reserved word strings to their TokenType.
# When we read a word like "while", we check this dict to see if it's
# a keyword. If it's not found here, it's treated as an IDENTIFIER.
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


# Represents a single token produced by the tokenizer.
# Stores the type of token, its raw text value, and where it
# appeared in the source file (line and column) for error reporting.
@dataclass
class Token:
    token_type: TokenType  # What kind of token this is (e.g., LEFT_PAREN, WHILE, IDENTIFIER)
    value: str             # The actual text from the source code (e.g., "(", "while", "myVar")
    line: int              # Line number where this token starts (1-indexed)
    col: int               # Column number where this token starts (1-indexed)

    def __repr__(self):
        return f"Token({self.token_type.name}, {self.value!r}, line={self.line}, col={self.col})"


# Custom exception for tokenizer errors.
# Includes the line and column where the error occurred so the user
# can find the problem in their source code.
class TokenizerError(Exception):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"Tokenizer error at line {line}, col {col}: {message}")
        self.line = line
        self.col = col


class Tokenizer:
    """
    Converts a raw source string into a list of Token objects.
    Walks through the source one character at a time (via pos),
    tracking the current line and column for error reporting.
    """

    def __init__(self, source: str):
        self.source = source       # The full source code string
        self.pos = 0               # Current character index in source
        self.line = 1              # Current line number (starts at 1)
        self.col = 1               # Current column number (starts at 1)
        self.tokens: List[Token] = []  # Accumulated list of tokens

    def peek(self) -> str | None:
        """
        Returns the current character without consuming it.
        Returns None if we've reached the end of the source.
        """
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def advance(self) -> str:
        """
        Consumes and returns the current character.
        Updates line/col tracking — if we hit a newline, we
        move to the next line and reset the column to 1.
        """
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def skip_whitespace(self):
        """
        Advances past any spaces, tabs, newlines, or carriage returns.
        These characters are not meaningful in ClassC — they just
        separate tokens.
        """
        while self.pos < len(self.source) and self.source[self.pos] in " \t\n\r":
            self.advance()

    def read_string(self) -> Token:
        """
        Reads a string literal enclosed in double quotes (e.g., "hello").
        Handles escape sequences like \\n, \\t, \\\\, and \\\".
        Raises TokenizerError if the string is never closed or has
        an invalid escape sequence.
        """
        start_line = self.line
        start_col = self.col
        self.advance()  # skip opening "
        value = []
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch == '"':
                self.advance()  # skip closing "
                return Token(TokenType.STRING_LITERAL, "".join(value), start_line, start_col)
            if ch == "\\":
                # Handle escape sequences: consume the backslash,
                # then check what character follows it
                self.advance()
                if self.pos >= len(self.source):
                    raise TokenizerError("Unexpected end of input in string escape", self.line, self.col)
                escaped = self.advance()
                escape_map = {"n": "\n", "t": "\t", "\\": "\\", '"': '"'}
                if escaped in escape_map:
                    value.append(escape_map[escaped])
                else:
                    raise TokenizerError(f"Unknown escape sequence: \\{escaped}", self.line, self.col)
            else:
                value.append(self.advance())
        raise TokenizerError("Unterminated string literal", start_line, start_col)

    def read_integer(self) -> Token:
        """
        Reads a sequence of digits as an integer literal (e.g., 42, 0, 100).
        Raises an error if the integer is immediately followed by a letter
        or underscore (e.g., '123abc' is not valid).
        """
        start_line = self.line
        start_col = self.col
        digits = []
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            digits.append(self.advance())
        # Make sure the integer isn't immediately followed by a letter (e.g., "123abc")
        if self.pos < len(self.source) and (self.source[self.pos].isalpha() or self.source[self.pos] == "_"):
            raise TokenizerError(
                f"Invalid character '{self.source[self.pos]}' after integer literal",
                self.line, self.col,
            )
        return Token(TokenType.INTEGER_LITERAL, "".join(digits), start_line, start_col)

    def read_identifier_or_keyword(self) -> Token:
        """
        Reads a word made of letters, digits, and underscores.
        After reading the full word, checks the KEYWORDS dict to see
        if it's a reserved word (like 'while' or 'class'). If it is,
        returns that keyword's TokenType. Otherwise, it's an IDENTIFIER
        (a user-defined name like a variable or class name).
        """
        start_line = self.line
        start_col = self.col
        chars = []
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == "_"):
            chars.append(self.advance())
        word = "".join(chars)
        # Look up the word in KEYWORDS — if not found, default to IDENTIFIER
        token_type = KEYWORDS.get(word, TokenType.IDENTIFIER)
        return Token(token_type, word, start_line, start_col)

    def tokenize(self) -> List[Token]:
        """
        Main loop: walks through the entire source string and produces
        a list of tokens. For each iteration, it skips whitespace, then
        looks at the current character to decide what kind of token to read:
          - '(' or ')' -> parentheses
          - '+', '-', '*', '/', '<' -> single-char operators
          - '=' -> could be ASSIGN (=) or DOUBLE_EQUALS (==), so we peek ahead
          - '"' -> start of a string literal
          - digit -> start of an integer literal
          - letter/underscore -> start of an identifier or keyword
          - anything else -> error
        """
        while self.pos < len(self.source):
            self.skip_whitespace()
            if self.pos >= len(self.source):
                break

            ch = self.source[self.pos]
            start_line = self.line
            start_col = self.col

            # Single-character tokens: parentheses and operators
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

            # '=' needs lookahead: could be '=' (assignment) or '==' (equality check)
            elif ch == "=":
                self.advance()
                if self.pos < len(self.source) and self.source[self.pos] == "=":
                    self.advance()  # consume the second '='
                    self.tokens.append(Token(TokenType.DOUBLE_EQUALS, "==", start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, "=", start_line, start_col))

            # Multi-character tokens: strings, integers, identifiers/keywords
            elif ch == '"':
                self.tokens.append(self.read_string())
            elif ch.isdigit():
                self.tokens.append(self.read_integer())
            elif ch.isalpha() or ch == "_":
                self.tokens.append(self.read_identifier_or_keyword())
            else:
                raise TokenizerError(f"Unexpected character: {ch!r}", start_line, start_col)

        return self.tokens


# Convenience function so other modules (like a future parser) can just call:
#   from tokenizer import tokenize
#   tokens = tokenize(source_code)
def tokenize(source: str) -> List[Token]:
    """Takes a source code string and returns a list of Tokens."""
    return Tokenizer(source).tokenize()


# Entry point: run the tokenizer on a file from the command line.
# Usage: python tokenizer.py <source_file>
# Prints each token on its own line.
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
