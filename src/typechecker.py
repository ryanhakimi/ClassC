from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from parser import (
    AssignStmt,
    BinOpExp,
    BooleanType,
    BreakStmt,
    CallExp,
    ClassDef,
    ClassType,
    Constructor,
    ExpStmt,
    FalseExp,
    IfStmt,
    IntLiteralExp,
    IntType,
    MethodDef,
    NewExp,
    PrintlnExp,
    Program,
    ReturnStmt,
    StringLiteralExp,
    ThisExp,
    TrueExp,
    VarDecStmt,
    VarExp,
    VoidType,
    WhileStmt,
    parse,
)


@dataclass(frozen=True)
class MethodSignature:
    name: str
    param_types: tuple


@dataclass
class MethodInfo:
    owner: str
    name: str
    params: list
    return_type: object
    body: list
    slot_name: str

    @property
    def signature(self):
        return MethodSignature(self.name, tuple(type_key(param) for param in self.params))


@dataclass
class ClassInfo:
    name: str
    parent: Optional[str]
    fields: Dict[str, object]
    field_order: list
    constructor: Constructor
    methods: Dict[MethodSignature, MethodInfo]
    method_order: list


@dataclass
class TypedProgram:
    program: Program
    classes: Dict[str, ClassInfo]


class TypecheckError(Exception):
    pass


class TypeEnvironment:
    def __init__(self, variables=None, initialized=None, inside_loop=False):
        self.variables = dict(variables or {})
        self.initialized = set(initialized or set())
        self.inside_loop = inside_loop

    def copy(self):
        return TypeEnvironment(self.variables, self.initialized, self.inside_loop)


