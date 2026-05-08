from parser import (
    AssignStmt,
    BinOpExp,
    BooleanType,
    BreakStmt,
    CallExp,
    ClassType,
    ExpStmt,
    FalseExp,
    IfStmt,
    IntLiteralExp,
    IntType,
    NewExp,
    PrintlnExp,
    ReturnStmt,
    StringLiteralExp,
    ThisExp,
    TrueExp,
    VarDecStmt,
    VarExp,
    VoidType,
    WhileStmt,
)
from typechecker import TypedProgram, type_key, typecheck


class CodegenError(Exception):
    pass


class CodeGenerator:
    def __init__(self, typed_program: TypedProgram):
        self.typed_program = typed_program
        self.program = typed_program.program
        self.classes = typed_program.classes
        self.class_defs = {class_def.name: class_def for class_def in self.program.classes}
        self.lines = []
        self.indent_level = 0
        self.current_class = None
        self.current_locals = {}
        self.current_self_name = "self"

    def generate(self):
        self._emit_prelude()
        self._emit_forward_declarations()
        self._emit_struct_definitions()
        self._emit_function_prototypes()
        self._emit_vtables()
        self._emit_constructors()
        self._emit_methods()
        self._emit_main()
        return "\n".join(self.lines) + "\n"

    def _emit(self, line=""):
        self.lines.append("    " * self.indent_level + line)

    def _emit_prelude(self):
        self._emit("#include <stdbool.h>")
        self._emit("#include <stdio.h>")
        self._emit("#include <stdlib.h>")
        self._emit("#include <string.h>")
        self._emit("")
        self._emit("typedef struct Object Object;")
        self._emit("typedef struct Object_vtable Object_vtable;")
        self._emit("struct Object { Object_vtable* vtable; };")
        self._emit("struct Object_vtable { int _unused; };")
        self._emit("static Object_vtable Object_vtable_instance = {0};")
        self._emit("")
        self._emit("static void ClassC_print_bool(bool value) {")
        self.indent_level += 1
        self._emit('printf("%s\\n", value ? "true" : "false");')
        self.indent_level -= 1
        self._emit("}")
        self._emit("")
        self._emit("static void ClassC_print_string(const char* value) {")
        self.indent_level += 1
        self._emit('printf("%s\\n", value);')
        self.indent_level -= 1
        self._emit("}")
        self._emit("")
        self._emit("static void ClassC_print_int(int value) {")
        self.indent_level += 1
        self._emit('printf("%d\\n", value);')
        self.indent_level -= 1
        self._emit("}")
        self._emit("")
        self._emit("static void ClassC_print_object(void* value) {")
        self.indent_level += 1
        self._emit('printf("%p\\n", value);')
        self.indent_level -= 1
        self._emit("}")
        self._emit("")

    def _emit_forward_declarations(self):
        for class_def in self.program.classes:
            self._emit(f"typedef struct {class_def.name} {class_def.name};")
            self._emit(f"typedef struct {class_def.name}_vtable {class_def.name}_vtable;")
        if self.program.classes:
            self._emit("")

    def _emit_struct_definitions(self):
        for class_def in self.program.classes:
            class_info = self.classes[class_def.name]
            parent = class_info.parent or "Object"

            self._emit(f"struct {class_def.name} {{")
            self.indent_level += 1
            self._emit(f"{parent} super;")
            for field_name in class_info.field_order:
                self._emit(f"{self._c_type(class_info.fields[field_name])} {field_name};")
            self.indent_level -= 1
            self._emit("};")
            self._emit("")

            self._emit(f"struct {class_def.name}_vtable {{")
            self.indent_level += 1
            self._emit(f"{parent}_vtable super;" if parent != "Object" else "Object_vtable super;")
            for method in self._introduced_methods(class_def.name):
                slot_owner = self._slot_owner(class_def.name, method.signature)
                self._emit(
                    f"{self._c_type(method.return_type)} (*{method.slot_name})({slot_owner}* self{self._param_list_from_types(method.params)});"
                )
            self.indent_level -= 1
            self._emit("};")
            self._emit("")

    def _emit_function_prototypes(self):
        for class_def in self.program.classes:
            class_name = class_def.name
            ctor = self.classes[class_name].constructor
            self._emit(f"static void {class_name}_init({class_name}* self{self._param_list(ctor.params)});")
            self._emit(f"static {class_name}* new_{class_name}({self._param_decl_list(ctor.params)});")
            for method_def in class_def.methods:
                info = self.classes[class_name].methods[self._signature_for_methoddef(class_name, method_def)]
                slot_owner = self._slot_owner(class_name, info.signature)
                self._emit(
                    f"static {self._c_type(info.return_type)} {class_name}_{info.slot_name}({slot_owner}* self{self._param_list(method_def.params)});"
                )
            self._emit("")

    def _emit_vtables(self):
        for class_def in self.program.classes:
            class_name = class_def.name
            self._emit(f"static {class_name}_vtable {class_name}_vtable_instance = {{")
            self.indent_level += 1
            parent = self.classes[class_name].parent or "Object"
            self._emit(f".super = {self._build_prefix_initializer(parent, class_name)},")
            for method in self._introduced_methods(class_name):
                impl_class = self._implementation_class(class_name, method.signature)
                self._emit(f".{method.slot_name} = {impl_class}_{method.slot_name},")
            self.indent_level -= 1
            self._emit("};")
            self._emit("")

    def _build_prefix_initializer(self, slot_class, concrete_class):
        if slot_class == "Object":
            return "{0}"
        parts = [f".super = {self._build_prefix_initializer(self.classes[slot_class].parent or 'Object', concrete_class)}"]
        for method in self._introduced_methods(slot_class):
            impl_class = self._implementation_class(concrete_class, method.signature)
            parts.append(f".{method.slot_name} = {impl_class}_{method.slot_name}")
        return "{" + ", ".join(parts) + "}"

    def _emit_constructors(self):
        for class_def in self.program.classes:
            class_name = class_def.name
            class_info = self.classes[class_name]
            ctor = class_info.constructor

            self._emit(f"static void {class_name}_init({class_name}* self{self._param_list(ctor.params)}) {{")
            self.indent_level += 1
            self.current_class = class_name
            self.current_locals = {param.var_name: param.var_type for param in ctor.params}
            self.current_self_name = "self"
            parent = class_info.parent or "Object"
            if parent != "Object":
                args = ", ".join(self._compile_expression(arg) for arg in (ctor.super_args or []))
                if args:
                    self._emit(f"{parent}_init(({parent}*) self, {args});")
                else:
                    self._emit(f"{parent}_init(({parent}*) self);")
            else:
                self._emit("self->super.vtable = &Object_vtable_instance;")
            self._emit(f"{self._object_vtable_lvalue(class_name, 'self')} = (Object_vtable*) &{class_name}_vtable_instance;")
            for statement in ctor.body:
                self._emit_statement(statement)
            self.indent_level -= 1
            self._emit("}")
            self._emit("")

            self._emit(f"static {class_name}* new_{class_name}({self._param_decl_list(ctor.params)}) {{")
            self.indent_level += 1
            self._emit(f"{class_name}* self = ({class_name}*) malloc(sizeof({class_name}));")
            self._emit("if (self == NULL) {")
            self.indent_level += 1
            self._emit('fprintf(stderr, "Out of memory\\n");')
            self._emit("exit(1);")
            self.indent_level -= 1
            self._emit("}")
            args = ", ".join(param.var_name for param in ctor.params)
            self._emit(f"{class_name}_init(self{', ' + args if args else ''});")
            self._emit("return self;")
            self.indent_level -= 1
            self._emit("}")
            self._emit("")

    def _emit_methods(self):
        for class_def in self.program.classes:
            class_name = class_def.name
            methods_by_sig = {self._signature_for_methoddef(class_name, method): method for method in class_def.methods}
            for signature, info in self.classes[class_name].methods.items():
                method_def = methods_by_sig[signature]
                slot_owner = self._slot_owner(class_name, signature)
                self._emit(
                    f"static {self._c_type(info.return_type)} {class_name}_{info.slot_name}({slot_owner}* self{self._param_list(method_def.params)}) {{"
                )
                self.indent_level += 1
                self.current_class = class_name
                self.current_locals = {param.var_name: param.var_type for param in method_def.params}
                self.current_self_name = "self"
                if slot_owner != class_name:
                    self.current_self_name = "self_this"
                    self._emit(f"{class_name}* self_this = ({class_name}*) self;")
                for statement in method_def.body:
                    self._emit_statement(statement)
                if isinstance(method_def.return_type, VoidType) and (not method_def.body or not isinstance(method_def.body[-1], ReturnStmt)):
                    self._emit("return;")
                self.indent_level -= 1
                self._emit("}")
                self._emit("")

    def _emit_main(self):
        self._emit("int main(void) {")
        self.indent_level += 1
        self.current_class = None
        self.current_locals = {}
        self.current_self_name = "self"
        for statement in self.program.statements:
            self._emit_statement(statement)
        self._emit("return 0;")
        self.indent_level -= 1
        self._emit("}")

    def _emit_statement(self, statement):
        if isinstance(statement, VarDecStmt):
            self.current_locals[statement.var_name] = statement.var_type
            self._emit(f"{self._c_type(statement.var_type)} {statement.var_name};")
            return
        if isinstance(statement, AssignStmt):
            target_type = self.current_locals.get(statement.var_name) if statement.var_name in self.current_locals else self._lookup_field_type(self.current_class, statement.var_name)
            expr_code = self._compile_expression(statement.expression)
            expr_type = self._infer_expression_type(statement.expression)
            expr_code = self._cast_if_needed(expr_code, expr_type, target_type)
            self._emit(f"{self._compile_lvalue(statement.var_name)} = {expr_code};")
            return
        if isinstance(statement, ExpStmt):
            self._emit(f"{self._compile_expression(statement.expression)};")
            return
        if isinstance(statement, ReturnStmt):
            if statement.expression is None:
                self._emit("return;")
            else:
                expr_code = self._compile_expression(statement.expression)
                expr_type = self._infer_expression_type(statement.expression)
                if isinstance(expr_type, VoidType):
                    self._emit(f"{expr_code};")
                    self._emit("return;")
                else:
                    self._emit(f"return {expr_code};")
            return
        if isinstance(statement, IfStmt):
            self._emit(f"if ({self._compile_expression(statement.condition)}) {{")
            self.indent_level += 1
            self._emit_statement(statement.then_stmt)
            self.indent_level -= 1
            if statement.else_stmt is not None:
                self._emit("} else {")
                self.indent_level += 1
                self._emit_statement(statement.else_stmt)
                self.indent_level -= 1
            self._emit("}")
            return
        if isinstance(statement, WhileStmt):
            self._emit(f"while ({self._compile_expression(statement.condition)}) {{")
            self.indent_level += 1
            for inner in statement.body:
                self._emit_statement(inner)
            self.indent_level -= 1
            self._emit("}")
            return
        if isinstance(statement, BreakStmt):
            self._emit("break;")
            return
        raise CodegenError(f"Unsupported statement: {statement}")

    def _compile_expression(self, expression):
        if isinstance(expression, IntLiteralExp):
            return str(expression.value)
        if isinstance(expression, StringLiteralExp):
            escaped = expression.value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
            return f'"{escaped}"'
        if isinstance(expression, TrueExp):
            return "true"
        if isinstance(expression, FalseExp):
            return "false"
        if isinstance(expression, ThisExp):
            return self.current_self_name
        if isinstance(expression, VarExp):
            return self._compile_lvalue(expression.name)
        if isinstance(expression, BinOpExp):
            return f"({self._compile_expression(expression.left)} {expression.op} {self._compile_expression(expression.right)})"
        if isinstance(expression, PrintlnExp):
            inner_type = self._infer_expression_type(expression.expression)
            code = self._compile_expression(expression.expression)
            if isinstance(inner_type, IntType):
                return f"(ClassC_print_int({code}), 0)"
            if isinstance(inner_type, BooleanType):
                return f"(ClassC_print_bool({code}), 0)"
            if isinstance(inner_type, ClassType) and inner_type.name == "String":
                return f"(ClassC_print_string({code}), 0)"
            return f"(ClassC_print_object({code}), 0)"
        if isinstance(expression, NewExp):
            ctor_params = self.classes[expression.class_name].constructor.params
            compiled_args = []
            for arg, param in zip(expression.args, ctor_params):
                arg_code = self._compile_expression(arg)
                arg_type = self._infer_expression_type(arg)
                compiled_args.append(self._cast_if_needed(arg_code, arg_type, param.var_type))
            args = ", ".join(compiled_args)
            return f"new_{expression.class_name}({args})"
        if isinstance(expression, CallExp):
            obj_type = self._infer_expression_type(expression.obj)
            method = self._resolve_call_method(obj_type.name, expression.method_name, expression.args)
            slot_owner = self._slot_owner(obj_type.name, method.signature)
            receiver = self._compile_expression(expression.obj)
            vtable_expr = self._vtable_expr(receiver, slot_owner)
            compiled_args = []
            for arg, param_type in zip(expression.args, method.params):
                arg_code = self._compile_expression(arg)
                arg_type = self._infer_expression_type(arg)
                compiled_args.append(self._cast_if_needed(arg_code, arg_type, param_type))
            args = ", ".join(compiled_args)
            prefix = f"(({slot_owner}_vtable*) {vtable_expr})->{method.slot_name}(({slot_owner}*) ({receiver})"
            if args:
                return prefix + f", {args})"
            return prefix + ")"
        raise CodegenError(f"Unsupported expression: {expression}")

    def _vtable_expr(self, receiver, slot_owner):
        if slot_owner == "Object":
            return f"((Object*) ({receiver}))->vtable"
        return self._object_vtable_lvalue(slot_owner, f"({receiver})")

    def _object_vtable_lvalue(self, class_name, base_expr):
        parent = self.classes[class_name].parent or "Object"
        if parent == "Object":
            return f"(({class_name}*) {base_expr})->super.vtable"
        return self._object_vtable_lvalue(parent, f"(({parent}*) {base_expr})")

    def _cast_if_needed(self, code, from_type, to_type):
        if type_key(from_type) == type_key(to_type):
            return code
        if isinstance(from_type, ClassType) and isinstance(to_type, ClassType) and to_type.name != "String":
            return f"(({to_type.name}*) ({code}))"
        return code

    def _compile_lvalue(self, name):
        if name in self.current_locals:
            return name
        if self.current_class is None:
            raise CodegenError(f"Unknown variable '{name}'")
        return self._field_access_path(self.current_class, name, self.current_self_name)

    def _field_access_path(self, class_name, field_name, base_expr):
        class_info = self.classes[class_name]
        if field_name in class_info.fields:
            return f"{base_expr}->{field_name}"
        parent = class_info.parent
        if parent is None or parent == "Object":
            raise CodegenError(f"Unknown field '{field_name}'")
        return self._field_access_path(parent, field_name, f"(({parent}*) {base_expr})")

    def _infer_expression_type(self, expression):
        if isinstance(expression, IntLiteralExp):
            return IntType()
        if isinstance(expression, StringLiteralExp):
            return ClassType("String")
        if isinstance(expression, TrueExp) or isinstance(expression, FalseExp):
            return BooleanType()
        if isinstance(expression, ThisExp):
            return ClassType(self.current_class)
        if isinstance(expression, VarExp):
            if expression.name in self.current_locals:
                return self.current_locals[expression.name]
            return self._lookup_field_type(self.current_class, expression.name)
        if isinstance(expression, PrintlnExp):
            return VoidType()
        if isinstance(expression, BinOpExp):
            return BooleanType() if expression.op in {"<", "=="} else IntType()
        if isinstance(expression, NewExp):
            return ClassType(expression.class_name)
        if isinstance(expression, CallExp):
            obj_type = self._infer_expression_type(expression.obj)
            return self._resolve_call_method(obj_type.name, expression.method_name, expression.args).return_type
        raise CodegenError(f"Cannot infer type for {expression}")

    def _lookup_field_type(self, class_name, field_name):
        class_info = self.classes[class_name]
        if field_name in class_info.fields:
            return class_info.fields[field_name]
        parent = class_info.parent
        if parent is None or parent == "Object":
            raise CodegenError(f"Unknown field '{field_name}'")
        return self._lookup_field_type(parent, field_name)

    def _resolve_call_method(self, class_name, method_name, args):
        arg_types = [self._infer_expression_type(arg) for arg in args]
        candidates = []
        for method in self._all_methods(class_name):
            if method.name != method_name or len(method.params) != len(arg_types):
                continue
            if all(self._is_subtype(arg_type, param_type) for arg_type, param_type in zip(arg_types, method.params)):
                candidates.append(method)
        if not candidates:
            raise CodegenError(f"No overload found for method '{method_name}'")
        best = []
        for candidate in candidates:
            dominated = False
            for other in candidates:
                if candidate is other:
                    continue
                if self._more_specific(other.params, candidate.params):
                    dominated = True
                    break
            if not dominated:
                best.append(candidate)
        if len(best) != 1:
            raise CodegenError(f"Ambiguous overload for method '{method_name}'")
        return best[0]

    def _all_methods(self, class_name):
        class_info = self.classes[class_name]
        methods = []
        parent = class_info.parent
        if parent is not None and parent != "Object":
            methods.extend(self._all_methods(parent))
        overridden = set(class_info.methods.keys())
        methods = [method for method in methods if method.signature not in overridden]
        methods.extend(class_info.methods[signature] for signature in class_info.method_order)
        return methods

    def _introduced_methods(self, class_name):
        class_info = self.classes[class_name]
        parent_methods = set()
        parent = class_info.parent
        if parent is not None and parent != "Object":
            parent_methods = {method.signature for method in self._all_methods(parent)}
        return [class_info.methods[signature] for signature in class_info.method_order if signature not in parent_methods]

    def _implementation_class(self, concrete_class, signature):
        current = concrete_class
        while current != "Object":
            if signature in self.classes[current].methods:
                return current
            current = self.classes[current].parent
        raise CodegenError("Missing implementation class")

    def _slot_owner(self, class_name, signature):
        current = class_name
        owner = class_name
        while current != "Object":
            parent = self.classes[current].parent
            if parent is None or parent == "Object":
                return owner
            if signature in self.classes[parent].methods:
                owner = parent
                current = parent
            else:
                return owner
        return owner

    def _signature_for_methoddef(self, class_name, method_def):
        return next(signature for signature, info in self.classes[class_name].methods.items() if info.name == method_def.name and len(info.params) == len(method_def.params) and all(type_key(param.var_type) == type_key(info_param) for param, info_param in zip(method_def.params, info.params)))

    def _c_type(self, type_node):
        if isinstance(type_node, IntType):
            return "int"
        if isinstance(type_node, BooleanType):
            return "bool"
        if isinstance(type_node, VoidType):
            return "void"
        if isinstance(type_node, ClassType):
            return "char*" if type_node.name == "String" else f"{type_node.name}*"
        raise CodegenError(f"Unknown type node: {type_node}")

    def _param_list(self, params):
        return "" if not params else ", " + ", ".join(f"{self._c_type(param.var_type)} {param.var_name}" for param in params)

    def _param_decl_list(self, params):
        return "void" if not params else ", ".join(f"{self._c_type(param.var_type)} {param.var_name}" for param in params)

    def _param_list_from_types(self, params):
        return "" if not params else ", " + ", ".join(f"{self._c_type(param)} arg{i}" for i, param in enumerate(params))

    def _is_subtype(self, left, right):
        if type_key(left) == type_key(right):
            return True
        if isinstance(left, ClassType) and isinstance(right, ClassType):
            current = left.name
            while current in self.classes:
                current = self.classes[current].parent
                if current == right.name:
                    return True
                if current is None:
                    break
        return False

    def _more_specific(self, left_params, right_params):
        strictly = False
        for left, right in zip(left_params, right_params):
            if not self._is_subtype(left, right):
                return False
            if type_key(left) != type_key(right):
                strictly = True
        return strictly


def generate_c(source: str) -> str:
    return CodeGenerator(typecheck(source)).generate()
