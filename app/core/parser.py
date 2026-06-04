"""
Analizador Sintáctico Descendente Recursivo para el lenguaje Chimera.

Este módulo implementa un parser descendente recursivo que consume directamente
los tokens generados por el analizador léxico, construye un Árbol Sintáctico
Abstracto (AST) y reporta errores sintácticos con línea y columna precisas.

Gramática implementada:
    programa            → main { lista_declaracion }
    lista_declaracion   → lista_declaracion declaracion | declaracion
    declaracion         → declaracion_variable | lista_sentencias
    declaracion_variable→ tipo identificador ;
    identificador       → id | identificador , id
    tipo                → int | float | bool
    lista_sentencias    → lista_sentencias sentencia | ε
    sentencia           → seleccion | iteracion | repeticion | sent_in
                        | sent_out | asignacion
    asignacion          → id = sent_expresion
    sent_expresion      → expresion ; | ;
    seleccion           → if expresion then lista_sentencias
                          [ else lista_sentencias ] end
    iteracion           → while expresion lista_sentencias end
    repeticion          → do lista_sentencias while expresion
    sent_in             → cin >> id ;
    sent_out            → cout << salida
    salida              → cadena | expresion | cadena << expresion
                        | expresion << cadena
    expresion           → expresion_simple [ rel_op expresion_simple ]
    rel_op              → < | <= | > | >= | == | !=
    expresion_simple    → expresion_simple suma_op termino | termino
    suma_op             → + | - | ++ | --
    termino             → termino mult_op factor | factor
    mult_op             → * | / | %
    factor              → factor pot_op componente | componente
    pot_op              → ^
    componente          → ( expresion ) | número | id | bool
                        | op_logico componente
    op_logico           → && | || | !
    cadena              → "cualquier texto"
"""

from typing import List, Any, Optional
from app.core.tokens import Token as LexToken, TokenType


# ======================================================================
# Nodo del Árbol Sintáctico Abstracto (AST)
# ======================================================================

class ASTNode:
    """Nodo genérico del Árbol Sintáctico Abstracto.

    Attributes:
        node_type: Etiqueta descriptiva del nodo (ej. 'Programa', 'If', '(+)').
        children:  Lista de nodos hijos (sub-árboles).
        value:     Valor literal para nodos hoja (ej. '42', 'x', '"hola"').
        line:      Línea del token de origen (para reportar errores).
        column:    Columna del token de origen.
    """

    def __init__(
        self,
        node_type: str,
        children: Optional[List["ASTNode"]] = None,
        value: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
    ):
        self.node_type = node_type
        self.children = children or []
        self.value = value
        self.line = line
        self.column = column

    # Para depuración / representación textual del AST
    def pretty(self, indent: int = 0) -> str:
        prefix = "  " * indent
        label = self.node_type
        if self.value is not None:
            label += f": {self.value}"
        lines = [f"{prefix}{label}"]
        for child in self.children:
            lines.append(child.pretty(indent + 1))
        return "\n".join(lines)

    def __repr__(self):
        if self.value is not None:
            return f"ASTNode({self.node_type!r}, value={self.value!r})"
        return f"ASTNode({self.node_type!r}, children={len(self.children)})"


# ======================================================================
# Resultado del análisis sintáctico
# ======================================================================

class SyntaxErrorResult:
    """Representa un error sintáctico individual."""

    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column

    def __repr__(self):
        return f"SyntaxError(L{self.line}:C{self.column} {self.message!r})"


class SyntacticResult:
    """Resultado completo del análisis sintáctico."""

    def __init__(self, tree: Any, errors: List[SyntaxErrorResult]):
        self.tree = tree
        self.errors = errors
        self.ast_string = tree.pretty() if tree else "Sin árbol generado debido a errores."


# ======================================================================
# Parser Descendente Recursivo
# ======================================================================

