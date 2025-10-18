from llvmlite import ir
import os
from AST import Node, NodeType, Program, Expression
from AST import ExpressionStatement, LetStatement, FunctionStatement, ReturnStatement, BlockStatement, AssignStatement, IfStatement
from AST import WhileStatement, ContinueStatement, BreakStatement, ForStatement
from AST import InfixExpression, CallExpression
from AST import IntegerLiteral, FloatLiteral, IdentifierLiteral, BooleanLiteral, StringLiteral
from AST import FunctionParameter , ImportStatement

from Environment import Environment

from Lexer import Lexer 
from Parser import Parser
class Compiler:
    def __init__(self) -> None:
        self.type_map: dict[str, ir.Type] = {
            'int': ir.IntType(32),
            'float': ir.FloatType(),
            'bool': ir.IntType(1),

            
            'void': ir.VoidType(),
            'str': ir.PointerType(ir.IntType(8))
        }

    
        self.module: ir.Module = ir.Module('main')
        self.target_triple: str = "x86_64-pc-windows-msvc"

        
        self.builder: ir.IRBuilder = ir.IRBuilder()

        
        self.counter: int = 0

        
        self.env: Environment = Environment()

    
        self.errors: list[str] = []

        
        self.__initialize_builtins()

        
        self.breakpoints: list[ir.Block] = []
        self.continues: list[ir.Block] = []

        self.global_parsed_pallets : dict[str,Program] = {}

    def __initialize_builtins(self) -> None:
        def __init_print() -> ir.Function:
            fnty: ir.FunctionType = ir.FunctionType(
                self.type_map['int'],
                [ir.IntType(8).as_pointer()],
                var_arg=True
            )
            return ir.Function(self.module, fnty, 'printf')
        
        def __init_booleans() -> tuple[ir.GlobalVariable, ir.GlobalVariable]:
            bool_type: ir.Type = self.type_map['bool']

            true_var = ir.GlobalVariable(self.module, bool_type, 'true')
            true_var.initializer = ir.Constant(bool_type, 1)
            true_var.global_constant = True

            false_var = ir.GlobalVariable(self.module, bool_type, 'false')
            false_var.initializer = ir.Constant(bool_type, 0)
            false_var.global_constant = True

            return true_var, false_var
        
        self.env.define('printf', __init_print(), ir.IntType(32))
        
        true_var, false_var = __init_booleans()
        self.env.define('true', true_var, true_var.type)
        self.env.define('false', false_var, false_var.type)

    def __increment_counter(self) -> int:
        self.counter += 1
        return self.counter

    def compile(self, node: Node) -> None:
        
        match node.type():
            case NodeType.Program:
                self.__visit_program(node)

            # Statements
            case NodeType.ExpressionStatement:
                self.__visit_expression_statement(node)
            case NodeType.LetStatement:
                self.__visit_let_statement(node)
            case NodeType.FunctionStatement:
                self.__visit_function_statement(node)
            case NodeType.BlockStatement:
                self.__visit_block_statement(node)
            case NodeType.ReturnStatement:
                self.__visit_return_statement(node)
            case NodeType.AssignStatement:
                self.__visit_assign_statement(node)
            case NodeType.IfStatement:
                self.__visit_if_statement(node)
            case NodeType.WhileStatement:
                self.__visit_while_statement(node)
            case NodeType.BreakStatement:
                self.__visit_break_statement(node)
            case NodeType.ContinueStatement:
                self.__visit_continue_statement(node)
            case NodeType.ForStatement:
                self.__visit_for_statement(node)
            case NodeType.ImportStatement:
                self.__visit_import_statement(node)

            # Expressions
            case NodeType.InfixExpression:
                self.__visit_infix_expression(node)
            case NodeType.CallExpression:
                self.__visit_call_expression(node)

    
    def __visit_program(self, node: Program) -> None:
        
        for stmt in node.statements:
            self.compile(stmt)

 
    def __visit_expression_statement(self, node: ExpressionStatement) -> None:
        self.compile(node.expr)

    def __visit_let_statement(self, node: LetStatement) -> None:
        name: str = node.name.value
        value: Expression = node.value
        value_type: str  = node.value_type 

        value, Type = self.__resolve_value(node=value)

        if self.env.lookup(name) is None:
           
            ptr = self.builder.alloca(Type)

            
            self.builder.store(value, ptr)

            
            self.env.define(name, ptr, Type)
        else:
            ptr, _ = self.env.lookup(name)
            self.builder.store(value, ptr)

    def __visit_block_statement(self, node: BlockStatement) -> None:
        for stmt in node.statements:
            self.compile(stmt)
    
    def __visit_return_statement(self, node: ReturnStatement) -> None:
        value: Expression = node.return_value
        value, Type = self.__resolve_value(value)

        self.builder.ret(value)

    def __visit_function_statement(self, node: FunctionStatement) -> None:
        name: str = node.name.value
        body: BlockStatement = node.body
        params: list[FunctionParameter] = node.parameters

        
        param_names: list[str] = [p.name for p in params]

        
        param_types: list[ir.Type] = [self.type_map[p.value_type] for p in params]

        return_type: ir.Type = self.type_map[node.return_type]

        fnty: ir.FunctionType = ir.FunctionType(return_type, param_types)
        func: ir.Function = ir.Function(self.module, fnty, name=name)

        block: ir.Block = func.append_basic_block(f'{name}_entry')

        previous_builder = self.builder

        self.builder = ir.IRBuilder(block)

       
        params_ptr = []
        for i, typ in enumerate(param_types):
            ptr = self.builder.alloca(typ)
            self.builder.store(func.args[i], ptr)
            params_ptr.append(ptr)

        
        previous_env = self.env
        self.env = Environment(parent=previous_env)
        for i, x in enumerate(zip(param_types, param_names)):
            typ = param_types[i]
            ptr = params_ptr[i]

            self.env.define(x[1], ptr, typ)

        self.env.define(name, func, return_type)

        self.compile(body)

        self.env = previous_env
        self.env.define(name, func, return_type)

        self.builder = previous_builder

    def __visit_assign_statement(self, node: AssignStatement) -> None:
        name: str = node.ident.value
        value: Expression = node.right_value

        value, Type = self.__resolve_value(value)

        if self.env.lookup(name) is None:
            self.errors.append(f"COMPILE ERROR: Identifier {name} has not been declared before it was re-assigned.")
        else:
            ptr, _ = self.env.lookup(name)
            self.builder.store(value, ptr)

    def __visit_if_statement(self, node: IfStatement) -> None:
        condition = node.condition
        consequenece = node.consequence
        alternative = node.alternative

        test, Type = self.__resolve_value(condition)

      
        if alternative is None:
            with self.builder.if_then(test):
                self.compile(consequenece)
        else:
            with self.builder.if_else(test) as (true, otherwise):
                
                with true:
                    self.compile(consequenece)
                
                with otherwise:
                    self.compile(alternative)

    def __visit_while_statement(self, node: WhileStatement) -> None:
        condition: Expression = node.condition
        body: BlockStatement = node.body

        test, _ = self.__resolve_value(condition)

        while_loop_entry = self.builder.append_basic_block(f"while_loop_entry_{self.__increment_counter()}")
        while_loop_otherwise = self.builder.append_basic_block(f"while_loop_otherwise_{self.counter}")

        # Set up break and continue targets
        self.breakpoints.append(while_loop_otherwise)
        self.continues.append(while_loop_entry)

        self.builder.cbranch(test, while_loop_entry, while_loop_otherwise)
        self.builder.position_at_start(while_loop_entry)

        self.compile(body)

        test, _ = self.__resolve_value(condition)

        self.builder.cbranch(test, while_loop_entry, while_loop_otherwise)
        self.builder.position_at_start(while_loop_otherwise)

        # Clean up break and continue targets
        self.breakpoints.pop()
        self.continues.pop()

    def __visit_break_statement(self, node: BreakStatement) -> None:
        self.builder.branch(self.breakpoints[-1])

    def __visit_continue_statement(self, node: ContinueStatement) -> None:
        self.builder.branch(self.continues[-1])

    def __visit_for_statement(self, node: ForStatement) -> None:
        var_declaration: LetStatement = node.var_declaration
        condition: Expression = node.condition
        action: AssignStatement = node.action
        body: BlockStatement = node.body

        
        previous_env = self.env
        self.env = Environment(parent=previous_env)

        
        self.compile(var_declaration)

        for_loop_entry = self.builder.append_basic_block(f"for_loop_entry_{self.__increment_counter()}")
        for_loop_otherwise = self.builder.append_basic_block(f"for_loop_otherwise_{self.counter}")

        self.breakpoints.append(for_loop_otherwise)
        self.continues.append(for_loop_entry)

        self.builder.branch(for_loop_entry)
        self.builder.position_at_start(for_loop_entry)

        self.compile(body)

        self.compile(action)

        test, _ = self.__resolve_value(condition)

        self.builder.cbranch(test, for_loop_entry, for_loop_otherwise)

        self.builder.position_at_start(for_loop_otherwise)

        self.breakpoints.pop()
        self.continues.pop()

    def __visit_import_statement(self,node:ImportStatement) -> None:
        file_path:str = node.file_path

        if self.global_parsed_pallets.get(file_path) is not None:
            print(f"[Lime Warning]: {file_path} is already imported globally")
            return
        
        # Resolve imports relative to project root or current file
        normalized_path = file_path.replace('/', os.sep).replace('\\', os.sep)
        candidate_paths = [
            os.path.abspath(normalized_path),
            os.path.abspath(os.path.join('tests', normalized_path)),
        ]
        pallet_path = None
        for p in candidate_paths:
            if os.path.exists(p):
                pallet_path = p
                break
        if pallet_path is None:
            print(f"Error with imported pallet: {file_path} (file not found)")
            exit(1)

        with open(pallet_path,"r") as f:
            pallet_code:str = f.read()

        l:Lexer = Lexer(source = pallet_code)
        p:Parser = Parser(lexer=l)
        program:Program = p.parse_program()
        if len(p.errors )> 0:
            print(f"Error with imported pallet: {file_path}")
            for x in p.errors:
                print(x)
            exit(1)
        self.compile(node=program)

        self.global_parsed_pallets[file_path] = program 



    def __visit_infix_expression(self, node: InfixExpression) -> None:
        operator: str = node.operator
        left_value, left_type = self.__resolve_value(node.left_node)
        right_value, right_type = self.__resolve_value(node.right_node)

        value = None
        Type = None
        if isinstance(right_type, ir.IntType) and isinstance(left_type, ir.IntType):
            Type = self.type_map['int']
            match operator:
                case '+':
                    value = self.builder.add(left_value, right_value)
                case '-':
                    value = self.builder.sub(left_value, right_value)
                case '*':
                    value = self.builder.mul(left_value, right_value)
                case '/':
                    value = self.builder.sdiv(left_value, right_value)
                case '%':
                    value = self.builder.srem(left_value, right_value)
                case '^':
                    pass
                case '<':
                    value = self.builder.icmp_signed('<', left_value, right_value)
                    Type = ir.IntType(1)
                case '<=':
                    value = self.builder.icmp_signed('<=', left_value, right_value)
                    Type = ir.IntType(1)
                case '>':
                    value = self.builder.icmp_signed('>', left_value, right_value)
                    Type = ir.IntType(1)
                case '>=':
                    value = self.builder.icmp_signed('>=', left_value, right_value)
                    Type = ir.IntType(1)
                case '==':
                    value = self.builder.icmp_signed('==', left_value, right_value)
                    Type = ir.IntType(1)
                
        elif isinstance(right_type, ir.FloatType) and isinstance(left_type, ir.FloatType):
            Type = ir.FloatType()
            match operator:
                case '+':
                    value = self.builder.fadd(left_value, right_value)
                case '-':
                    value = self.builder.fsub(left_value, right_value)
                case '*':
                    value = self.builder.fmul(left_value, right_value)
                case '/':
                    value = self.builder.fdiv(left_value, right_value)
                case '%':
                    value = self.builder.frem(left_value, right_value)
                case '^':
                    pass
                case '<':
                    value = self.builder.fcmp_ordered('<', left_value, right_value)
                    Type = ir.IntType(1)
                case '<=':
                    value = self.builder.fcmp_ordered('<=', left_value, right_value)
                    Type = ir.IntType(1)
                case '>':
                    value = self.builder.fcmp_ordered('>', left_value, right_value)
                    Type = ir.IntType(1)
                case '>=':
                    value = self.builder.fcmp_ordered('>=', left_value, right_value)
                    Type = ir.IntType(1)
                case '==':
                    value = self.builder.fcmp_ordered('==', left_value, right_value)
                    Type = ir.IntType(1)

        return value, Type
    
    def __visit_call_expression(self, node: CallExpression) -> tuple[ir.Instruction, ir.Type]:
        name: str = node.function.value
        params: list[Expression] = node.arguments

        args = []
        types = []
        if len(params) > 0:
            for x in params:
                p_val, p_type = self.__resolve_value(x)
                args.append(p_val)
                types.append(p_type)

        match name:
            case 'printf':
                ret = self.builtin_printf(params=args, return_type=types[0])
                ret_type = self.type_map['int']
            case _:
                func, ret_type = self.env.lookup(name)
                ret = self.builder.call(func, args)
        
        return ret, ret_type
    
    def __resolve_value(self, node: Expression) -> tuple[ir.Value, ir.Type]:
        """ Resolves a value and returns a tuple (ir_value, ir_type) """
        match node.type():
            
            case NodeType.IntegerLiteral:
                node: IntegerLiteral = node
                value, Type = node.value, self.type_map['int']
                return ir.Constant(Type, value), Type
            case NodeType.FloatLiteral:
                node: FloatLiteral = node
                value, Type = node.value, self.type_map['float']
                return ir.Constant(Type, value), Type
            case NodeType.IdentifierLiteral:
                node: IdentifierLiteral = node
                ptr, Type = self.env.lookup(node.value)
                return self.builder.load(ptr), Type
            case NodeType.BooleanLiteral:
                node: BooleanLiteral = node
                print(node.value)
                return ir.Constant(ir.IntType(1), 1 if node.value else 0), ir.IntType(1)
            case NodeType.StringLiteral:
                node: StringLiteral = node
                string, Type = self.__convert_string(node.value)
                return string, Type
            
            
            case NodeType.InfixExpression:
                return self.__visit_infix_expression(node)
            case NodeType.CallExpression:
                return self.__visit_call_expression(node)
            
    def __convert_string(self, string: str) -> tuple[ir.Constant, ir.ArrayType]:
        string = string.replace('\\n', '\n\0')
        
        fmt: str = f"{string}\0"
        c_fmt: ir.Constant = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)), bytearray(fmt.encode("utf8")))

        
        global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name=f'__str_{self.__increment_counter()}')
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_fmt

        return global_fmt, global_fmt.type

    def builtin_printf(self, params: list[ir.Value], return_type: ir.Type) -> None:
        func, _ = self.env.lookup('printf')
        
        # Process all arguments to ensure they are i8* if they are strings
        final_args = []
        for p in params:
            # Case 1: The parameter is a global variable (e.g., a direct string literal)
            if isinstance(p, ir.GlobalVariable):
                # Bitcast the global variable to an i8*
                final_args.append(self.builder.bitcast(p, ir.IntType(8).as_pointer()))
            
            # Case 2: The parameter is a value whose type is a pointer to an array (e.g., a loaded string variable)
            elif isinstance(p.type, ir.PointerType) and isinstance(p.type.pointee, ir.ArrayType):
                # Bitcast the loaded value to an i8*
                final_args.append(self.builder.bitcast(p, ir.IntType(8).as_pointer()))
                
            # Case 3: Any other type of parameter (e.g., int, float)
            else:
                final_args.append(p)
                
        return self.builder.call(func, final_args)