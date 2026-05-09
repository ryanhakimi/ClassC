import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tokenizer import Token, TokenType, tokenize
from parser import (
    Parser, ParseError, parse,
    IntType, BooleanType, VoidType, ClassType,
    IntLiteralExp, VarExp, ThisExp, TrueExp, FalseExp,
    PrintlnExp, BinOpExp, CallExp, NewExp,
    VarDecStmt, AssignStmt, WhileStmt, BreakStmt, IfStmt, ReturnStmt, ExpStmt,
    MethodDef, Constructor, ClassDef, Program, PlusOp, MinusOp, MultiplyOp, DivideOp, LessThanOp, DoubleEqualsOp,
)


# Helper functions for parsing from source strings
def parse_exp(source):
    tokens = tokenize(source)
    p = Parser(tokens)
    return p.parse_expression()


def parse_stmt(source):
    tokens = tokenize(source)
    p = Parser(tokens)
    return p.parse_statement()


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
    assert isinstance(result.op, PlusOp)
    assert result.left == IntLiteralExp(1)
    assert result.right == IntLiteralExp(2)


def test_parse_binop_minus():
    result = parse_exp("(- 10 3)")
    assert isinstance(result, BinOpExp)
    assert isinstance(result.op, MinusOp)


def test_parse_binop_multiply():
    result = parse_exp("(* 4 5)")
    assert isinstance(result, BinOpExp)
    assert isinstance(result.op, MultiplyOp)


def test_parse_binop_divide():
    result = parse_exp("(/ 10 2)")
    assert isinstance(result, BinOpExp)
    assert isinstance(result.op, DivideOp)


def test_parse_binop_less_than():
    result = parse_exp("(< x 10)")
    assert isinstance(result, BinOpExp)
    assert isinstance(result.op, LessThanOp)
    assert isinstance(result.left, VarExp)
    assert isinstance(result.right, IntLiteralExp)


def test_parse_binop_equals():
    result = parse_exp("(== x y)")
    assert isinstance(result, BinOpExp)
    assert isinstance(result.op, DoubleEqualsOp)
    assert isinstance(result.left, VarExp)
    assert isinstance(result.right, VarExp)


def test_parse_binop_nested():
    result = parse_exp("(+ (* 2 3) (- 5 1))")
    assert isinstance(result, BinOpExp)
    assert isinstance(result.op, PlusOp)
    assert isinstance(result.left, BinOpExp)
    assert isinstance(result.left.op, MultiplyOp)
    assert isinstance(result.right, BinOpExp)
    assert isinstance(result.right.op, MinusOp)


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


def test_parse_vardec_int():
    result = parse_stmt("(vardec Int x)")
    assert isinstance(result, VarDecStmt)
    assert isinstance(result.var_type, IntType)
    assert result.var_name == "x"


def test_parse_vardec_boolean():
    result = parse_stmt("(vardec Boolean flag)")
    assert isinstance(result, VarDecStmt)
    assert isinstance(result.var_type, BooleanType)
    assert result.var_name == "flag"


def test_parse_vardec_class_type():
    result = parse_stmt("(vardec Animal pet)")
    assert isinstance(result, VarDecStmt)
    assert isinstance(result.var_type, ClassType)
    assert result.var_type.name == "Animal"
    assert result.var_name == "pet"


def test_parse_vardec_void_type():
    result = parse_stmt("(vardec Void nothing)")
    assert isinstance(result, VarDecStmt)
    assert isinstance(result.var_type, VoidType)
    assert result.var_name == "nothing"


def test_parse_assignment():
    result = parse_stmt("(= x 5)")
    assert isinstance(result, AssignStmt)
    assert result.var_name == "x"
    assert isinstance(result.expression, IntLiteralExp)
    assert result.expression.value == 5


def test_parse_assignment_with_expression():
    result = parse_stmt("(= y (+ x 1))")
    assert isinstance(result, AssignStmt)
    assert result.var_name == "y"
    assert isinstance(result.expression, BinOpExp)


def test_parse_while_empty_body():
    result = parse_stmt("(while true)")
    assert isinstance(result, WhileStmt)
    assert isinstance(result.condition, TrueExp)
    assert result.body == []


def test_parse_while_with_body():
    result = parse_stmt("(while (< x 10) (= x (+ x 1)))")
    assert isinstance(result, WhileStmt)
    assert isinstance(result.condition, BinOpExp)
    assert len(result.body) == 1
    assert isinstance(result.body[0], AssignStmt)


