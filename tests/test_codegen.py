import os
import sys
import subprocess
import tempfile

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


def test_fixture_simple_println():
    """Test simple_println.classc compiles and runs correctly."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "simple_println.classc")
    with open(fixture_path, "r") as f:
        source = f.read()
    
    c_code = generate_c(source)
    
    # Verify basic structure
    assert "int main(void)" in c_code
    assert "ClassC_print_int(42)" in c_code
    
    # Compile and run
    with tempfile.TemporaryDirectory() as tmpdir:
        c_file = os.path.join(tmpdir, "test.c")
        exe_file = os.path.join(tmpdir, "test")
        
        with open(c_file, "w") as f:
            f.write(c_code)
        
        result = subprocess.run(
            ["gcc", "-o", exe_file, c_file],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Compilation failed: {result.stderr}"
        
        result = subprocess.run([exe_file], capture_output=True, text=True)
        assert result.returncode == 0
        assert result.stdout.strip() == "42"


def test_fixture_comprehensive():
    """Exercises all binary ops, this/field access, inherited fields, if-else,
    while, bool/string println, and virtual dispatch through a single program."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "comprehensive.classc")
    with open(fixture_path, "r") as f:
        source = f.read()

    c_code = generate_c(source)

    with tempfile.TemporaryDirectory() as tmpdir:
        c_file = os.path.join(tmpdir, "test.c")
        exe_file = os.path.join(tmpdir, "test")

        with open(c_file, "w") as f:
            f.write(c_code)

        result = subprocess.run(
            ["gcc", "-o", exe_file, c_file],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Compilation failed: {result.stderr}"

        result = subprocess.run([exe_file], capture_output=True, text=True)
        assert result.returncode == 0
        assert result.stdout.strip().splitlines() == [
            "10",     # Box.add: 7 + 3
            "1",      # classify(10): n > 0
            "-1",     # classify(-5): n < 0
            "0",      # classify(0): n == 0
            "42",     # 6 * 7
            "25",     # 100 / 4
            "true",   # 5 == 5
            "true",   # 3 < 7
            "done",   # string literal
            "1",      # cb.touch
            "2",      # cb.touch
            "6",      # cb.touch after while-loop ran 3 more times
            "16",     # cb.total: hits(6) + inherited n(10)
        ]


def test_fixture_animals():
    """Test animals.classc compiles and runs correctly."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "animals.classc")
    with open(fixture_path, "r") as f:
        source = f.read()
    
    c_code = generate_c(source)
    
    # Verify basic structure
    assert "struct Animal" in c_code
    assert "struct Cat" in c_code
    assert "new_Cat" in c_code
    
    # Compile and run
    with tempfile.TemporaryDirectory() as tmpdir:
        c_file = os.path.join(tmpdir, "test.c")
        exe_file = os.path.join(tmpdir, "test")
        
        with open(c_file, "w") as f:
            f.write(c_code)
        
        result = subprocess.run(
            ["gcc", "-o", exe_file, c_file],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Compilation failed: {result.stderr}"
        
        result = subprocess.run([exe_file], capture_output=True, text=True)
        assert result.returncode == 0
        assert result.stdout.strip() == "1\n2"
