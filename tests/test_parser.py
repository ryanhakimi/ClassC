import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tokenizer import Token, TokenType, tokenize
from parser import (
    Parser, ParseError,
    IntType, BooleanType, VoidType, ClassType,
    IntLiteralExp, VarExp, ThisExp, TrueExp, FalseExp,
    PrintlnExp, BinOpExp, CallExp, NewExp,
)


# Helper functions for parsing from source strings
def parse_exp(source):
    tokens = tokenize(source)
    p = Parser(tokens)
    return p.parse_expression()


def parse_type_from(source):
    tokens = tokenize(source)
    p = Parser(tokens)
    return p.parse_type()


# Type parsing tests
def test_parse_int_type():
    assert parse_type_from("Int") == IntType()


def test_parse_boolean_type():
    assert parse_type_from("Boolean") == BooleanType()


def test_parse_void_type():
    assert parse_type_from("Void") == VoidType()


def test_parse_class_type():
    result = parse_type_from("Animal")
    assert isinstance(result, ClassType)
    assert result.name == "Animal"


def test_parse_type_error_wrong_token():
    with pytest.raises(ParseError):
        parse_type_from("42")


def test_parse_type_error_end_of_input():
    p = Parser([])
    with pytest.raises(ParseError, match="end of input"):
        p.parse_type()


# Simple expression parsing tests
def test_parse_integer_literal():
    result = parse_exp("42")
    assert isinstance(result, IntLiteralExp)
    assert result.value == 42


def test_parse_integer_zero():
    result = parse_exp("0")
    assert isinstance(result, IntLiteralExp)
    assert result.value == 0


def test_parse_variable():
    result = parse_exp("myVar")
    assert isinstance(result, VarExp)
    assert result.name == "myVar"


def test_parse_this():
    result = parse_exp("this")
    assert isinstance(result, ThisExp)


def test_parse_true():
    result = parse_exp("true")
    assert isinstance(result, TrueExp)


def test_parse_false():
    result = parse_exp("false")
    assert isinstance(result, FalseExp)


def test_parse_expression_error_end_of_input():
    p = Parser([])
    with pytest.raises(ParseError, match="end of input"):
        p.parse_expression()


def test_parse_expression_error_unexpected_token():
    with pytest.raises(ParseError):
        parse_exp(")")


# Parenthesized expression parsing tests
def test_parse_println():
    result = parse_exp("(println 42)")
    assert isinstance(result, PrintlnExp)
    assert isinstance(result.expression, IntLiteralExp)
    assert result.expression.value == 42


def test_parse_println_var():
    result = parse_exp("(println x)")
    assert isinstance(result, PrintlnExp)
    assert isinstance(result.expression, VarExp)


def test_parse_binop_plus():
    result = parse_exp("(+ 1 2)")
    assert isinstance(result, BinOpExp)
    assert result.op == "+"
    assert result.left == IntLiteralExp(1)
    assert result.right == IntLiteralExp(2)


def test_parse_binop_minus():
    result = parse_exp("(- 10 3)")
    assert isinstance(result, BinOpExp)
    assert result.op == "-"


def test_parse_binop_multiply():
    result = parse_exp("(* 4 5)")
    assert isinstance(result, BinOpExp)
    assert result.op == "*"


def test_parse_binop_divide():
    result = parse_exp("(/ 10 2)")
    assert isinstance(result, BinOpExp)
    assert result.op == "/"


def test_parse_binop_less_than():
    result = parse_exp("(< x 10)")
    assert isinstance(result, BinOpExp)
    assert result.op == "<"
    assert isinstance(result.left, VarExp)
    assert isinstance(result.right, IntLiteralExp)


def test_parse_binop_equals():
    result = parse_exp("(== x y)")
    assert isinstance(result, BinOpExp)
    assert result.op == "=="
    assert isinstance(result.left, VarExp)
    assert isinstance(result.right, VarExp)


def test_parse_binop_nested():
    result = parse_exp("(+ (* 2 3) (- 5 1))")
    assert isinstance(result, BinOpExp)
    assert result.op == "+"
    assert isinstance(result.left, BinOpExp)
    assert result.left.op == "*"
    assert isinstance(result.right, BinOpExp)
    assert result.right.op == "-"


def test_parse_call_no_args():
    result = parse_exp("(call obj speak)")
    assert isinstance(result, CallExp)
    assert isinstance(result.obj, VarExp)
    assert result.obj.name == "obj"
    assert result.method_name == "speak"
    assert result.args == []


def test_parse_call_with_args():
    result = parse_exp("(call obj add 1 2)")
    assert isinstance(result, CallExp)
    assert result.method_name == "add"
    assert len(result.args) == 2
    assert result.args[0] == IntLiteralExp(1)
    assert result.args[1] == IntLiteralExp(2)


def test_parse_call_on_this():
    result = parse_exp("(call this getName)")
    assert isinstance(result, CallExp)
    assert isinstance(result.obj, ThisExp)
    assert result.method_name == "getName"


def test_parse_call_chained():
    result = parse_exp("(call (call obj getInner) doStuff)")
    assert isinstance(result, CallExp)
    assert isinstance(result.obj, CallExp)
    assert result.obj.method_name == "getInner"
    assert result.method_name == "doStuff"


def test_parse_new_no_args():
    result = parse_exp("(new Cat)")
    assert isinstance(result, NewExp)
    assert result.class_name == "Cat"
    assert result.args == []


def test_parse_new_with_args():
    result = parse_exp("(new Person 30 42)")
    assert isinstance(result, NewExp)
    assert result.class_name == "Person"
    assert len(result.args) == 2
    assert isinstance(result.args[0], IntLiteralExp)
    assert isinstance(result.args[1], IntLiteralExp)


def test_parse_paren_expression_error_end_of_input():
    tokens = tokenize("(")
    p = Parser(tokens)
    with pytest.raises(ParseError, match="end of input"):
        p.parse_expression()


def test_parse_paren_expression_error_invalid_token():
    with pytest.raises(ParseError):
        parse_exp("(break)")