def test_parse_while_multiple_stmts():
    result = parse_stmt("(while true (= x 1) (= y 2) break)")
    assert isinstance(result, WhileStmt)
    assert len(result.body) == 3
    assert isinstance(result.body[0], AssignStmt)
    assert isinstance(result.body[1], AssignStmt)
    assert isinstance(result.body[2], BreakStmt)


def test_parse_break():
    result = parse_stmt("break")
    assert isinstance(result, BreakStmt)


def test_parse_if_no_else():
    result = parse_stmt("(if true (= x 1))")
    assert isinstance(result, IfStmt)
    assert isinstance(result.condition, TrueExp)
    assert isinstance(result.then_stmt, AssignStmt)
    assert result.else_stmt is None


def test_parse_if_with_else():
    result = parse_stmt("(if (< x 0) (= x 0) (= x 1))")
    assert isinstance(result, IfStmt)
    assert isinstance(result.condition, BinOpExp)
    assert isinstance(result.then_stmt, AssignStmt)
    assert isinstance(result.else_stmt, AssignStmt)


def test_parse_if_nested():
    result = parse_stmt("(if true (if false (= x 1)))")
    assert isinstance(result, IfStmt)
    assert isinstance(result.then_stmt, IfStmt)
    assert result.then_stmt.else_stmt is None


def test_parse_return_void():
    result = parse_stmt("(return)")
    assert isinstance(result, ReturnStmt)
    assert result.expression is None


def test_parse_return_with_value():
    result = parse_stmt("(return 42)")
    assert isinstance(result, ReturnStmt)
    assert isinstance(result.expression, IntLiteralExp)
    assert result.expression.value == 42


def test_parse_return_with_expression():
    result = parse_stmt("(return (+ x y))")
    assert isinstance(result, ReturnStmt)
    assert isinstance(result.expression, BinOpExp)


def test_parse_expression_statement_println():
    result = parse_stmt("(println 42)")
    assert isinstance(result, ExpStmt)
    assert isinstance(result.expression, PrintlnExp)


def test_parse_expression_statement_call():
    result = parse_stmt("(call obj doStuff)")
    assert isinstance(result, ExpStmt)
    assert isinstance(result.expression, CallExp)
    assert result.expression.method_name == "doStuff"


def test_parse_statement_error_end_of_input():
    p = Parser([])
    with pytest.raises(ParseError, match="end of input"):
        p.parse_statement()


def test_parse_statement_error_unexpected_token():
    with pytest.raises(ParseError):
        parse_stmt("42")


def test_parse_statement_error_paren_end_of_input():
    tokens = tokenize("(")
    p = Parser(tokens)
    with pytest.raises(ParseError, match="end of input"):
        p.parse_statement()


def test_parse_method_no_params():
    tokens = tokenize("(method speak () Void (return))")
    p = Parser(tokens)
    result = p.parse_method()
    assert isinstance(result, MethodDef)
    assert result.name == "speak"
    assert result.params == []
    assert isinstance(result.return_type, VoidType)
    assert len(result.body) == 1
    assert isinstance(result.body[0], ReturnStmt)


def test_parse_method_with_params():
    tokens = tokenize("(method add ((vardec Int a) (vardec Int b)) Int (return (+ a b)))")
    p = Parser(tokens)
    result = p.parse_method()
    assert result.name == "add"
    assert len(result.params) == 2
    assert result.params[0].var_name == "a"
    assert result.params[1].var_name == "b"
    assert isinstance(result.return_type, IntType)
    assert len(result.body) == 1


def test_parse_method_empty_body():
    tokens = tokenize("(method noop () Void)")
    p = Parser(tokens)
    result = p.parse_method()
    assert result.name == "noop"
    assert result.body == []


def test_parse_method_multiple_stmts():
    tokens = tokenize("(method doStuff () Void (vardec Int x) (= x 5) (return))")
    p = Parser(tokens)
    result = p.parse_method()
    assert len(result.body) == 3
    assert isinstance(result.body[0], VarDecStmt)
    assert isinstance(result.body[1], AssignStmt)
    assert isinstance(result.body[2], ReturnStmt)


def test_parse_method_returns_class_type():
    tokens = tokenize("(method create () Animal (return (new Animal)))")
    p = Parser(tokens)
    result = p.parse_method()
    assert isinstance(result.return_type, ClassType)
    assert result.return_type.name == "Animal"


def test_parse_method_boolean_return():
    tokens = tokenize("(method isPositive ((vardec Int x)) Boolean (return (< 0 x)))")
    p = Parser(tokens)
    result = p.parse_method()
    assert result.name == "isPositive"
    assert isinstance(result.return_type, BooleanType)
    assert isinstance(result.body[0], ReturnStmt)
    assert isinstance(result.body[0].expression, BinOpExp)


