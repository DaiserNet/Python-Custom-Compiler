"""Tests unitarios para el analizador sintáctico descendente recursivo de Chimera."""

import unittest
from app.core.lexer import LexicalAnalyzer
from app.core.parser import ChimeraParser, ASTNode, SyntaxErrorResult, SyntacticResult


def _parse(source: str) -> SyntacticResult:
    """Helper: analiza léxica y sintácticamente un programa fuente."""
    lexer = LexicalAnalyzer()
    tokens = lexer.analyze(source).tokens
    parser = ChimeraParser()
    return parser.parse_token(tokens)


def _ast(source: str) -> ASTNode:
    """Helper: retorna el AST asumiendo que no hay errores."""
    result = _parse(source)
    assert not result.errors, f"Errores inesperados: {result.errors}"
    assert result.tree is not None
    return result.tree


class TestProgramaMinimo(unittest.TestCase):
    """Programa más simple posible."""

    def test_programa_vacio(self):
        tree = _ast("main { }")
        self.assertEqual(tree.node_type, "Programa")
        self.assertEqual(len(tree.children), 0)

    def test_programa_requiere_main(self):
        result = _parse("{ }")
        self.assertTrue(len(result.errors) > 0)

    def test_programa_requiere_llaves(self):
        result = _parse("main")
        self.assertTrue(len(result.errors) > 0)


class TestDeclaracionVariable(unittest.TestCase):
    """Declaraciones de variables con tipo."""

    def test_declaracion_simple_int(self):
        tree = _ast("main { int x; }")
        self.assertEqual(tree.node_type, "Programa")
        decl = tree.children[0]
        self.assertEqual(decl.node_type, "Declaración")
        # Primer hijo = Tipo, segundo hijo = Identificador
        self.assertEqual(decl.children[0].value, "int")
        self.assertEqual(decl.children[1].value, "x")

    def test_declaracion_float(self):
        tree = _ast("main { float y; }")
        decl = tree.children[0]
        self.assertEqual(decl.children[0].value, "float")

    def test_declaracion_real(self):
        tree = _ast("main { real r; }")
        decl = tree.children[0]
        self.assertEqual(decl.children[0].value, "real")

    def test_declaracion_bool(self):
        tree = _ast("main { bool flag; }")
        decl = tree.children[0]
        self.assertEqual(decl.children[0].value, "bool")

    def test_declaracion_multiple_ids(self):
        tree = _ast("main { int a, b, c; }")
        decl = tree.children[0]
        self.assertEqual(decl.children[0].value, "int")
        self.assertEqual(decl.children[1].value, "a")
        self.assertEqual(decl.children[2].value, "b")
        self.assertEqual(decl.children[3].value, "c")

    def test_multiples_declaraciones(self):
        tree = _ast("main { int x; float y; bool z; }")
        self.assertEqual(len(tree.children), 3)


class TestAsignacion(unittest.TestCase):
    """Asignaciones de variables."""

    def test_asignacion_simple(self):
        tree = _ast("main { int x; x = 5; }")
        asig = tree.children[1]
        self.assertEqual(asig.node_type, "Asignación")
        self.assertEqual(asig.children[0].value, "x")
        self.assertEqual(asig.children[1].value, "5")

    def test_asignacion_expresion(self):
        tree = _ast("main { int x; x = 2 + 3; }")
        asig = tree.children[1]
        expr = asig.children[1]
        self.assertEqual(expr.node_type, "Operador Suma: (+)")
        self.assertEqual(expr.children[0].value, "2")
        self.assertEqual(expr.children[1].value, "3")

    def test_asignacion_vacia(self):
        tree = _ast("main { int x; x = ; }")
        asig = tree.children[1]
        self.assertEqual(asig.node_type, "Asignación")
        # Solo tiene el id, sin expresión
        self.assertEqual(len(asig.children), 1)


class TestSeleccion(unittest.TestCase):
    """Sentencia if/else."""

    def test_if_simple(self):
        tree = _ast("main { if true then end ; }")
        if_node = tree.children[0]
        self.assertEqual(if_node.node_type, "If")
        self.assertEqual(if_node.children[0].value, "true")

    def test_if_else(self):
        tree = _ast("main { if false then else end ; }")
        if_node = tree.children[0]
        self.assertEqual(if_node.node_type, "If-Else")

    def test_if_con_sentencias(self):
        tree = _ast("main { int x; if x > 0 then x = 1; else x = 0; end ; }")
        if_node = tree.children[1]
        self.assertEqual(if_node.node_type, "If-Else")
        # Condición es (>)
        self.assertEqual(if_node.children[0].node_type, "Operador Relacion: (>)")


