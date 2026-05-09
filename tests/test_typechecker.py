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


def test_typecheck_rejects_println_object():
    source = """
    (class Animal
      ()
      (init ()))

    (vardec Animal a)
    (= a (new Animal))
    (println a)
    """
    with pytest.raises(TypecheckError, match="println"):
        typecheck(source)

def test_typecheck_rejects_ambiguous_overload_resolution():
    source = """
    (class A () (init ()))
    (class B A () (init () (super)))

    (class C
      ()
      (init ())
      (method pick ((vardec A a) (vardec B b)) Int
        (return 1))
      (method pick ((vardec B b) (vardec A a)) Int
        (return 2)))

    (vardec C c)
    (vardec B b)
    (= c (new C))
    (= b (new B))
    (println (call c pick b b))
    """
    with pytest.raises(TypecheckError, match="Ambiguous overload"):
        typecheck(source)


def test_typecheck_rejects_cyclic_inheritance():
    source = """
    (class A B () (init () (super)))
    (class B A () (init () (super)))
    (println 0)
    """
    with pytest.raises(TypecheckError, match="Inheritance cycle"):
        typecheck(source)


def test_typecheck_rejects_duplicate_class():
    source = """
    (class A () (init ()))
    (class A () (init ()))
    (println 0)
    """
    with pytest.raises(TypecheckError, match="Duplicate class"):
        typecheck(source)


def test_typecheck_rejects_duplicate_field():
    source = """
    (class A
      ((vardec Int x) (vardec Int x))
      (init ()))
    (println 0)
    """
    with pytest.raises(TypecheckError, match="Duplicate field"):
        typecheck(source)


def test_typecheck_rejects_duplicate_parameter():
    source = """
    (class A
      ()
      (init ())
      (method bad ((vardec Int x) (vardec Boolean x)) Void))
    (println 0)
    """
    with pytest.raises(TypecheckError, match="Duplicate parameter"):
        typecheck(source)


def test_typecheck_rejects_while_assignment_as_initialization():
    source = """
    (vardec Int x)
    (while true
      (= x 1))
    (println x)
    """
    with pytest.raises(TypecheckError, match="initialized"):
        typecheck(source)


def test_typecheck_rejects_if_without_else_as_initialization():
    source = """
    (vardec Int x)
    (if true
      (= x 1))
    (println x)
    """
    with pytest.raises(TypecheckError, match="initialized"):
        typecheck(source)


def test_typecheck_rejects_override_return_type_mismatch():
    source = """
    (class Animal
      ()
      (init ())
      (method speak () Int
        (return 1)))

    (class Dog Animal
      ()
      (init ()
        (super))
      (method speak () Boolean
        (return true)))

    (println 0)
    """
    with pytest.raises(TypecheckError, match="different return type"):
        typecheck(source)


def test_typecheck_rejects_wrong_argument_type_call():
    source = """
    (class Animal () (init ()))
    (class Cat Animal () (init () (super)))
    (class Dog Animal () (init () (super)))

    (class Vet
      ()
      (init ())
      (method treatDog ((vardec Dog d)) Void))

    (vardec Vet v)
    (vardec Cat c)
    (= v (new Vet))
    (= c (new Cat))
    (call v treatDog c)
    """
    with pytest.raises(TypecheckError, match="No matching overload"):
        typecheck(source)


def test_typecheck_rejects_sibling_assignment():
    source = """
    (class Animal () (init ()))
    (class Cat Animal () (init () (super)))
    (class Dog Animal () (init () (super)))

    (vardec Cat c)
    (= c (new Dog))
    """
    with pytest.raises(TypecheckError, match="Cannot assign"):
        typecheck(source)


def test_typecheck_rejects_new_string():
    source = """
    (vardec String s)
    (= s (new String))
    """
    with pytest.raises(TypecheckError, match="String"):
        typecheck(source)


def test_typecheck_rejects_call_on_string():
    source = """
    (println (call "hello" length))
    """
    with pytest.raises(TypecheckError, match="String"):
        typecheck(source)