def test_parse_constructor_empty():
    tokens = tokenize("(init ())")
    p = Parser(tokens)
    result = p.parse_constructor()
    assert isinstance(result, Constructor)
    assert result.params == []
    assert result.super_args is None
    assert result.body == []


def test_parse_constructor_with_params():
    tokens = tokenize("(init ((vardec Int x)))")
    p = Parser(tokens)
    result = p.parse_constructor()
    assert len(result.params) == 1
    assert result.params[0].var_name == "x"


def test_parse_constructor_with_super_no_args():
    tokens = tokenize("(init () (super))")
    p = Parser(tokens)
    result = p.parse_constructor()
    assert result.super_args == []


def test_parse_constructor_with_super_args():
    tokens = tokenize("(init ((vardec Int x)) (super x 5))")
    p = Parser(tokens)
    result = p.parse_constructor()
    assert len(result.params) == 1
    assert len(result.super_args) == 2
    assert isinstance(result.super_args[0], VarExp)
    assert isinstance(result.super_args[1], IntLiteralExp)


def test_parse_constructor_with_body():
    tokens = tokenize("(init () (= x 0) (= y 0))")
    p = Parser(tokens)
    result = p.parse_constructor()
    assert result.super_args is None
    assert len(result.body) == 2


def test_parse_constructor_super_and_body():
    tokens = tokenize("(init () (super) (= x 0))")
    p = Parser(tokens)
    result = p.parse_constructor()
    assert result.super_args == []
    assert len(result.body) == 1
    assert isinstance(result.body[0], AssignStmt)


def test_parse_class_minimal():
    tokens = tokenize("(class Foo () (init ()))")
    p = Parser(tokens)
    result = p.parse_class()
    assert isinstance(result, ClassDef)
    assert result.name == "Foo"
    assert result.parent is None
    assert result.fields == []
    assert isinstance(result.constructor, Constructor)
    assert result.methods == []


def test_parse_class_with_parent():
    tokens = tokenize("(class Cat Animal () (init () (super)))")
    p = Parser(tokens)
    result = p.parse_class()
    assert result.name == "Cat"
    assert result.parent == "Animal"


def test_parse_class_with_fields():
    source = "(class Point ((vardec Int x) (vardec Int y)) (init ()))"
    tokens = tokenize(source)
    p = Parser(tokens)
    result = p.parse_class()
    assert result.name == "Point"
    assert len(result.fields) == 2
    assert result.fields[0].var_name == "x"
    assert result.fields[1].var_name == "y"


def test_parse_class_with_methods():
    source = """
    (class Animal
      ()
      (init ())
      (method speak () Void
        (return (println 0))))
    """
    tokens = tokenize(source)
    p = Parser(tokens)
    result = p.parse_class()
    assert result.name == "Animal"
    assert len(result.methods) == 1
    assert result.methods[0].name == "speak"


def test_parse_class_with_multiple_methods():
    source = """
    (class Calc
      ()
      (init ())
      (method add ((vardec Int a) (vardec Int b)) Int
        (return (+ a b)))
      (method sub ((vardec Int a) (vardec Int b)) Int
        (return (- a b))))
    """
    tokens = tokenize(source)
    p = Parser(tokens)
    result = p.parse_class()
    assert len(result.methods) == 2
    assert result.methods[0].name == "add"
    assert result.methods[1].name == "sub"


def test_parse_class_full():
    source = """
    (class Dog Animal
      ((vardec Int age))
      (init ((vardec Int a))
        (super)
        (= age a))
      (method getAge () Int
        (return age))
      (method speak () Void
        (return (println 2))))
    """
    tokens = tokenize(source)
    p = Parser(tokens)
    result = p.parse_class()
    assert result.name == "Dog"
    assert result.parent == "Animal"
    assert len(result.fields) == 1
    assert result.fields[0].var_name == "age"
    assert len(result.constructor.params) == 1
    assert result.constructor.super_args == []
    assert len(result.constructor.body) == 1
    assert len(result.methods) == 2


def test_parse_program_stmts_only():
    result = parse("(vardec Int x) (= x 5)")
    assert isinstance(result, Program)
    assert result.classes == []
    assert len(result.statements) == 2


def test_parse_program_single_stmt():
    result = parse("(return 0)")
    assert isinstance(result, Program)
    assert len(result.statements) == 1


