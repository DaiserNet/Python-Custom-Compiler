from lark import Lark, Tree, Token, Transformer
from lark import exceptions as lark_exceptions 
from typing import List, Any
from app.core.tokens import Token as Custom

"""
Este modulo define el parser para el lenguaje de programación Chimera. Utiliza la biblioteca Lark 
para construir un parser a partir de una gramática optimizada para generar un AST real.
"""
GRAMMAR = r"""
    start: programa

    programa: "main" "{" bloque "}"
    
    bloque: instruccion*
    ?instruccion: declaracion_variable | sentencia
    
    // Soporte para tipo 'real' añadido
    declaracion_variable: TIPO identificador ";"
    TIPO: "int" | "float" | "bool" | "real"
    identificador: ID ("," ID)*
    
    // Agregamos 'inc_dec' como una sentencia válida
    ?sentencia: seleccion | iteracion | repeticion | sent_in | sent_out | asignacion | inc_dec
    asignacion: ID "=" sent_expresion
    
    ?sent_expresion: expresion ";" | ";"
    
    // Estructuras de control adaptadas al archivo de prueba
    seleccion: "if" expresion "then" bloque ("else" bloque)? "end" ";"?
    iteracion: "while" expresion "{" bloque "}" ";"?
    repeticion: "do" bloque "until" expresion ";"?
    
    // Remoción de los operadores << y >> para cin/cout directos
    sent_in: "cin" ID ";"
    sent_out: "cout" expresion ";"
    
    // Sentencia dedicada para incremento y decremento posfijo
    inc_dec: ID INC_DEC_OP ";"
    INC_DEC_OP: "++" | "--"
    
    // === JERARQUÍA DE OPERADORES ===
    ?expresion: expresion_logica

    ?expresion_logica: expresion_relacional (OP_AND_OR expresion_relacional)*
    OP_AND_OR: "&&" | "||"
    
    ?expresion_relacional: expresion_simple (REL_OP expresion_simple)?
    REL_OP: "<" | "<=" | ">" | ">=" | "==" | "!="
    
    // Se removieron '++' y '--' de aquí para evitar conflictos binarios
    ?expresion_simple: termino (SUMA_OP termino)*
    SUMA_OP: "+" | "-"
    
    ?termino: factor (MULT_OP factor)*
    MULT_OP: "*" | "/" | "%"
    
    ?factor: componente (POT_OP componente)*
    POT_OP: "^"
    
    ?componente: "(" expresion ")" | NUMERO | ID | BOOL_VAL | OP_NOT componente
    OP_NOT: "!"

    ID: /[a-zA-Z_][a-zA-Z0-9_]*/
    NUMERO: /[0-9]+(\.[0-9]+)?/
    CADENA: /"[^"]*"/ | /'[^']*'/
    BOOL_VAL: "true" | "false"

    %import common.WS
    %ignore WS
"""

