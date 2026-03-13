import sys
import os
import pytest

# Add src directory to path so we can import tokenizer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tokenizer import Token, Tokenizer, TokenizerError, TokenType, tokenize, KEYWORDS


# ── Single-character tokens ──────────────────────────────────────
# Tests that each one-character symbol produces the correct token type and value.

def test_single_character_tokens():
    # Feed all single-char symbols in one string and check the result
    tokens = tokenize("()+-*/<")
    types = [t.token_type for t in tokens]
    values = [t.value for t in tokens]

    assert types == [
        TokenType.LEFT_PAREN,
        TokenType.RIGHT_PAREN,
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.MULTIPLY,
        TokenType.DIVIDE,
        TokenType.LESS_THAN,
    ]
    assert values == ["(", ")", "+", "-", "*", "/", "<"]


# ── Assignment and equality ──────────────────────────────────────
# The tokenizer must tell apart "=" (assign) from "==" (equality).

def test_assign_and_double_equals():
    # "= ==" should give one ASSIGN then one DOUBLE_EQUALS
    tokens = tokenize("= ==")

    assert tokens[0].token_type == TokenType.ASSIGN
    assert tokens[0].value == "="
    assert tokens[1].token_type == TokenType.DOUBLE_EQUALS
    assert tokens[1].value == "=="


# ── Keywords ─────────────────────────────────────────────────────
# Reserved words like "while", "class", "Int" must map to their specific token types.

def test_keywords():
    # Put every keyword in one source string, separated by spaces
    source = (
        "Int Boolean Void true false this break println while if "
        "return vardec method init super class new call"
    )
    tokens = tokenize(source)
    expected = [
        TokenType.INT_TYPE,
        TokenType.BOOLEAN_TYPE,
        TokenType.VOID_TYPE,
        TokenType.TRUE,
        TokenType.FALSE,
        TokenType.THIS,
        TokenType.BREAK,
        TokenType.PRINTLN,
        TokenType.WHILE,
        TokenType.IF,
        TokenType.RETURN,
        TokenType.VARDEC,
        TokenType.METHOD,
        TokenType.INIT,
        TokenType.SUPER,
        TokenType.CLASS,
        TokenType.NEW,
        TokenType.CALL,
    ]
    assert [t.token_type for t in tokens] == expected


def test_every_keyword_in_dict():
    # Loop through the KEYWORDS dictionary and verify each one individually
    for word, expected_type in KEYWORDS.items():
        tokens = tokenize(word)
        assert len(tokens) == 1
        assert tokens[0].token_type == expected_type
        assert tokens[0].value == word


# ── Identifiers ──────────────────────────────────────────────────
# Words that are NOT keywords should become IDENTIFIER tokens.

def test_identifier_simple():
    # A plain variable name
    tokens = tokenize("myVar")
    assert len(tokens) == 1
    assert tokens[0].token_type == TokenType.IDENTIFIER
    assert tokens[0].value == "myVar"


def test_identifier_with_underscore():
    # Underscores are allowed at the start and in the middle of identifiers
    tokens = tokenize("_foo my_var _123")
    assert len(tokens) == 3
    assert all(t.token_type == TokenType.IDENTIFIER for t in tokens)
    assert tokens[0].value == "_foo"
    assert tokens[1].value == "my_var"
    assert tokens[2].value == "_123"


def test_identifier_with_digits():
    # Digits are allowed inside identifiers (just not at the start)
    tokens = tokenize("var1 x2y")
    assert len(tokens) == 2
    assert tokens[0].token_type == TokenType.IDENTIFIER
    assert tokens[1].token_type == TokenType.IDENTIFIER


# ── Integer literals ─────────────────────────────────────────────
# Sequences of digits become INTEGER_LITERAL tokens.

def test_integer_literal():
    # A basic number
    tokens = tokenize("42")
    assert len(tokens) == 1
    assert tokens[0].token_type == TokenType.INTEGER_LITERAL
    assert tokens[0].value == "42"


def test_integer_zero():
    # Zero is a valid integer literal
    tokens = tokenize("0")
    assert tokens[0].token_type == TokenType.INTEGER_LITERAL
    assert tokens[0].value == "0"


def test_integer_multiple():
    # Multiple integers separated by spaces
    tokens = tokenize("1 23 456")
    assert len(tokens) == 3
    assert tokens[0].value == "1"
    assert tokens[1].value == "23"
    assert tokens[2].value == "456"