def test_parse_program_with_classes():
    source = """
    (class Animal
      ()
      (init ())
      (method speak () Void
        (return (println 0))))

    (class Cat Animal
      ()
      (init ()
        (super))
      (method speak () Void
        (return (println 1))))

    (vardec Animal cat)
    (= cat (new Cat))
    """
    result = parse(source)
    assert len(result.classes) == 2
    assert result.classes[0].name == "Animal"
    assert result.classes[1].name == "Cat"
    assert len(result.statements) == 2


def test_parse_program_empty_raises():
    with pytest.raises(ParseError, match="at least one statement"):
        parse("")


def test_parse_program_only_classes_raises():
    source = "(class Foo () (init ()))"
    with pytest.raises(ParseError, match="at least one statement"):
        parse(source)


def test_parse_program_break_as_entry():
    result = parse("break")
    assert len(result.statements) == 1
    assert isinstance(result.statements[0], BreakStmt)


def test_parse_call_as_stmt_in_program():
    result = parse("(call obj doStuff)")
    assert len(result.statements) == 1
    assert isinstance(result.statements[0], ExpStmt)
    assert isinstance(result.statements[0].expression, CallExp)


def test_parse_animals_example():
    source = """
    (class Animal
      ()
      (init ())
      (method speak () Void
        (return (println 0))))

    (class Cat Animal
      ()
      (init ()
        (super))
      (method speak () Void
        (return (println 1))))

    (class Dog Animal
      ()
      (init ()
        (super))
      (method speak () Void
        (return (println 2))))

    (vardec Animal cat)
    (vardec Animal dog)
    (= cat (new Cat))
    (= dog (new Dog))
    (call cat speak)
    (call dog speak)
    """
    result = parse(source)
    assert isinstance(result, Program)
    assert len(result.classes) == 3
    assert result.classes[0].name == "Animal"
    assert result.classes[0].parent is None
    assert result.classes[1].name == "Cat"
    assert result.classes[1].parent == "Animal"
    assert result.classes[2].name == "Dog"
    assert result.classes[2].parent == "Animal"
    assert len(result.statements) == 6
    assert isinstance(result.statements[0], VarDecStmt)
    assert result.statements[0].var_name == "cat"
    assert isinstance(result.statements[0].var_type, ClassType)
    assert isinstance(result.statements[1], VarDecStmt)
    assert result.statements[1].var_name == "dog"
    assert isinstance(result.statements[2], AssignStmt)
    assert isinstance(result.statements[2].expression, NewExp)
    assert result.statements[2].expression.class_name == "Cat"
    assert isinstance(result.statements[3], AssignStmt)
    assert isinstance(result.statements[3].expression, NewExp)
    assert result.statements[3].expression.class_name == "Dog"


# Edge cases and error handling
def test_parse_deeply_nested_expression():
    result = parse_exp("(+ (+ (+ 1 2) 3) 4)")
    assert isinstance(result, BinOpExp)
    assert isinstance(result.left, BinOpExp)
    assert isinstance(result.left.left, BinOpExp)
    assert result.left.left.left == IntLiteralExp(1)


def test_parse_call_expression_as_arg():
    result = parse_exp("(call x foo (call y bar))")
    assert isinstance(result, CallExp)
    assert len(result.args) == 1
    assert isinstance(result.args[0], CallExp)


def test_parse_new_in_assignment():
    result = parse_stmt("(= obj (new MyClass 1 2 3))")
    assert isinstance(result, AssignStmt)
    assert isinstance(result.expression, NewExp)
    assert result.expression.class_name == "MyClass"
    assert len(result.expression.args) == 3


def test_parse_while_with_break():
    result = parse_stmt("(while true break)")
    assert isinstance(result, WhileStmt)
    assert len(result.body) == 1
    assert isinstance(result.body[0], BreakStmt)


def test_parse_while_with_if_and_break():
    result = parse_stmt("(while (< x 10) (if (== x 5) break) (= x (+ x 1)))")
    assert isinstance(result, WhileStmt)
    assert len(result.body) == 2
    assert isinstance(result.body[0], IfStmt)
    assert isinstance(result.body[0].then_stmt, BreakStmt)
    assert isinstance(result.body[1], AssignStmt)


def test_parse_error_missing_closing_paren():
    with pytest.raises(ParseError):
        parse_exp("(+ 1 2")


def test_parse_error_expect_wrong_token():
    tokens = tokenize("42")
    p = Parser(tokens)
    with pytest.raises(ParseError, match="Expected LEFT_PAREN"):
        p.expect(TokenType.LEFT_PAREN)


