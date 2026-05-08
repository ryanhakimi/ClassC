import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from parser import ClassType, IntType, VoidType
from typechecker import TypecheckError, typecheck


def test_typecheck_animals_program():
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

    (vardec Animal pet)
    (= pet (new Cat))
    (call pet speak)
    """
    typed_program = typecheck(source)
    assert "Animal" in typed_program.classes
    assert "Cat" in typed_program.classes


def test_typecheck_rejects_use_before_init():
    source = """
    (vardec Int x)
    (println x)
    """
    with pytest.raises(TypecheckError, match="initialized"):
        typecheck(source)


def test_typecheck_allows_init_then_use():
    source = """
    (vardec Int x)
    (= x 5)
    (println x)
    """
    typecheck(source)


def test_typecheck_rejects_non_boolean_if_condition():
    source = """
    (if 1 (println 0))
    """
    with pytest.raises(TypecheckError, match="Boolean"):
        typecheck(source)


def test_typecheck_rejects_missing_return():
    source = """
    (class Counter
      ()
      (init ())
      (method bad () Int
        (vardec Int x)
        (= x 1)))
    (println 0)
    """
    with pytest.raises(TypecheckError, match="may not return"):
        typecheck(source)


def test_typecheck_accepts_if_else_both_return():
    source = """
    (class Counter
      ()
      (init ())
      (method good ((vardec Boolean flag)) Int
        (if flag
            (return 1)
            (return 2))))
    (println 0)
    """
    typecheck(source)


def test_typecheck_supports_overloading_and_subtyping():
    source = """
    (class Animal
      ()
      (init ())
      (method id ((vardec Animal other)) Int
        (return 1)))

    (class Dog Animal
      ()
      (init ()
        (super))
      (method id ((vardec Dog other)) Int
        (return 2)))

    (vardec Dog d)
    (= d (new Dog))
    (println (call d id d))
    """
    typecheck(source)


def test_typecheck_rejects_break_outside_loop():
    with pytest.raises(TypecheckError, match="inside a while"):
        typecheck("break")


def test_typecheck_supports_string_literals():
    source = '(println "hello")'
    typecheck(source)