def test_integer_followed_by_letter_raises():
    # "123abc" is not valid — digits glued to letters should error
    with pytest.raises(TokenizerError):
        tokenize("123abc")


def test_integer_followed_by_underscore_raises():
    # "99_x" is not valid — digits glued to underscores should error
    with pytest.raises(TokenizerError):
        tokenize("99_x")


# ── String literals ──────────────────────────────────────────────
# Strings are enclosed in double quotes. The tokenizer must handle
# escape sequences and report errors for malformed strings.

def test_string_literal_simple():
    # A normal string with no special characters
    tokens = tokenize('"hello"')
    assert len(tokens) == 1
    assert tokens[0].token_type == TokenType.STRING_LITERAL
    assert tokens[0].value == "hello"


def test_string_literal_empty():
    # An empty string "" is valid
    tokens = tokenize('""')
    assert tokens[0].token_type == TokenType.STRING_LITERAL
    assert tokens[0].value == ""


def test_string_with_spaces():
    # Spaces inside a string should be preserved (not treated as token separators)
    tokens = tokenize('"hello world"')
    assert tokens[0].value == "hello world"


def test_string_escape_newline():
    # \n inside a string should become an actual newline character
    tokens = tokenize('"line1\\nline2"')
    assert tokens[0].value == "line1\nline2"


def test_string_escape_tab():
    # \t inside a string should become an actual tab character
    tokens = tokenize('"col1\\tcol2"')
    assert tokens[0].value == "col1\tcol2"


def test_string_escape_backslash():
    # \\\\ in source becomes a single backslash in the token value
    tokens = tokenize('"path\\\\dir"')
    assert tokens[0].value == "path\\dir"


def test_string_escape_quote():
    # \" inside a string should become a literal quote character
    tokens = tokenize('"say \\"hi\\""')
    assert tokens[0].value == 'say "hi"'


def test_string_unknown_escape_raises():
    # \x is not a valid escape sequence — should raise an error
    with pytest.raises(TokenizerError):
        tokenize('"bad\\x"')


def test_string_unterminated_raises():
    # A string that never gets a closing quote should raise an error
    with pytest.raises(TokenizerError):
        tokenize('"no closing')


def test_string_escape_at_end_of_input_raises():
    # A backslash at the very end of input (nothing to escape) should error
    with pytest.raises(TokenizerError):
        tokenize('"trailing\\')


# ── Comments ─────────────────────────────────────────────────────
# "//" starts a line comment — everything after it until the newline is ignored.

def test_line_comment_skipped():
    # The comment between 42 and 7 should be ignored entirely
    tokens = tokenize("42 // this is a comment\n7")
    assert len(tokens) == 2
    assert tokens[0].value == "42"
    assert tokens[1].value == "7"


def test_line_comment_at_end_of_input():
    # A comment at the end of the file (no newline after) should still work
    tokens = tokenize("42 // trailing comment")
    assert len(tokens) == 1
    assert tokens[0].value == "42"


def test_divide_not_comment():
    # A single "/" is division, not a comment — only "//" is a comment
    tokens = tokenize("10 / 2")
    assert len(tokens) == 3
    assert tokens[1].token_type == TokenType.DIVIDE


# ── Whitespace handling ──────────────────────────────────────────
# Spaces, tabs, newlines, and carriage returns are skipped between tokens.

def test_empty_source():
    # Empty input should produce no tokens
    assert tokenize("") == []


def test_whitespace_only():
    # Input that is all whitespace should produce no tokens
    assert tokenize("   \t\n\r  ") == []


def test_mixed_whitespace():
    # Tokens separated by tabs, newlines, and spaces should all be found
    tokens = tokenize("  42\t\n  7  ")
    assert len(tokens) == 2


# ── Line and column tracking ─────────────────────────────────────
# Each token records its line and column position (both start at 1).

def test_line_col_first_token():
    # The very first token should be at line 1, column 1
    tokens = tokenize("hello")
    assert tokens[0].line == 1
    assert tokens[0].col == 1


def test_line_col_second_line():
    # A token after a newline should be on line 2
    tokens = tokenize("a\nb")
    assert tokens[0].line == 1
    assert tokens[1].line == 2
    assert tokens[1].col == 1


def test_line_col_with_spaces():
    # Leading spaces should shift the column number
    tokens = tokenize("  x")
    assert tokens[0].col == 3