def test_parse_error_expect_end_of_input():
    p = Parser([])
    with pytest.raises(ParseError, match="end of input"):
        p.expect(TokenType.LEFT_PAREN)


def test_parser_peek_returns_none_at_end():
    p = Parser([])
    assert p.peek() is None


def test_parser_at_end():
    p = Parser([])
    assert p.at_end() is True


def test_parser_at_end_false():
    tokens = tokenize("42")
    p = Parser(tokens)
    assert p.at_end() is False


def test_parser_advance():
    tokens = tokenize("42")
    p = Parser(tokens)
    tok = p.advance()
    assert tok.token_type == TokenType.INTEGER_LITERAL
    assert p.pos == 1


def test_parse_error_attributes():
    tok = Token(TokenType.PLUS, "+", 3, 7)
    err = ParseError("bad token", tok)
    assert err.token == tok
    assert "line 3" in str(err)
    assert "col 7" in str(err)


def test_parse_error_no_token():
    err = ParseError("something wrong")
    assert err.token is None
    assert "something wrong" in str(err)


def test_parse_boolean_expression_in_condition():
    result = parse_stmt("(if (== x true) (return false))")
    assert isinstance(result, IfStmt)
    assert isinstance(result.condition, BinOpExp)
    assert isinstance(result.condition.right, TrueExp)
    body = result.then_stmt
    assert isinstance(body, ReturnStmt)
    assert isinstance(body.expression, FalseExp)


def test_parse_new_expression_complex_args():
    result = parse_exp("(new Pair (new Left 1) (new Right 2))")
    assert isinstance(result, NewExp)
    assert result.class_name == "Pair"
    assert len(result.args) == 2
    assert isinstance(result.args[0], NewExp)
    assert isinstance(result.args[1], NewExp)


def test_parse_println_in_expression():
    result = parse_exp("(println (+ 1 2))")
    assert isinstance(result, PrintlnExp)
    assert isinstance(result.expression, BinOpExp)


# ── Complex integration tests ──────────────────────────────────

def test_parse_method_with_while_loop():
    source = """
    (class Counter
      ((vardec Int count))
      (init ()
        (= count 0))
      (method countTo ((vardec Int n)) Void
        (while (< count n)
          (= count (+ count 1)))))
    (vardec Counter c)
    (= c (new Counter))
    (call c countTo 10)
    """
    result = parse(source)
    assert len(result.classes) == 1
    cls = result.classes[0]
    assert cls.name == "Counter"
    assert len(cls.fields) == 1
    assert len(cls.methods) == 1
    method = cls.methods[0]
    assert method.name == "countTo"
    assert len(method.params) == 1
    assert len(method.body) == 1
    assert isinstance(method.body[0], WhileStmt)


def test_parse_if_else_in_method():
    source = """
    (class Math
      ()
      (init ())
      (method abs ((vardec Int x)) Int
        (if (< x 0)
          (return (- 0 x))
          (return x))))
    (vardec Int result)
    (= result (call (new Math) abs (- 0 5)))
    """
    result = parse(source)
    assert len(result.classes) == 1
    method = result.classes[0].methods[0]
    assert method.name == "abs"
    assert isinstance(method.body[0], IfStmt)
    assert isinstance(method.body[0].then_stmt, ReturnStmt)
    assert isinstance(method.body[0].else_stmt, ReturnStmt)


def test_parse_multiple_classes_inheritance_chain():
    source = """
    (class A
      ()
      (init ()))
    (class B A
      ()
      (init ()
        (super)))
    (class C B
      ()
      (init ()
        (super)))
    (vardec C obj)
    (= obj (new C))
    """
    result = parse(source)
    assert len(result.classes) == 3
    assert result.classes[0].name == "A"
    assert result.classes[0].parent is None
    assert result.classes[1].name == "B"
    assert result.classes[1].parent == "A"
    assert result.classes[2].name == "C"
    assert result.classes[2].parent == "B"


def test_parse_constructor_with_multiple_params_and_super():
    source = """
    (class Base
      ((vardec Int x))
      (init ((vardec Int a))
        (= x a)))
    (class Child Base
      ((vardec Int y))
      (init ((vardec Int a) (vardec Int b))
        (super a)
        (= y b)))
    (vardec Child c)
    (= c (new Child 1 2))
    """
    result = parse(source)
    assert len(result.classes) == 2
    child = result.classes[1]
    assert child.name == "Child"
    assert len(child.constructor.params) == 2
    assert len(child.constructor.super_args) == 1
    assert isinstance(child.constructor.super_args[0], VarExp)
    assert len(child.constructor.body) == 1
