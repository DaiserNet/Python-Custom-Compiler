import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.lexer import LexicalAnalyzer
from app.core.tokens import TokenType
from app.core.tokens import token_color_group


class TestLexicalAnalyzer(unittest.TestCase):
    def setUp(self):
        self.lexer = LexicalAnalyzer()

    def test_keywords_identifiers_and_numbers(self):
        source = "int main if else end do while switch case float cin cout var1 abc123 12 3.14"
        tokens = self.lexer.tokenize(source)
        lexeme_types = [(t.lexeme, t.token_type) for t in tokens]

        expected = [
            ("int", TokenType.KEYWORD),
            ("main", TokenType.KEYWORD),
            ("if", TokenType.KEYWORD),
            ("else", TokenType.KEYWORD),
            ("end", TokenType.KEYWORD),
            ("do", TokenType.KEYWORD),
            ("while", TokenType.KEYWORD),
            ("switch", TokenType.KEYWORD),
            ("case", TokenType.KEYWORD),
            ("float", TokenType.KEYWORD),
            ("cin", TokenType.KEYWORD),
            ("cout", TokenType.KEYWORD),
            ("var1", TokenType.IDENTIFIER),
            ("abc123", TokenType.IDENTIFIER),
            ("12", TokenType.INTEGER),
            ("3.14", TokenType.REAL),
        ]
        self.assertEqual(lexeme_types, expected)

    def test_comments_single_and_multi_line(self):
        source = "// comentario\n/* multi\nline */"
        tokens = self.lexer.tokenize(source)
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].token_type, TokenType.COMMENT_SINGLE)
        self.assertEqual(tokens[1].token_type, TokenType.COMMENT_MULTI)

    def test_arithmetic_relational_logical_assignment_and_symbols(self):
        source = "+ - * / % ^ ++ -- < <= > >= != == && || ! ; = ( ) { } , ; \" '"
        tokens = self.lexer.tokenize(source)
        types = [t.token_type for t in tokens]

        expected = [
            TokenType.ARITHMETIC_OPERATOR,
            TokenType.ARITHMETIC_OPERATOR,
            TokenType.ARITHMETIC_OPERATOR,
            TokenType.ARITHMETIC_OPERATOR,
            TokenType.ARITHMETIC_OPERATOR,
            TokenType.ARITHMETIC_OPERATOR,
            TokenType.ARITHMETIC_OPERATOR,
            TokenType.ARITHMETIC_OPERATOR,
            TokenType.RELATIONAL_OPERATOR,
            TokenType.RELATIONAL_OPERATOR,
            TokenType.RELATIONAL_OPERATOR,
            TokenType.RELATIONAL_OPERATOR,
            TokenType.RELATIONAL_OPERATOR,
            TokenType.RELATIONAL_OPERATOR,
            TokenType.LOGICAL_OPERATOR,
            TokenType.LOGICAL_OPERATOR,
            TokenType.LOGICAL_OPERATOR,
            TokenType.SYMBOL,
            TokenType.ASSIGNMENT,
            TokenType.SYMBOL,
            TokenType.SYMBOL,
            TokenType.SYMBOL,
            TokenType.SYMBOL,
            TokenType.SYMBOL,
            TokenType.SYMBOL,
            TokenType.SYMBOL,
            TokenType.SYMBOL,
        ]
        self.assertEqual(types, expected)

    def test_longest_match_ignores_whitespace_for_multi_char_operators(self):
        source = "a+\n+;"
        tokens = self.lexer.tokenize(source)
        lexeme_types = [(t.lexeme, t.token_type) for t in tokens]

        self.assertEqual(lexeme_types, [
            ("a", TokenType.IDENTIFIER),
            ("++", TokenType.ARITHMETIC_OPERATOR),
            (";", TokenType.SYMBOL),
        ])

    def test_longest_match_stops_at_statement_terminator(self):
        source = "+\n;+\n+;"
        tokens = self.lexer.tokenize(source)
        lexemes = [t.lexeme for t in tokens]

        self.assertEqual(lexemes, ["+", ";", "++", ";"])

    def test_logical_keywords(self):
        source = "and or not"
        tokens = self.lexer.tokenize(source)
        self.assertEqual([t.token_type for t in tokens], [
            TokenType.LOGICAL_OPERATOR,
            TokenType.LOGICAL_OPERATOR,
            TokenType.LOGICAL_OPERATOR,
        ])

    def test_color_group_mapping(self):
        self.assertEqual(token_color_group(TokenType.INTEGER), 1)
        self.assertEqual(token_color_group(TokenType.REAL), 1)
        self.assertEqual(token_color_group(TokenType.IDENTIFIER), 2)
        self.assertEqual(token_color_group(TokenType.COMMENT_SINGLE), 3)
        self.assertEqual(token_color_group(TokenType.KEYWORD), 4)
        self.assertEqual(token_color_group(TokenType.ARITHMETIC_OPERATOR), 5)
        self.assertEqual(token_color_group(TokenType.RELATIONAL_OPERATOR), 6)
        self.assertEqual(token_color_group(TokenType.LOGICAL_OPERATOR), 6)

    def test_invalid_character_reports_line_and_column(self):
        result = self.lexer.analyze("int main @")
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].line, 1)
        self.assertEqual(result.errors[0].column, 10)
        self.assertEqual(result.errors[0].lexeme, "@")

    def test_malformed_number_reports_error(self):
        result = self.lexer.analyze("12abc")
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Numero mal formado", result.errors[0].message)
        self.assertEqual(result.errors[0].line, 1)
        self.assertEqual(result.errors[0].column, 1)
        self.assertEqual(result.errors[0].lexeme, "12abc")
        self.assertEqual(len(result.tokens), 1)
        self.assertEqual(result.tokens[0].token_type, TokenType.UNKNOWN)

    def test_malformed_decimal_number_consumes_full_lexeme(self):
        result = self.lexer.analyze("32.algo")

        self.assertEqual(len(result.tokens), 1)
        self.assertEqual(result.tokens[0].token_type, TokenType.UNKNOWN)
        self.assertEqual(result.tokens[0].lexeme, "32.algo")

        self.assertEqual(len(result.errors), 1)
        self.assertIn("Numero mal formado", result.errors[0].message)
        self.assertEqual(result.errors[0].line, 1)
        self.assertEqual(result.errors[0].column, 1)
        self.assertEqual(result.errors[0].lexeme, "32.algo")

    def test_unclosed_multiline_comment_reports_error(self):
        result = self.lexer.analyze("/* sin cierre")
        self.assertEqual(len(result.errors), 1)
        self.assertIn("sin cierre", result.errors[0].message)
        self.assertEqual(result.errors[0].line, 1)
        self.assertEqual(result.errors[0].column, 1)

    def test_line_traces_are_created(self):
        result = self.lexer.analyze("int a = 1;\nfloat b = 2.5;")
        self.assertEqual(len(result.line_traces), 2)
        self.assertEqual(result.line_traces[0].line_number, 1)
        self.assertGreater(len(result.line_traces[0].token_summaries), 0)


if __name__ == "__main__":
    unittest.main()