# ── Token __repr__ ───────────────────────────────────────────────
# The Token class has a custom __repr__ for readable debug output.

def test_token_repr():
    # Check the format of repr for a simple operator token
    tok = Token(TokenType.PLUS, "+", 1, 5)
    assert repr(tok) == "Token(PLUS, '+', line=1, col=5)"


def test_token_repr_string():
    # Check repr for a string literal token
    tok = Token(TokenType.STRING_LITERAL, "hi", 3, 2)
    assert repr(tok) == "Token(STRING_LITERAL, 'hi', line=3, col=2)"


# ── TokenizerError ───────────────────────────────────────────────
# The custom error class should include the line, column, and message.

def test_tokenizer_error_message():
    # Verify the error message format and that line/col are stored
    err = TokenizerError("bad char", 5, 10)
    assert "line 5" in str(err)
    assert "col 10" in str(err)
    assert "bad char" in str(err)
    assert err.line == 5
    assert err.col == 10


def test_unexpected_character_raises():
    # Characters not in the language (like @) should raise TokenizerError
    with pytest.raises(TokenizerError):
        tokenize("@")


def test_unexpected_character_position():
    # The error should report the correct position of the bad character
    try:
        tokenize("  @")
    except TokenizerError as e:
        assert e.line == 1
        assert e.col == 3


# ── Tokenizer internal methods ───────────────────────────────────
# These test the helper methods on the Tokenizer class directly.

def test_peek_at_end():
    # peek() should return None when there are no more characters
    t = Tokenizer("")
    assert t.peek() is None


def test_peek_next_at_end():
    # peek_next() should return None when there is only one character left
    t = Tokenizer("a")
    assert t.peek_next() is None


def test_peek_next_returns_char():
    # peek_next() should return the character after the current position
    t = Tokenizer("ab")
    assert t.peek_next() == "b"


def test_match_mismatch():
    # match() should return False and NOT advance if the character doesn't match
    t = Tokenizer("a")
    assert t.match("b") is False


def test_match_success():
    # match() should return True and advance past the character if it matches
    t = Tokenizer("a")
    assert t.match("a") is True
    assert t.pos == 1


# ── Integration tests ────────────────────────────────────────────
# These test realistic multi-token inputs that combine several token types.

def test_complex_expression():
    # A math expression with parentheses, operators, and an assignment
    tokens = tokenize("x = (1 + 2) * 3")
    types = [t.token_type for t in tokens]
    assert types == [
        TokenType.IDENTIFIER,
        TokenType.ASSIGN,
        TokenType.LEFT_PAREN,
        TokenType.INTEGER_LITERAL,
        TokenType.PLUS,
        TokenType.INTEGER_LITERAL,
        TokenType.RIGHT_PAREN,
        TokenType.MULTIPLY,
        TokenType.INTEGER_LITERAL,
    ]


def test_class_declaration_snippet():
    # A snippet that looks like a ClassC class definition
    tokens = tokenize("class Dog init(name) vardec Int x = 0")
    assert tokens[0].token_type == TokenType.CLASS
    assert tokens[1].token_type == TokenType.IDENTIFIER  # "Dog" is not a keyword
    assert tokens[2].token_type == TokenType.INIT


def test_while_if_return():
    # A control-flow snippet with while, if, comparisons, and return
    tokens = tokenize("while (x < 10) if (x == 5) return x")
    types = [t.token_type for t in tokens]
    assert TokenType.WHILE in types
    assert TokenType.IF in types
    assert TokenType.RETURN in types
    assert TokenType.LESS_THAN in types
    assert TokenType.DOUBLE_EQUALS in types


def test_multiline_source():
    # Tokens on different lines should have correct line numbers
    tokens = tokenize("vardec Int x = 5\nprintln(x)")
    assert tokens[0].token_type == TokenType.VARDEC
    # println is on the second line
    println_tok = [t for t in tokens if t.token_type == TokenType.PRINTLN][0]
    assert println_tok.line == 2


def test_divide_at_end_of_input():
    # "/" at the end of input (no next char to form "//") should be DIVIDE
    tokens = tokenize("3/")
    assert tokens[1].token_type == TokenType.DIVIDE


def test_assign_at_end_of_input():
    # "=" at the end of input (no next char to form "==") should be ASSIGN
    tokens = tokenize("x =")
    assert tokens[1].token_type == TokenType.ASSIGN
