import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from codegen import generate_c


def test_codegen_contains_vtables_and_structs():
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
    output = generate_c(source)
    assert "struct Animal" in output
    assert "struct Cat" in output
    assert "Animal_vtable" in output
    assert "Cat_vtable" in output
    assert "new_Cat" in output
    assert "Cat_speak__void" in output


def test_codegen_handles_string_literals():
    output = generate_c('(println "hello")')
    assert 'ClassC_print_string("hello")' in output


def test_codegen_emits_main_function():
    output = generate_c("(println 1)")
    assert "int main(void)" in output
    assert "return 0;" in output