class ChimeraParser:
    """Analizador sintáctico descendente recursivo para Chimera.

    Consume tokens del analizador léxico y construye un AST.
    Los errores se acumulan y el parser intenta recuperarse
    para reportar múltiples errores en una sola pasada.
    """

    # Tokens que se ignoran al alimentar el parser
    _IGNORED_TOKEN_TYPES = frozenset({
        TokenType.WHITESPACE,
        TokenType.COMMENT_SINGLE,
        TokenType.COMMENT_MULTI,
    })

    # Tipos de la gramática
    _TYPE_KEYWORDS = frozenset({"int", "float", "real", "bool"})

    # Operadores relacionales
    _REL_OPS = frozenset({"<", "<=", ">", ">=", "==", "!="})

    # Operadores de suma
    _ADD_OPS = frozenset({"+", "-", "++", "--"})

    # Operadores de multiplicación
    _MULT_OPS = frozenset({"*", "/", "%"})

    # Operadores de potencia
    _POT_OPS = frozenset({"^"})

    # Operadores lógicos binarios (infijos: &&, ||)
    _BINARY_LOGICAL_OPS = frozenset({"&&", "||"})

    # Operador lógico unario (prefijo: !)
    _UNARY_LOGICAL_OPS = frozenset({"!"})

    # Puntos de sincronización para recuperación de errores
    _SYNC_LEXEMES = frozenset({";", "}", "end"})

    def __init__(self):
        self.tokens: List[LexToken] = []
        self.pos: int = 0
        self.errors: List[SyntaxErrorResult] = []

    # ------------------------------------------------------------------
    # Punto de entrada público (mantiene la interfaz original)
    # ------------------------------------------------------------------

    def parse_token(self, tokens: List[LexToken]) -> SyntacticResult:
        """Analiza la lista de tokens y retorna el resultado sintáctico.

        Args:
            tokens: Lista de tokens producidos por el analizador léxico.

        Returns:
            SyntacticResult con el AST y lista de errores.
        """
        # Filtrar tokens ignorados (espacios, comentarios)
        self.tokens = [t for t in tokens if t.token_type not in self._IGNORED_TOKEN_TYPES]
        self.pos = 0
        self.errors = []

        ast = None
        try:
            ast = self._programa()
        except _ParseAbort:
            # Error fatal irrecuperable — se reportó en self.errors
            pass

        return SyntacticResult(ast, self.errors)

    # ------------------------------------------------------------------
    # Utilidades de consumo de tokens
    # ------------------------------------------------------------------

    def _current(self) -> Optional[LexToken]:
        """Retorna el token actual sin avanzar, o None si se acabaron."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _peek_lexeme(self) -> Optional[str]:
        """Retorna el lexema del token actual."""
        tok = self._current()
        return tok.lexeme if tok else None

    def _peek_type(self) -> Optional[TokenType]:
        """Retorna el tipo del token actual."""
        tok = self._current()
        return tok.token_type if tok else None

    def _advance(self) -> LexToken:
        """Avanza al siguiente token y retorna el anterior."""
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _check_lexeme(self, lexeme: str) -> bool:
        """¿El token actual tiene este lexema?"""
        tok = self._current()
        return tok is not None and tok.lexeme == lexeme

    def _check_type(self, token_type: TokenType) -> bool:
        """¿El token actual tiene este tipo?"""
        tok = self._current()
        return tok is not None and tok.token_type == token_type

    def _match_lexeme(self, lexeme: str) -> LexToken:
        """Consume el token si su lexema coincide; de lo contrario reporta error."""
        tok = self._current()
        if tok is not None and tok.lexeme == lexeme:
            return self._advance()
        self._error_expected(f"'{lexeme}'")
        # Retornar un token sintético para que el parser pueda continuar
        return self._synthetic_token(lexeme)

    def _match_type(self, token_type: TokenType) -> LexToken:
        """Consume el token si su tipo coincide; de lo contrario reporta error."""
        tok = self._current()
        if tok is not None and tok.token_type == token_type:
            return self._advance()
        self._error_expected(token_type.value)
        return self._synthetic_token(f"<{token_type.value}>")

    def _check_double(self, ch: str) -> bool:
        """Verifica si los próximos dos tokens forman un operador doble (>> o <<)."""
        if self.pos + 1 >= len(self.tokens):
            return False
        t1 = self.tokens[self.pos]
        t2 = self.tokens[self.pos + 1]
        return t1.lexeme == ch and t2.lexeme == ch

    def _match_double(self, ch: str, display: str) -> LexToken:
        """Consume dos tokens consecutivos idénticos (>> o <<)."""
        if self._check_double(ch):
            tok = self._advance()
            self._advance()
            return tok
        self._error_expected(f"'{display}'")
        return self._synthetic_token(display)

    def _at_end(self) -> bool:
        """¿Se agotaron los tokens?"""
        return self.pos >= len(self.tokens)

    # ------------------------------------------------------------------
    # Manejo de errores
    # ------------------------------------------------------------------

    def _error(self, message: str):
        """Registra un error sintáctico con posición del token actual."""
        tok = self._current()
        if tok:
            line, col = tok.line, tok.column
        elif self.tokens:
            last = self.tokens[-1]
            line, col = last.line, last.column
        else:
            line, col = 1, 1
        self.errors.append(SyntaxErrorResult(message, line, col))

    def _error_expected(self, expected: str):
        """Reporta error indicando qué se esperaba vs qué se encontró."""
        tok = self._current()
        if tok:
            found = f"'{tok.lexeme}'"
            self._error(f"Se esperaba {expected}, se encontró {found}.")
        else:
            self._error(f"Se esperaba {expected}, pero se llegó al final del archivo.")

    def _synchronize(self):
        """Avanza tokens hasta encontrar un punto de sincronización.

        Esto permite continuar el análisis después de un error.
        """
        while not self._at_end():
            tok = self._current()
            if tok.lexeme in self._SYNC_LEXEMES:
                # Consumir el punto de sincronización y continuar
                self._advance()
                return
            # Si encontramos el inicio de una nueva declaración o sentencia
            if tok.lexeme in self._TYPE_KEYWORDS or tok.lexeme in (
                "if", "while", "do", "cin", "cout"
            ):
                return  # No consumir — es el inicio de algo nuevo
            self._advance()

    def _synthetic_token(self, lexeme: str) -> LexToken:
        """Crea un token sintético para recuperación de errores."""
        tok = self._current()
        if tok:
            return LexToken(
                token_type=TokenType.UNKNOWN,
                lexeme=lexeme,
                start=tok.start,
                end=tok.end,
                line=tok.line,
                column=tok.column,
            )
        elif self.tokens:
            last = self.tokens[-1]
            return LexToken(
                token_type=TokenType.UNKNOWN,
                lexeme=lexeme,
                start=last.end,
                end=last.end,
                line=last.line,
                column=last.column,
            )
        return LexToken(
            token_type=TokenType.UNKNOWN,
            lexeme=lexeme,
            start=0, end=0, line=1, column=1,
        )

    # ------------------------------------------------------------------
    # Reglas gramaticales
    # ------------------------------------------------------------------

    def _programa(self) -> Optional[ASTNode]:
        """programa → main { lista_declaracion }"""
        tok_main = self._match_lexeme("main")
        self._match_lexeme("{")
        declaraciones = self._lista_declaracion()
        self._match_lexeme("}")

        # Verificar que no queden tokens sin procesar
        if not self._at_end():
            tok = self._current()
            self._error(f"Token inesperado '{tok.lexeme}' después del cierre del programa.")

        node = ASTNode(
            "Programa",
            children=declaraciones,
            line=tok_main.line,
            column=tok_main.column,
        )
        return node

    def _lista_declaracion(self) -> List[ASTNode]:
        """lista_declaracion → { declaracion }

        Consume declaraciones (variables y sentencias) hasta encontrar
        '}' o fin de tokens.
        """
        declaraciones = []
        while not self._at_end() and not self._check_lexeme("}"):
            decl = self._declaracion()
            if decl is not None:
                declaraciones.append(decl)
        return declaraciones

    def _declaracion(self) -> Optional[ASTNode]:
        """declaracion → declaracion_variable | sentencia

        Si el token actual es un tipo (int/float/bool), parsea una
        declaración de variable. De lo contrario, parsea una sentencia.
        """
        tok = self._current()
        if tok is None:
            return None

        # ¿Es una declaración de variable?
        if tok.lexeme in self._TYPE_KEYWORDS:
            return self._declaracion_variable()

        # Si no, es una sentencia
        return self._sentencia()

    def _declaracion_variable(self) -> Optional[ASTNode]:
        """declaracion_variable → tipo identificador ;"""
        tipo_node = self._tipo()

        # Parsear la lista de identificadores separados por coma
        ids = self._identificador_lista()

        self._match_lexeme(";")

        children = [tipo_node] + ids
        return ASTNode(
            "Declaración",
            children=children,
            line=tipo_node.line,
            column=tipo_node.column,
        )

    def _tipo(self) -> ASTNode:
        """tipo → int | float | real | bool"""
        tok = self._current()
        if tok and tok.lexeme in self._TYPE_KEYWORDS:
            self._advance()
            return ASTNode("Tipo", value=tok.lexeme, line=tok.line, column=tok.column)

        self._error_expected("tipo (int, float, real, bool)")
        return ASTNode("Error_Sintactico: Expresion Invalida", value="<error_tipo>", line=tok.line if tok else 1, column=tok.column if tok else 1)

    def _identificador_lista(self) -> List[ASTNode]:
        """identificador → id | identificador , id

        Parsea una lista de identificadores separados por coma.
        """
        ids = []
        tok = self._match_type(TokenType.IDENTIFIER)
        ids.append(ASTNode("Identificador", value=tok.lexeme, line=tok.line, column=tok.column))

        while self._check_lexeme(","):
            self._advance()  # Consumir ','
            tok = self._match_type(TokenType.IDENTIFIER)
            ids.append(ASTNode("Identificador", value=tok.lexeme, line=tok.line, column=tok.column))

        return ids

    def _sentencia(self) -> Optional[ASTNode]:
        """sentencia → seleccion | iteracion | repeticion | sent_in | sent_out
                     | incremento | asignacion"""
        tok = self._current()
        if tok is None:
            return None

        if tok.lexeme == "if":
            return self._seleccion()
        elif tok.lexeme == "while":
            return self._iteracion()
        elif tok.lexeme == "do":
            return self._repeticion()
        elif tok.lexeme == "cin":
            return self._sent_in()
        elif tok.lexeme == "cout":
            return self._sent_out()
        elif tok.lexeme in ("++", "--"):
            # Prefijo: ++id ; | --id ;
            return self._incremento_prefijo()
        elif tok.token_type == TokenType.IDENTIFIER:
            # Verificar si es postfijo: id++ ; | id-- ;
            next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_tok and next_tok.lexeme in ("++", "--"):
                return self._incremento_postfijo()
            return self._asignacion()
        else:
            self._error(f"Sentencia inesperada: '{tok.lexeme}'.")
            self._synchronize()
            return None

    def _incremento_prefijo(self) -> ASTNode:
        """Incremento/decremento prefijo: ++id ; | --id ;"""
        op_tok = self._advance()  # Consumir ++ o --
        tok_id = self._match_type(TokenType.IDENTIFIER)
        self._match_lexeme(";")

        id_node = ASTNode("Identificador", value=tok_id.lexeme, line=tok_id.line, column=tok_id.column)
        op_label = "Incremento" if op_tok.lexeme == "++" else "Decremento"
        return ASTNode(
            f"{op_label}_Pre",
            children=[id_node],
            line=op_tok.line,
            column=op_tok.column,
        )

    def _incremento_postfijo(self) -> ASTNode:
        """Incremento/decremento postfijo: id++ ; | id-- ;"""
        tok_id = self._advance()  # Consumir identificador
        op_tok = self._advance()  # Consumir ++ o --
        self._match_lexeme(";")

        id_node = ASTNode("Identificador", value=tok_id.lexeme, line=tok_id.line, column=tok_id.column)
        op_label = "Incremento" if op_tok.lexeme == "++" else "Decremento"
        return ASTNode(
            f"{op_label}_Post",
            children=[id_node],
            line=tok_id.line,
            column=tok_id.column,
        )

    def _asignacion(self) -> ASTNode:
        """asignacion → id = sent_expresion
        sent_expresion → expresion ; | ;
        """
        tok_id = self._match_type(TokenType.IDENTIFIER)
        id_node = ASTNode("Identificador", value=tok_id.lexeme, line=tok_id.line, column=tok_id.column)

        self._match_lexeme("=")

        # sent_expresion → expresion ; | ;
        if self._check_lexeme(";"):
            self._advance()
            return ASTNode(
                "Asignación",
                children=[id_node],
                line=tok_id.line,
                column=tok_id.column,
            )

        expr = self._expresion()
        self._match_lexeme(";")

        return ASTNode(
            "Asignación",
            children=[id_node, expr],
            line=tok_id.line,
            column=tok_id.column,
        )

    def _seleccion(self) -> ASTNode:
        """seleccion → if expresion then lista_sentencias [ else lista_sentencias ] end ;"""
        tok_if = self._match_lexeme("if")
        condicion = self._expresion()
        self._match_lexeme("then")

        bloque_then = self._lista_sentencias_bloque()

        bloque_else = None
        if self._check_lexeme("else"):
            self._advance()
            bloque_else = self._lista_sentencias_bloque()

        self._match_lexeme("end")
        self._match_lexeme(";")

        children = [condicion, bloque_then]
        node_type = "If"
        if bloque_else is not None:
            children.append(bloque_else)
            node_type = "If-Else"

        return ASTNode(node_type, children=children, line=tok_if.line, column=tok_if.column)

    def _iteracion(self) -> ASTNode:
        """iteracion → while ( expresion ) { lista_sentencias }"""
        tok_while = self._match_lexeme("while")
        self._match_lexeme("(")
        condicion = self._expresion()
        self._match_lexeme(")")
        self._match_lexeme("{")
        cuerpo = self._lista_sentencias_bloque()
        self._match_lexeme("}")

        return ASTNode(
            "While",
            children=[condicion, cuerpo],
            line=tok_while.line,
            column=tok_while.column,
        )

    def _repeticion(self) -> ASTNode:
        """repeticion → do lista_sentencias while expresion ;"""
        tok_do = self._match_lexeme("do")
        cuerpo = self._lista_sentencias_bloque()
        self._match_lexeme("while")
        condicion = self._expresion()
        self._match_lexeme(";")

        return ASTNode(
            "Do-While",
            children=[cuerpo, condicion],
            line=tok_do.line,
            column=tok_do.column,
        )

    def _sent_in(self) -> ASTNode:
        """sent_in → cin >> id ;"""
        tok_cin = self._match_lexeme("cin")
        tok_op = self._match_double(">", ">>")
        tok_id = self._match_type(TokenType.IDENTIFIER)
        self._match_lexeme(";")

        op_node = ASTNode("Operador", value=">>", line=tok_op.line, column=tok_op.column)
        id_node = ASTNode("Identificador", value=tok_id.lexeme, line=tok_id.line, column=tok_id.column)
        return ASTNode("Entrada", children=[op_node, id_node], line=tok_cin.line, column=tok_cin.column)

    def _sent_out(self) -> ASTNode:
        """sent_out → cout << salida ;
        salida → cadena | expresion | cadena << expresion | expresion << cadena
        """
        tok_cout = self._match_lexeme("cout")
        tok_op = self._match_double("<", "<<")

        op_node = ASTNode("Operador", value="<<", line=tok_op.line, column=tok_op.column)
        salida_node = self._salida()
        self._match_lexeme(";")

        return ASTNode("Salida", children=[op_node, salida_node], line=tok_cout.line, column=tok_cout.column)

    def _salida(self) -> ASTNode:
        """salida → cadena | expresion | cadena << expresion | expresion << cadena"""
        tok = self._current()

        if tok and tok.token_type == TokenType.STRING:
            # Comienza con cadena
            cadena_tok = self._advance()
            cadena_node = ASTNode("Cadena", value=cadena_tok.lexeme, line=cadena_tok.line, column=cadena_tok.column)

            if self._check_double("<"):
                # cadena << expresion
                tok_op = self._match_double("<", "<<")
                expr = self._expresion()
                op_node = ASTNode("Operador", value="<<", line=tok_op.line, column=tok_op.column)
                return ASTNode(
                    "SalidaCompuesta",
                    children=[cadena_node, op_node, expr],
                    line=cadena_tok.line,
                    column=cadena_tok.column,
                )
            return cadena_node
        else:
            # Comienza con expresion
            expr = self._expresion()

            if self._check_double("<"):
                # expresion << cadena
                tok_op = self._match_double("<", "<<")
                tok_cad = self._current()
                if tok_cad and tok_cad.token_type == TokenType.STRING:
                    cadena_tok = self._advance()
                    cadena_node = ASTNode("Cadena", value=cadena_tok.lexeme, line=cadena_tok.line, column=cadena_tok.column)
                    op_node = ASTNode("Operador", value="<<", line=tok_op.line, column=tok_op.column)
                    return ASTNode(
                        "SalidaCompuesta",
                        children=[expr, op_node, cadena_node],
                        line=expr.line,
                        column=expr.column,
                    )
                else:
                    self._error_expected("cadena de texto")
            return expr

    def _lista_sentencias_bloque(self) -> ASTNode:
        """Parsea un bloque de sentencias (lista_sentencias).

        Se detiene al encontrar 'else', 'end', 'while' (para do-while),
        '}', o fin de tokens.
        """
        sentencias = []
        while not self._at_end():
            tok = self._current()
            if tok.lexeme in ("else", "end", "}", "while"):
                break
            sent = self._declaracion()
            if sent is not None:
                sentencias.append(sent)

        first = sentencias[0] if sentencias else None
        return ASTNode(
            "Bloque",
            children=sentencias,
            line=first.line if first else (self._current().line if self._current() else 1),
            column=first.column if first else (self._current().column if self._current() else 1),
        )

    # ------------------------------------------------------------------
    # Expresiones con precedencia de operadores
    # ------------------------------------------------------------------

    def _expresion(self) -> ASTNode:
        """expresion → expresion_logica

        Nivel más bajo de precedencia: operadores lógicos binarios (&&, ||)
        """
        return self._expresion_logica()

    def _expresion_logica(self) -> ASTNode:
        """expresion_logica → expresion_relacional { (&& | ||) expresion_relacional }"""
        node = self._expresion_relacional()

        while not self._at_end():
            tok = self._current()
            if tok is None or tok.lexeme not in self._BINARY_LOGICAL_OPS:
                break
            op_tok = self._advance()
            right = self._expresion_relacional()
            node = ASTNode(
                f"Operador lógico: ({op_tok.lexeme})",
                children=[node, right],
                line=op_tok.line,
                column=op_tok.column,
            )

        return node

    def _expresion_relacional(self) -> ASTNode:
        """expresion_relacional → expresion_simple [ rel_op expresion_simple ]"""
        left = self._expresion_simple()

        tok = self._current()
        if tok and tok.lexeme in self._REL_OPS:
            op_tok = self._advance()
            right = self._expresion_simple()
            return ASTNode(
                f"Operador Relacion: ({op_tok.lexeme})",
                children=[left, right],
                line=op_tok.line,
                column=op_tok.column,
            )

        return left

    def _expresion_simple(self) -> ASTNode:
        """expresion_simple → termino { suma_op termino }

        Iteración izquierda-a-derecha (asociatividad izquierda).
        """
        node = self._termino()

        while not self._at_end():
            tok = self._current()
            if tok is None or tok.lexeme not in self._ADD_OPS:
                break
            op_tok = self._advance()
            right = self._termino()
            node = ASTNode(
                f"Operador Suma: ({op_tok.lexeme})",
                children=[node, right],
                line=op_tok.line,
                column=op_tok.column,
            )

        return node

    def _termino(self) -> ASTNode:
        """termino → factor { mult_op factor }"""
        node = self._factor()

        while not self._at_end():
            tok = self._current()
            if tok is None or tok.lexeme not in self._MULT_OPS:
                break
            op_tok = self._advance()
            right = self._factor()
            node = ASTNode(
                f"Operador Mult: ({op_tok.lexeme})",
                children=[node, right],
                line=op_tok.line,
                column=op_tok.column,
            )

        return node

    def _factor(self) -> ASTNode:
        """factor → componente { pot_op componente }"""
        node = self._componente()

        while not self._at_end():
            tok = self._current()
            if tok is None or tok.lexeme not in self._POT_OPS:
                break
            op_tok = self._advance()
            right = self._componente()
            node = ASTNode(
                f"Operador Pot: ({op_tok.lexeme})",
                children=[node, right],
                line=op_tok.line,
                column=op_tok.column,
            )

        return node

    def _componente(self) -> ASTNode:
        """componente → ( expresion ) | número | id | bool | op_logico componente

        op_logico → && | || | !
        """
        tok = self._current()
        if tok is None:
            self._error("Se esperaba una expresión, pero se llegó al final del archivo.")
            return ASTNode("Error_Sintactico: Expresion Invalida", value="<EOF>", line=1, column=1)

        # Operador lógico unario prefijo: !
        if tok.lexeme in self._UNARY_LOGICAL_OPS:
            op_tok = self._advance()
            operand = self._componente()
            return ASTNode(
                f"Operador lógico: ({op_tok.lexeme})",
                children=[operand],
                line=op_tok.line,
                column=op_tok.column,
            )

        # Paréntesis
        if tok.lexeme == "(":
            self._advance()
            expr = self._expresion()
            self._match_lexeme(")")
            return expr

        # Número entero
        if tok.token_type == TokenType.INTEGER:
            self._advance()
            return ASTNode("Entero", value=tok.lexeme, line=tok.line, column=tok.column)

        # Número real
        if tok.token_type == TokenType.REAL:
            self._advance()
            return ASTNode("Real", value=tok.lexeme, line=tok.line, column=tok.column)

        # Booleano (true / false)
        if tok.lexeme in ("true", "false"):
            self._advance()
            return ASTNode("Booleano", value=tok.lexeme, line=tok.line, column=tok.column)

        # Identificador
        if tok.token_type == TokenType.IDENTIFIER:
            self._advance()
            return ASTNode("Identificador", value=tok.lexeme, line=tok.line, column=tok.column)

        # Ningún componente válido
        self._error(f"Se esperaba un valor o expresión, se encontró '{tok.lexeme}'.")
        self._advance()  # Avanzar para no quedar en bucle infinito
        return ASTNode("Error_Sintactico: Expresion Invalida", value=tok.lexeme, line=tok.line, column=tok.column)


# ======================================================================
# Excepción interna para abortar el análisis
# ======================================================================

class _ParseAbort(Exception):
    """Excepción interna: aborta el análisis ante un error irrecuperable."""
    pass