class TestIteracion(unittest.TestCase):
    """Sentencia while."""

    def test_while_simple(self):
        tree = _ast("main { while (true) { } }")
        w = tree.children[0]
        self.assertEqual(w.node_type, "While")
        self.assertEqual(w.children[0].value, "true")

    def test_while_con_cuerpo(self):
        tree = _ast("main { int x; while (x > 0) { x = x - 1; } }")
        w = tree.children[1]
        self.assertEqual(w.node_type, "While")
        cuerpo = w.children[1]
        self.assertEqual(cuerpo.node_type, "Bloque")


class TestRepeticion(unittest.TestCase):
    """Sentencia do-while."""

    def test_do_while(self):
        tree = _ast("main { do while true ; }")
        dw = tree.children[0]
        self.assertEqual(dw.node_type, "Do-While")
        self.assertEqual(dw.children[1].value, "true")

    def test_do_while_con_cuerpo(self):
        tree = _ast("main { int x; do x = x + 1; while x < 10 ; }")
        dw = tree.children[1]
        self.assertEqual(dw.node_type, "Do-While")
        cuerpo = dw.children[0]
        self.assertEqual(cuerpo.node_type, "Bloque")


class TestEntradaSalida(unittest.TestCase):
    """Sentencias cin y cout."""

    def test_cin(self):
        tree = _ast("main { int x; cin >> x; }")
        cin = tree.children[1]
        self.assertEqual(cin.node_type, "Entrada")
        self.assertEqual(cin.children[1].value, "x")

    def test_cout_cadena(self):
        tree = _ast('main { cout << "hola" ; }')
        cout = tree.children[0]
        self.assertEqual(cout.node_type, "Salida")
        self.assertEqual(cout.children[1].node_type, "Cadena")

    def test_cout_expresion(self):
        tree = _ast("main { int x; cout << x ; }")
        cout = tree.children[1]
        self.assertEqual(cout.node_type, "Salida")
        self.assertEqual(cout.children[1].value, "x")

    def test_cout_cadena_y_expresion(self):
        tree = _ast('main { int x; cout << "valor:" << x ; }')
        cout = tree.children[1]
        self.assertEqual(cout.node_type, "Salida")
        compuesta = cout.children[1]
        self.assertEqual(compuesta.node_type, "SalidaCompuesta")


class TestExpresiones(unittest.TestCase):
    """Expresiones aritméticas y precedencia de operadores."""

    def test_suma(self):
        tree = _ast("main { int x; x = 1 + 2; }")
        expr = tree.children[1].children[1]
        self.assertEqual(expr.node_type, "Operador Suma: (+)")

    def test_multiplicacion(self):
        tree = _ast("main { int x; x = 3 * 4; }")
        expr = tree.children[1].children[1]
        self.assertEqual(expr.node_type, "Operador Mult: (*)")

    def test_precedencia_mult_sobre_suma(self):
        """2 + 3 * 4 => (+) con hijos [2, (*) con hijos [3, 4]]"""
        tree = _ast("main { int x; x = 2 + 3 * 4; }")
        expr = tree.children[1].children[1]
        self.assertEqual(expr.node_type, "Operador Suma: (+)")
        self.assertEqual(expr.children[0].value, "2")
        mult = expr.children[1]
        self.assertEqual(mult.node_type, "Operador Mult: (*)")
        self.assertEqual(mult.children[0].value, "3")
        self.assertEqual(mult.children[1].value, "4")

    def test_potencia(self):
        tree = _ast("main { int x; x = 2 ^ 3; }")
        expr = tree.children[1].children[1]
        self.assertEqual(expr.node_type, "Operador Pot: (^)")

    def test_parentesis(self):
        """(2 + 3) * 4 => (*) con hijos [(+), 4]"""
        tree = _ast("main { int x; x = (2 + 3) * 4; }")
        expr = tree.children[1].children[1]
        self.assertEqual(expr.node_type, "Operador Mult: (*)")
        self.assertEqual(expr.children[0].node_type, "Operador Suma: (+)")

    def test_relacional(self):
        tree = _ast("main { if 1 >= 2 then end ; }")
        cond = tree.children[0].children[0]
        self.assertEqual(cond.node_type, "Operador Relacion: (>=)")

    def test_operador_logico_not(self):
        tree = _ast("main { if ! true then end ; }")
        cond = tree.children[0].children[0]
        self.assertEqual(cond.node_type, "Operador lógico: (!)")

    def test_operador_logico_and(self):
        tree = _ast("main { if true && false then end ; }")
        cond = tree.children[0].children[0]
        self.assertEqual(cond.node_type, "Operador lógico: (&&)")

    def test_numero_real(self):
        tree = _ast("main { float x; x = 3.14; }")
        expr = tree.children[1].children[1]
        self.assertEqual(expr.node_type, "Real")
        self.assertEqual(expr.value, "3.14")


