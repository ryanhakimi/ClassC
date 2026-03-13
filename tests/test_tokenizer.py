import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tokenizer import Token, Tokenizer, TokenizerError, TokenType, tokenize


# Single-character tokens

def test_single_character_tokens():
    tokens = tokenize("()+-*/<")
    types = [t.token_type for t in tokens]
    assert types == [
        TokenType.LEFT_PAREN,
        TokenType.RIGHT_PAREN,
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.MULTIPLY,
        TokenType.DIVIDE,
        TokenType.LESS_THAN,
    ]


# Assignment vs equality

def test_assign_and_double_equals():
    tokens = tokenize("= ==")
    assert tokens[0].token_type == TokenType.ASSIGN
    assert tokens[0].value == "="
    assert tokens[1].token_type == TokenType.DOUBLE_EQUALS
    assert tokens[1].value == "=="


# Keywords

def test_keywords():
    source = (
        "Int Boolean Void true false this break println while if "
        "return vardec method init super class new call"
    )
    tokens = tokenize(source)
    expected = [
        TokenType.INT_TYPE, TokenType.BOOLEAN_TYPE, TokenType.VOID_TYPE,
        TokenType.TRUE, TokenType.FALSE, TokenType.THIS, TokenType.BREAK,
        TokenType.PRINTLN, TokenType.WHILE, TokenType.IF, TokenType.RETURN,
        TokenType.VARDEC, TokenType.METHOD, TokenType.INIT, TokenType.SUPER,
        TokenType.CLASS, TokenType.NEW, TokenType.CALL,
    ]
    assert [t.token_type for t in tokens] == expected


# Identifiers

def test_identifiers():
    tokens = tokenize("myVar _foo var1")
    assert all(t.token_type == TokenType.IDENTIFIER for t in tokens)
    assert [t.value for t in tokens] == ["myVar", "_foo", "var1"]


# Integer literals 

def test_integer_literals():
    tokens = tokenize("0 42 100")
    assert all(t.token_type == TokenType.INTEGER_LITERAL for t in tokens)
    assert [t.value for t in tokens] == ["0", "42", "100"]


def test_integer_followed_by_letter_raises():
    with pytest.raises(TokenizerError):
        tokenize("123abc")


# Whitespace handling 

def test_empty_source():
    assert tokenize("") == []


def test_whitespace_only():
    assert tokenize("   \t\n\r  ") == []


# Line and column tracking 

def test_multiline_tracking():
    tokens = tokenize("a\nb")
    assert tokens[0].line == 1
    assert tokens[1].line == 2
    assert tokens[1].col == 1


# Error handling

def test_unexpected_character_raises():
    with pytest.raises(TokenizerError):
        tokenize("@")


# Integration: spec example

def test_class_definition_from_spec():
    source = (
        "(class Animal ()\n"
        "  (init ())\n"
        "  (method speak () Void\n"
        "    (return (println 0))))"
    )
    tokens = tokenize(source)
    types = [t.token_type for t in tokens]
    assert TokenType.CLASS in types
    assert TokenType.IDENTIFIER in types
    assert TokenType.INIT in types
    assert TokenType.METHOD in types
    assert TokenType.RETURN in types
    assert TokenType.PRINTLN in types
    assert TokenType.INTEGER_LITERAL in types
    assert TokenType.VOID_TYPE in types