class ChimeraASTTransformer(Transformer):
    """Transforma el árbol de análisis sintáctico generado por Lark en un AST más manejable y específico para Chimera."""
    def start(self, items):
        return items[0]

    def programa(self, items):
        # Simplifica el nodo raíz agrupando directamente los bloques hijos
        return Tree("Programa", items[0].children if hasattr(items[0], 'children') else items)

    def bloque(self, items):
        return Tree("Bloque", items)
    
    def declaracion_variable(self, items):
        tipo_var = str(items[0])
        id_node = items[1]
        ids = id_node.children if isinstance(id_node, Tree) else [id_node]
        return Tree(f"({tipo_var})", ids)

    def asignacion(self, items):
        # Asignación limpia: Variable -> Expresión matemática
        return Tree(f"[=]", [items[0], items[1]])

    def seleccion(self, items):
        # items que contiene solo: condición, bloque_then, bloque_else (opcional)
        condicion = items[0]
        bloque_then = items[1]
        if len(items) > 2:
            return Tree("If-Else", [condicion, bloque_then, items[2]])
        return Tree("If", [condicion, bloque_then])
    
    def iteracion(self, items):
        # items contiene solo: condición, bloque
        return Tree("While", [items[0], items[1]])
    
    def repeticion(self, items):
        # items contiene solo: bloque, condición
        return Tree("Do-Until", [items[0], items[1]])
    
    def inc_dec(self, items):
        # Mapea los incrementos/decrementos unarios posfijos en el AST
        variable = items[0]
        operador = str(items[1])
        return Tree(f"Post_Op ({operador})", [variable])

    # --- Procesador Genérico para operaciones binarias (aritméticas y lógicas) ---
    def _build_binary_tree(self, items):
        if len(items) == 1:
            return items[0]
        
        # Convierte una lista plana [1, '+', 2, '-', 3] en un árbol binario jerárquico real
        root_node = items[0]
        i = 1
        while i < len(items):
            # Extrae el símbolo del operador real de Lark (+, -, *, etc.)
            op_symbol = str(items[i])
            right_operand = items[i+1]

            # El operador se convierte en el padre supremo de la operación actual
            root_node = Tree(f"({op_symbol})", [root_node, right_operand])
            i += 2
        return root_node

    def expresion(self, items): return self._build_binary_tree(items)
    def expresion_logica(self, items): return self._build_binary_tree(items)
    def expresion_relacional(self, items): return self._build_binary_tree(items)
    def expresion_simple(self, items): return self._build_binary_tree(items)
    def termino(self, items): return self._build_binary_tree(items)
    def factor(self, items): return self._build_binary_tree(items)

    def componente(self, items):
        # Esta regla atrapa el operador unario NOT (!)
        if len(items) == 2: 
            op_symbol = str(items[0])
            return Tree(f"Op_Unario ({op_symbol})", [items[1]])
        return items[0]

class SyntaxErrorResult:
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column

class SyntacticResult:
    def __init__(self, tree: Any, errors: List[SyntaxErrorResult]):
        self.tree = tree
        self.errors = errors
        self.ast_string = tree.pretty() if tree else "Sin árbol generado debido a errores."

class ChimeraParser:
    def __init__(self):
        self.parser = Lark(GRAMMAR, parser='earley', start='start')

    def parse_token(self, tokens: List[Token]) -> SyntacticResult:
        """
        Toma la lista de tokens del lexer, reconstruye la cadena fuente 
        y genera el AST reportando errores precisos sin romper la GUI.
        """
        ignored_types = {'WHITESPACE', 'COMMENT_SINGLE', 'COMMENT_MULTI'}
        valid_tokens = [t for t in tokens if t.token_type.name not in ignored_types]

        source_from_tokens = " ".join([t.lexeme for t in valid_tokens])

        errors = []
        ast = None

        try:
            # 1. Generar el árbol sintáctico concreto base (CST)
            raw_tree = self.parser.parse(source_from_tokens)
            
            # 2. Transformar el CST aplicando ingeniería inversa para obtener un AST real
            ast = ChimeraASTTransformer().transform(raw_tree)
            
        except lark_exceptions.UnexpectedToken as e:
            error_idx = source_from_tokens[:e.pos_in_stream].count(' ')
            original_token = valid_tokens[min(error_idx, len(valid_tokens)-1)]
            msg = f"Error: Token inesperado '{e.token}'. Se esperaba uno de: {', '.join(e.expected)}."
            errors.append(SyntaxErrorResult(msg, original_token.line, original_token.column))
            
        except lark_exceptions.UnexpectedCharacters as e:
            errors.append(SyntaxErrorResult("Error: Estructura sintáctica inválida en esta región.", e.line, e.column))
            
        except lark_exceptions.UnexpectedEOF as e:
            last_line = valid_tokens[-1].line if valid_tokens else 1
            last_col = valid_tokens[-1].column if valid_tokens else 1
            msg = "Error: Estructura sintáctica incompleta en el bloque."
            errors.append(SyntaxErrorResult(msg, last_line, last_col))
        
        return SyntacticResult(ast, errors)