class TestIncrementos(unittest.TestCase):
    """Incremento y decremento prefijo y postfijo."""

    def test_incremento_prefijo(self):
        tree = _ast("main { int x; ++x; }")
        inc = tree.children[1]
        self.assertEqual(inc.node_type, "Incremento_Pre")
        self.assertEqual(inc.children[0].value, "x")

    def test_decremento_prefijo(self):
        tree = _ast("main { int x; --x; }")
        dec = tree.children[1]
        self.assertEqual(dec.node_type, "Decremento_Pre")
        self.assertEqual(dec.children[0].value, "x")

    def test_incremento_postfijo(self):
        tree = _ast("main { int x; x++; }")
        inc = tree.children[1]
        self.assertEqual(inc.node_type, "Incremento_Post")
        self.assertEqual(inc.children[0].value, "x")

    def test_decremento_postfijo(self):
        tree = _ast("main { int x; x--; }")
        dec = tree.children[1]
        self.assertEqual(dec.node_type, "Decremento_Post")
        self.assertEqual(dec.children[0].value, "x")


class TestErroresSintacticos(unittest.TestCase):
    """Verificar que los errores se reportan correctamente."""

    def test_falta_llave_apertura(self):
        result = _parse("main }")
        self.assertTrue(len(result.errors) > 0)

    def test_falta_llave_cierre(self):
        result = _parse("main {")
        self.assertTrue(len(result.errors) > 0)

    def test_falta_punto_y_coma(self):
        result = _parse("main { int x }")
        self.assertTrue(len(result.errors) > 0)

    def test_falta_end_en_if(self):
        result = _parse("main { if true then }")
        self.assertTrue(len(result.errors) > 0)

    def test_error_reporta_linea_columna(self):
        result = _parse("main { int ; }")
        self.assertTrue(len(result.errors) > 0)
        err = result.errors[0]
        self.assertIsInstance(err, SyntaxErrorResult)
        self.assertIsInstance(err.line, int)
        self.assertIsInstance(err.column, int)
        self.assertGreater(err.line, 0)

    def test_error_multiples_continua(self):
        """El parser debe intentar continuar después de un error."""
        result = _parse("main { int ; float y; }")
        # Debe haber al menos un error por la declaración mal formada
        self.assertTrue(len(result.errors) > 0)
        # Pero el árbol debe existir (recuperación de errores)
        self.assertIsNotNone(result.tree)


class TestSyntacticResult(unittest.TestCase):
    """Verificar la estructura del resultado."""

    def test_resultado_exitoso(self):
        result = _parse("main { }")
        self.assertIsNotNone(result.tree)
        self.assertEqual(len(result.errors), 0)
        self.assertIsInstance(result.ast_string, str)
        self.assertIn("Programa", result.ast_string)

    def test_resultado_con_errores(self):
        result = _parse("main")
        self.assertTrue(len(result.errors) > 0)

    def test_pretty_print(self):
        tree = _ast("main { int x; x = 5; }")
        pretty = tree.pretty()
        self.assertIn("Programa", pretty)
        self.assertIn("Declaración", pretty)
        self.assertIn("Asignación", pretty)


class TestProgramaCompleto(unittest.TestCase):
    """Programa completo que combina múltiples construcciones."""

    def test_programa_completo(self):
        source = """
        main {
            int x, y;
            float resultado;
            cin >> x;
            cin >> y;
            resultado = x + y * 2;
            if resultado >= 10 then
                cout << "Mayor o igual a 10" ;
            else
                cout << resultado ;
            end ;
            while (x > 0) {
                x--;
            }
        }
        """
        result = _parse(source)
        self.assertEqual(len(result.errors), 0, f"Errores: {result.errors}")
        self.assertIsNotNone(result.tree)
        self.assertEqual(result.tree.node_type, "Programa")

    def test_programa_con_do_while(self):
        source = """
        main {
            int i;
            i = 0;
            do
                ++i;
                cout << i ;
            while i < 5 ;
        }
        """
        result = _parse(source)
        self.assertEqual(len(result.errors), 0, f"Errores: {result.errors}")


if __name__ == "__main__":
    unittest.main()