class TypeChecker:
    def __init__(self, program: Program):
        self.program = program
        self.classes: Dict[str, ClassInfo] = {
            "Object": ClassInfo("Object", None, {}, [], Constructor([], None, []), {}, []),
            "String": ClassInfo("String", "Object", {}, [], Constructor([], None, []), {}, []),
        }

    def check(self) -> TypedProgram:
        self._collect_classes()
        self._check_classes()
        self._check_entry_point()
        return TypedProgram(self.program, self.classes)

    def _collect_classes(self):
        for class_def in self.program.classes:
            if class_def.name in self.classes:
                raise TypecheckError(f"Duplicate class '{class_def.name}'")
            if class_def.name in {"Object", "String"}:
                raise TypecheckError(f"Cannot redefine built-in class '{class_def.name}'")
            fields = {}
            field_order = []
            for field in class_def.fields:
                self._validate_type_exists(field.var_type)
                if isinstance(field.var_type, VoidType):
                    raise TypecheckError(f"Field '{field.var_name}' in class '{class_def.name}' cannot have type Void")
                if field.var_name in fields:
                    raise TypecheckError(f"Duplicate field '{field.var_name}' in class '{class_def.name}'")
                fields[field.var_name] = field.var_type
                field_order.append(field.var_name)

            methods = {}
            method_order = []
            for method in class_def.methods:
                self._validate_type_exists(method.return_type)
                params = []
                seen_params = set()
                for param in method.params:
                    self._validate_type_exists(param.var_type)
                    if isinstance(param.var_type, VoidType):
                        raise TypecheckError(f"Parameter '{param.var_name}' in method '{method.name}' cannot have type Void")
                    if param.var_name in seen_params:
                        raise TypecheckError(f"Duplicate parameter '{param.var_name}' in method '{method.name}'")
                    seen_params.add(param.var_name)
                    params.append(param.var_type)
                slot_name = self._make_slot_name(method.name, params)
                info = MethodInfo(class_def.name, method.name, params, method.return_type, method.body, slot_name)
                if info.signature in methods:
                    raise TypecheckError(f"Duplicate overload for method '{method.name}' in class '{class_def.name}'")
                methods[info.signature] = info
                method_order.append(info.signature)

            self.classes[class_def.name] = ClassInfo(
                class_def.name,
                class_def.parent or "Object",
                fields,
                field_order,
                class_def.constructor,
                methods,
                method_order,
            )

        for class_def in self.program.classes:
            class_info = self.classes[class_def.name]
            if class_info.parent not in self.classes:
                raise TypecheckError(f"Class '{class_info.name}' extends unknown class '{class_info.parent}'")
            if class_info.parent == "String":
                raise TypecheckError("Cannot extend built-in class 'String'")

        self._check_inheritance_cycles()
        self._validate_override_compatibility()

    def _check_inheritance_cycles(self):
        for class_name in list(self.classes.keys()):
            seen = set()
            current = class_name
            while current is not None:
                if current in seen:
                    raise TypecheckError(f"Inheritance cycle detected involving class '{class_name}'")
                seen.add(current)
                current = self.classes[current].parent if current in self.classes else None

    def _validate_override_compatibility(self):
        for class_name, class_info in self.classes.items():
            parent_name = class_info.parent
            if parent_name is None or class_name in {"Object", "String"}:
                continue
            inherited = self._all_methods(parent_name)
            for signature, method in class_info.methods.items():
                if signature in inherited:
                    inherited_method = inherited[signature]
                    if not self._same_type(method.return_type, inherited_method.return_type):
                        raise TypecheckError(
                            f"Method '{method.name}' in class '{class_name}' overrides with different return type"
                        )

    def _check_classes(self):
        for class_def in self.program.classes:
            class_info = self.classes[class_def.name]
            self._check_constructor(class_info, class_def.constructor)
            for method in class_def.methods:
                self._check_method(class_info, method)

    def _check_constructor(self, class_info: ClassInfo, constructor: Constructor):
        param_env = {}
        initialized = set()
        for param in constructor.params:
            if isinstance(param.var_type, VoidType):
                raise TypecheckError(f"Constructor parameter '{param.var_name}' in class '{class_info.name}' cannot have type Void")
            if param.var_name in param_env:
                raise TypecheckError(f"Duplicate constructor parameter '{param.var_name}' in class '{class_info.name}'")
            param_env[param.var_name] = param.var_type
            initialized.add(param.var_name)

        parent_name = class_info.parent
        if parent_name and parent_name != "Object":
            parent_ctor_params = self.classes[parent_name].constructor.params
            super_args = constructor.super_args
            if super_args is None:
                super_args = []
            if len(super_args) != len(parent_ctor_params):
                raise TypecheckError(
                    f"Constructor for class '{class_info.name}' must call super with {len(parent_ctor_params)} argument(s)"
                )
            env = TypeEnvironment(param_env, initialized)
            for arg, param in zip(super_args, parent_ctor_params):
                arg_type = self._type_of_expression(arg, env, class_info, allow_uninitialized_fields=True)
                if not self._is_subtype(arg_type, param.var_type):
                    raise TypecheckError(
                        f"Super constructor argument type mismatch in class '{class_info.name}'"
                    )
        elif constructor.super_args not in (None, []):
            raise TypecheckError(f"Class '{class_info.name}' cannot call super because it has no explicit parent constructor")

        env = TypeEnvironment(param_env, initialized)
        for statement in constructor.body:
            env = self._check_statement(statement, env, class_info, VoidType(), in_constructor=True)

    def _check_method(self, class_info: ClassInfo, method: MethodDef):
        variables = {}
        initialized = set()
        for param in method.params:
            variables[param.var_name] = param.var_type
            initialized.add(param.var_name)
        env = TypeEnvironment(variables, initialized)
        for statement in method.body:
            env = self._check_statement(statement, env, class_info, method.return_type, in_constructor=False)
        if not isinstance(method.return_type, VoidType) and not self._guarantees_return(method.body):
            raise TypecheckError(
                f"Method '{method.name}' in class '{class_info.name}' may not return a value on every path"
            )

    def _check_entry_point(self):
        env = TypeEnvironment()
        for statement in self.program.statements:
            env = self._check_statement(statement, env, None, VoidType(), in_constructor=False)

    def _check_statement(self, statement, env: TypeEnvironment, current_class: Optional[ClassInfo], expected_return_type, in_constructor: bool):
        if isinstance(statement, VarDecStmt):
            self._validate_type_exists(statement.var_type)
            if isinstance(statement.var_type, VoidType):
                raise TypecheckError(f"Variable '{statement.var_name}' cannot have type Void")
            if statement.var_name in env.variables:
                raise TypecheckError(f"Duplicate variable declaration '{statement.var_name}'")
            if current_class and statement.var_name in self._all_fields(current_class.name):
                raise TypecheckError(f"Local variable '{statement.var_name}' shadows a field name")
            next_env = env.copy()
            next_env.variables[statement.var_name] = statement.var_type
            return next_env

        if isinstance(statement, AssignStmt):
            target_type, is_field = self._resolve_variable_type(statement.var_name, env, current_class)
            value_type = self._type_of_expression(statement.expression, env, current_class, allow_uninitialized_fields=in_constructor)
            if not self._is_subtype(value_type, target_type):
                raise TypecheckError(f"Cannot assign value of type {self._type_name(value_type)} to '{statement.var_name}'")
            next_env = env.copy()
            if not is_field:
                next_env.initialized.add(statement.var_name)
            return next_env

        if isinstance(statement, WhileStmt):
            condition_type = self._type_of_expression(statement.condition, env, current_class, allow_uninitialized_fields=in_constructor)
            if not isinstance(condition_type, BooleanType):
                raise TypecheckError("While condition must have type Boolean")
            loop_env = env.copy()
            loop_env.inside_loop = True
            for inner in statement.body:
                loop_env = self._check_statement(inner, loop_env, current_class, expected_return_type, in_constructor)
            return env.copy()

        if isinstance(statement, BreakStmt):
            if not env.inside_loop:
                raise TypecheckError("break can only be used inside a while loop")
            return env.copy()

        if isinstance(statement, IfStmt):
            condition_type = self._type_of_expression(statement.condition, env, current_class, allow_uninitialized_fields=in_constructor)
            if not isinstance(condition_type, BooleanType):
                raise TypecheckError("If condition must have type Boolean")
            then_env = self._check_statement(statement.then_stmt, env.copy(), current_class, expected_return_type, in_constructor)
            if statement.else_stmt is not None:
                else_env = self._check_statement(statement.else_stmt, env.copy(), current_class, expected_return_type, in_constructor)
                merged = env.copy()
                merged.initialized = then_env.initialized & else_env.initialized
                return merged
            return env.copy()

        if isinstance(statement, ReturnStmt):
            if isinstance(expected_return_type, VoidType):
                if statement.expression is not None:
                    actual_type = self._type_of_expression(statement.expression, env, current_class, allow_uninitialized_fields=in_constructor)
                    if not isinstance(actual_type, VoidType):
                        raise TypecheckError("Void function cannot return a non-void value")
            else:
                if statement.expression is None:
                    raise TypecheckError("Non-void function must return a value")
                actual_type = self._type_of_expression(statement.expression, env, current_class, allow_uninitialized_fields=in_constructor)
                if not self._is_subtype(actual_type, expected_return_type):
                    raise TypecheckError(
                        f"Return type mismatch: expected {self._type_name(expected_return_type)} but got {self._type_name(actual_type)}"
                    )
            return env.copy()

        if isinstance(statement, ExpStmt):
            self._type_of_expression(statement.expression, env, current_class, allow_uninitialized_fields=in_constructor)
            return env.copy()

        raise TypecheckError(f"Unsupported statement: {statement}")

    def _type_of_expression(self, expression, env: TypeEnvironment, current_class: Optional[ClassInfo], allow_uninitialized_fields: bool = False):
        if isinstance(expression, IntLiteralExp):
            return IntType()
        if isinstance(expression, StringLiteralExp):
            return ClassType("String")
        if isinstance(expression, TrueExp) or isinstance(expression, FalseExp):
            return BooleanType()
        if isinstance(expression, ThisExp):
            if current_class is None:
                raise TypecheckError("'this' can only be used inside a class method or constructor")
            return ClassType(current_class.name)
        if isinstance(expression, VarExp):
            var_type, is_field = self._resolve_variable_type(expression.name, env, current_class)
            if not is_field and expression.name not in env.initialized:
                raise TypecheckError(f"Variable '{expression.name}' may be used before it is initialized")
            if is_field and allow_uninitialized_fields:
                return var_type
            return var_type
        if isinstance(expression, PrintlnExp):
            self._type_of_expression(expression.expression, env, current_class, allow_uninitialized_fields)
            return VoidType()
        if isinstance(expression, BinOpExp):
            left_type = self._type_of_expression(expression.left, env, current_class, allow_uninitialized_fields)
            right_type = self._type_of_expression(expression.right, env, current_class, allow_uninitialized_fields)
            if expression.op in {"+", "-", "*", "/"}:
                if not isinstance(left_type, IntType) or not isinstance(right_type, IntType):
                    raise TypecheckError(f"Operator '{expression.op}' requires Int operands")
                return IntType()
            if expression.op == "<":
                if not isinstance(left_type, IntType) or not isinstance(right_type, IntType):
                    raise TypecheckError("Operator '<' requires Int operands")
                return BooleanType()
            if expression.op == "==":
                if not self._same_type(left_type, right_type) and not self._is_subtype(left_type, right_type) and not self._is_subtype(right_type, left_type):
                    raise TypecheckError("Operator '==' requires compatible operand types")
                return BooleanType()
            raise TypecheckError(f"Unknown operator '{expression.op}'")
        if isinstance(expression, NewExp):
            if expression.class_name not in self.classes:
                raise TypecheckError(f"Cannot instantiate unknown class '{expression.class_name}'")
            if expression.class_name == "String":
                raise TypecheckError("Cannot instantiate built-in String with new")
            constructor = self.classes[expression.class_name].constructor
            if len(expression.args) != len(constructor.params):
                raise TypecheckError(
                    f"Constructor for class '{expression.class_name}' expects {len(constructor.params)} argument(s)"
                )
            for arg, param in zip(expression.args, constructor.params):
                arg_type = self._type_of_expression(arg, env, current_class, allow_uninitialized_fields)
                if not self._is_subtype(arg_type, param.var_type):
                    raise TypecheckError(f"Constructor argument type mismatch for class '{expression.class_name}'")
            return ClassType(expression.class_name)
        if isinstance(expression, CallExp):
            obj_type = self._type_of_expression(expression.obj, env, current_class, allow_uninitialized_fields)
            if not isinstance(obj_type, ClassType):
                raise TypecheckError("Method calls require an object receiver")
            if obj_type.name == "String":
                raise TypecheckError("Built-in String does not support methods")
            method = self._resolve_method(obj_type.name, expression.method_name, expression.args, env, current_class, allow_uninitialized_fields)
            return method.return_type
        raise TypecheckError(f"Unsupported expression: {expression}")

    def _resolve_method(self, class_name: str, method_name: str, args, env, current_class, allow_uninitialized_fields):
        arg_types = [self._type_of_expression(arg, env, current_class, allow_uninitialized_fields) for arg in args]
        candidates = []
        for method in self._all_methods(class_name).values():
            if method.name != method_name or len(method.params) != len(arg_types):
                continue
            if all(self._is_subtype(arg_type, param_type) for arg_type, param_type in zip(arg_types, method.params)):
                candidates.append(method)
        if not candidates:
            raise TypecheckError(f"No matching overload for method '{method_name}' on class '{class_name}'")
        best = []
        for candidate in candidates:
            dominated = False
            for other in candidates:
                if candidate is other:
                    continue
                if self._is_more_specific(other.params, candidate.params):
                    dominated = True
                    break
            if not dominated:
                best.append(candidate)
        if len(best) != 1:
            raise TypecheckError(f"Ambiguous overload for method '{method_name}' on class '{class_name}'")
        return best[0]

    def _is_more_specific(self, left_params, right_params):
        strictly_better = False
        for left_type, right_type in zip(left_params, right_params):
            if not self._is_subtype(left_type, right_type):
                return False
            if not self._same_type(left_type, right_type):
                strictly_better = True
        return strictly_better

    def _resolve_variable_type(self, name: str, env: TypeEnvironment, current_class: Optional[ClassInfo]):
        if name in env.variables:
            return env.variables[name], False
        if current_class is not None:
            fields = self._all_fields(current_class.name)
            if name in fields:
                return fields[name], True
        raise TypecheckError(f"Unknown variable '{name}'")

    def _all_fields(self, class_name: str):
        class_info = self.classes[class_name]
        fields = {}
        if class_info.parent is not None and class_name != "Object":
            fields.update(self._all_fields(class_info.parent))
        fields.update(class_info.fields)
        return fields

    def _all_methods(self, class_name: str):
        class_info = self.classes[class_name]
        methods = {}
        if class_info.parent is not None and class_name != "Object":
            methods.update(self._all_methods(class_info.parent))
        methods.update(class_info.methods)
        return methods

    def _validate_type_exists(self, type_node):
        if isinstance(type_node, ClassType) and type_node.name not in self.classes and type_node.name not in [class_def.name for class_def in self.program.classes]:
            raise TypecheckError(f"Unknown type '{type_node.name}'")

    def _is_subtype(self, left, right):
        if self._same_type(left, right):
            return True
        if isinstance(left, ClassType) and isinstance(right, ClassType):
            current = left.name
            while current in self.classes:
                parent = self.classes[current].parent
                if parent == right.name:
                    return True
                current = parent
                if current is None:
                    break
        return False

    def _same_type(self, left, right):
        return type_key(left) == type_key(right)

    def _type_name(self, type_node):
        if isinstance(type_node, IntType):
            return "Int"
        if isinstance(type_node, BooleanType):
            return "Boolean"
        if isinstance(type_node, VoidType):
            return "Void"
        if isinstance(type_node, ClassType):
            return type_node.name
        return str(type_node)

    def _make_slot_name(self, method_name: str, params: List[object]):
        if not params:
            return method_name + "__void"
        pieces = [method_name]
        for param in params:
            if isinstance(param, IntType):
                pieces.append("Int")
            elif isinstance(param, BooleanType):
                pieces.append("Boolean")
            elif isinstance(param, VoidType):
                pieces.append("Void")
            elif isinstance(param, ClassType):
                pieces.append(param.name)
        return "__".join(pieces)

    def _guarantees_return(self, statements):
        for statement in statements:
            if isinstance(statement, ReturnStmt):
                return True
            if isinstance(statement, IfStmt):
                if statement.else_stmt is not None and self._guarantees_return([statement.then_stmt]) and self._guarantees_return([statement.else_stmt]):
                    return True
            if isinstance(statement, WhileStmt):
                continue
        return False


def type_key(type_node):
    if isinstance(type_node, IntType):
        return ("Int", None)
    if isinstance(type_node, BooleanType):
        return ("Boolean", None)
    if isinstance(type_node, VoidType):
        return ("Void", None)
    if isinstance(type_node, ClassType):
        return ("Class", type_node.name)
    raise TypecheckError(f"Unknown type node: {type_node}")


def typecheck(source: str) -> TypedProgram:
    return TypeChecker(parse(source)).check()
