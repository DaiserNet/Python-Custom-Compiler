# core/lexer.py
from typing import List
from typing import Tuple

from app.core.tokens import LexicalAnalysisResult
from app.core.tokens import LexicalError
from app.core.tokens import LexicalLineTrace
from app.core.tokens import Token
from app.core.tokens import TokenType


class LexicalAnalyzer:
    """Deterministic scanner (DFA-style) for the Chimera language."""

    KEYWORDS = {
        "if",
        "else",
        "end",
        "do",
        "while",
        "switch",
        "case",
        "then",
        "true",
        "false",
        "int",
        "float",
        "bool",
        "main",
        "cin",
        "cout",
    }

    LOGICAL_KEYWORDS = {
        "and",
        "or",
        "not",
    }

    SYMBOLS = {
        "(",
        ")",
        "{",
        "}",
        ",",
        ";",
    }

    MULTI_CHAR_TOKENS = {
        "++": TokenType.ARITHMETIC_OPERATOR,
        "--": TokenType.ARITHMETIC_OPERATOR,
        "<=": TokenType.RELATIONAL_OPERATOR,
        ">=": TokenType.RELATIONAL_OPERATOR,
        "!=": TokenType.RELATIONAL_OPERATOR,
        "==": TokenType.RELATIONAL_OPERATOR,
        "&&": TokenType.LOGICAL_OPERATOR,
        "||": TokenType.LOGICAL_OPERATOR,
    }

    SINGLE_CHAR_TOKENS = {
        "+": TokenType.ARITHMETIC_OPERATOR,
        "-": TokenType.ARITHMETIC_OPERATOR,
        "*": TokenType.ARITHMETIC_OPERATOR,
        "/": TokenType.ARITHMETIC_OPERATOR,
        "%": TokenType.ARITHMETIC_OPERATOR,
        "^": TokenType.ARITHMETIC_OPERATOR,
        "<": TokenType.RELATIONAL_OPERATOR,
        ">": TokenType.RELATIONAL_OPERATOR,
        "!": TokenType.LOGICAL_OPERATOR,
        "=": TokenType.ASSIGNMENT,
    }

    def tokenize(self, source: str, include_whitespace: bool = False) -> List[Token]:
        tokens, _ = self._scan(source, include_whitespace=include_whitespace, collect_errors=False)
        return tokens

    def analyze(self, source: str, include_whitespace: bool = False) -> LexicalAnalysisResult:
        tokens, errors = self._scan(source, include_whitespace=include_whitespace, collect_errors=True)
        line_traces = self._build_line_traces(source, tokens)
        return LexicalAnalysisResult(tokens=tokens, errors=errors, line_traces=line_traces)

    def _scan(self, source: str, include_whitespace: bool, collect_errors: bool) -> Tuple[List[Token], List[LexicalError]]:
        tokens: List[Token] = []
        errors: List[LexicalError] = []
        i = 0
        line = 1
        column = 1
        length = len(source)

        while i < length:
            ch = source[i]
            start = i
            start_line = line
            start_column = column

            if ch.isspace():
                i, line, column = self._consume_whitespace(source, i, line, column)
                if include_whitespace:
                    tokens.append(
                        Token(
                            token_type=TokenType.WHITESPACE,
                            lexeme=source[start:i],
                            start=start,
                            end=i,
                            line=start_line,
                            column=start_column,
                        )
                    )
                continue

            if self._is_identifier_start(ch):
                i, line, column = self._consume_identifier(source, i, line, column)
                lexeme = source[start:i]
                if lexeme in self.KEYWORDS:
                    token_type = TokenType.KEYWORD
                elif lexeme in self.LOGICAL_KEYWORDS:
                    token_type = TokenType.LOGICAL_OPERATOR
                else:
                    token_type = TokenType.IDENTIFIER
                tokens.append(
                    Token(
                        token_type=token_type,
                        lexeme=lexeme,
                        start=start,
                        end=i,
                        line=start_line,
                        column=start_column,
                    )
                )
                continue

            if ch.isdigit():
                i, line, column, is_real, is_malformed = self._consume_number(source, i, line, column)
                
                if is_malformed:
                    # Solo se agrega a la lista de errores, NO a los tokens.
                    if collect_errors:
                        errors.append(
                            LexicalError(
                                message="Número mal formado.",
                                line=start_line,
                                column=start_column,
                                lexeme=source[start:i],
                            )
                        )
                else:
                    token_type = TokenType.REAL if is_real else TokenType.INTEGER
                    tokens.append(
                        Token(
                            token_type=token_type,
                            lexeme=source[start:i],
                            start=start,
                            end=i,
                            line=start_line,
                            column=start_column,
                        )
                    )
                continue

            if ch == "/" and i + 1 < length:
                nxt = source[i + 1]
                if nxt == "/":
                    i, line, column = self._consume_single_line_comment(source, i, line, column)
                    tokens.append(
                        Token(
                            token_type=TokenType.COMMENT_SINGLE,
                            lexeme=source[start:i],
                            start=start,
                            end=i,
                            line=start_line,
                            column=start_column,
                        )
                    )
                    continue
                if nxt == "*":
                    i, line, column, is_closed = self._consume_multi_line_comment(source, i, line, column)
                    tokens.append(
                        Token(
                            token_type=TokenType.COMMENT_MULTI,
                            lexeme=source[start:i],
                            start=start,
                            end=i,
                            line=start_line,
                            column=start_column,
                        )
                    )
                    if collect_errors and not is_closed:
                        errors.append(
                            LexicalError(
                                message="Comentario multilinea sin cierre.",
                                line=start_line,
                                column=start_column,
                                lexeme=source[start:i],
                            )
                        )
                    continue

            multi_operator = self._consume_multi_char_operator_with_gaps(source, i, line, column)
            if multi_operator is not None:
                maybe_multi, token_type, i, line, column = multi_operator
                tokens.append(
                    Token(
                        token_type=token_type,
                        lexeme=maybe_multi,
                        start=start,
                        end=i,
                        line=start_line,
                        column=start_column,
                    )
                )
                continue

            # String literal scanning (only double quotes)
            if ch == '"':
                i, line, column, is_closed = self._consume_string(source, i, line, column)
                if is_closed:
                    tokens.append(
                        Token(
                            token_type=TokenType.STRING,
                            lexeme=source[start:i],
                            start=start,
                            end=i,
                            line=start_line,
                            column=start_column,
                        )
                    )
                else:
                    if collect_errors:
                        errors.append(
                            LexicalError(
                                message="Cadena de texto sin cierre.",
                                line=start_line,
                                column=start_column,
                                lexeme=source[start:i],
                            )
                        )
                continue

            if ch in self.SYMBOLS:
                i, line, column = self._advance_sequence(source, i, line, column, 1)
                tokens.append(
                    Token(
                        token_type=TokenType.SYMBOL,
                        lexeme=ch,
                        start=start,
                        end=i,
                        line=start_line,
                        column=start_column,
                    )
                )
                continue

            if ch in ("&", "|"):
                i, line, column = self._advance_sequence(source, i, line, column, 1)
                # Omitido de la lista de tokens, se reporta como error directo.
                if collect_errors:
                    errors.append(
                        LexicalError(
                            message="Operador logico incompleto: use && o ||.",
                            line=start_line,
                            column=start_column,
                            lexeme=ch,
                        )
                    )
                continue

            token_type = self.SINGLE_CHAR_TOKENS.get(ch)
            if token_type is not None:
                i, line, column = self._advance_sequence(source, i, line, column, 1)
                tokens.append(
                    Token(
                        token_type=token_type,
                        lexeme=ch,
                        start=start,
                        end=i,
                        line=start_line,
                        column=start_column,
                    )
                )
                continue

            # Para cualquier caracter no reconocido
            i, line, column = self._advance_sequence(source, i, line, column, 1)
            # Omitido de la lista de tokens, solo se reporta el error.
            if collect_errors:
                errors.append(
                    LexicalError(
                        message="Caracter invalido o token no reconocido.",
                        line=start_line,
                        column=start_column,
                        lexeme=ch,
                    )
                )

        return tokens, errors

    def _build_line_traces(self, source: str, tokens: List[Token]) -> List[LexicalLineTrace]:
        tokens_by_line = {}
        for token in tokens:
            if token.token_type == TokenType.WHITESPACE:
                continue
            tokens_by_line.setdefault(token.line, []).append(token)

        lines = source.split("\n")
        if not lines:
            lines = [""]

        traces: List[LexicalLineTrace] = []
        for line_number, line_text in enumerate(lines, start=1):
            line_tokens = tokens_by_line.get(line_number, [])
            if line_tokens:
                last_token = line_tokens[-1]
                scanned_up_to_column = last_token.column + len(last_token.lexeme) - 1
            else:
                scanned_up_to_column = 0

            token_summaries = [
                f"{token.lexeme}<{token.token_type.value}>" for token in line_tokens
            ]
            traces.append(
                LexicalLineTrace(
                    line_number=line_number,
                    line_text=line_text,
                    scanned_up_to_column=scanned_up_to_column,
                    token_summaries=token_summaries,
                )
            )
        return traces

    @staticmethod
    def _is_identifier_start(ch: str) -> bool:
        return ch.isalpha()

    @staticmethod
    def _is_identifier_part(ch: str) -> bool:
        return ch.isalnum()

    def _consume_identifier(self, source: str, i: int, line: int, column: int):
        while i < len(source) and self._is_identifier_part(source[i]):
            i, line, column = self._advance_sequence(source, i, line, column, 1)
        return i, line, column

    def _consume_number(self, source: str, i: int, line: int, column: int):
        while i < len(source) and source[i].isdigit():
            i, line, column = self._advance_sequence(source, i, line, column, 1)

        is_real = False
        is_malformed = False
        
        if i < len(source) and source[i] == ".":
            if i + 1 < len(source) and source[i + 1].isdigit():
                is_real = True
                i, line, column = self._advance_sequence(source, i, line, column, 1) # Consumir el '.'
                while i < len(source) and source[i].isdigit():
                    i, line, column = self._advance_sequence(source, i, line, column, 1)
            else:
                # Caso para un número mal formado como "32."
                is_malformed = True
                i, line, column = self._advance_sequence(source, i, line, column, 1) # Consumir el '.'
                
        # Se ha eliminado el bloque "_is_identifier_start" para que no consuma
        # identificadores adjuntos (ej. la palabra "algo" en "32.algo").

        return i, line, column, is_real, is_malformed

    def _consume_multi_char_operator_with_gaps(self, source: str, i: int, line: int, column: int):
        if i >= len(source):
            return None

        first_char = source[i]
        if not any(op[0] == first_char for op in self.MULTI_CHAR_TOKENS):
            return None

        probe_i, probe_line, probe_column = self._advance_sequence(source, i, line, column, 1)

        while probe_i < len(source) and source[probe_i].isspace():
            probe_i, probe_line, probe_column = self._advance_sequence(
                source,
                probe_i,
                probe_line,
                probe_column,
                1,
            )

        if probe_i >= len(source) or source[probe_i] == ";":
            return None

        maybe_multi = first_char + source[probe_i]
        token_type = self.MULTI_CHAR_TOKENS.get(maybe_multi)
        if token_type is None:
            return None

        probe_i, probe_line, probe_column = self._advance_sequence(
            source,
            probe_i,
            probe_line,
            probe_column,
            1,
        )
        return maybe_multi, token_type, probe_i, probe_line, probe_column

    def _consume_single_line_comment(self, source: str, i: int, line: int, column: int):
        i, line, column = self._advance_sequence(source, i, line, column, 2)
        while i < len(source) and source[i] != "\n":
            i, line, column = self._advance_sequence(source, i, line, column, 1)
        return i, line, column

    def _consume_multi_line_comment(self, source: str, i: int, line: int, column: int):
        i, line, column = self._advance_sequence(source, i, line, column, 2)
        is_closed = False
        while i < len(source):
            if source[i] == "*" and i + 1 < len(source) and source[i + 1] == "/":
                i, line, column = self._advance_sequence(source, i, line, column, 2)
                is_closed = True
                break
            i, line, column = self._advance_sequence(source, i, line, column, 1)
        return i, line, column, is_closed

    def _consume_string(self, source: str, i: int, line: int, column: int):
        """Consume a double-quoted string literal."""
        # Skip the opening quote
        i, line, column = self._advance_sequence(source, i, line, column, 1)
        is_closed = False
        while i < len(source):
            if source[i] == '"':
                i, line, column = self._advance_sequence(source, i, line, column, 1)
                is_closed = True
                break
            if source[i] == '\n':
                # Strings cannot span multiple lines
                break
            i, line, column = self._advance_sequence(source, i, line, column, 1)
        return i, line, column, is_closed

    @staticmethod
    def _consume_whitespace(source: str, i: int, line: int, column: int):
        while i < len(source) and source[i].isspace():
            i, line, column = LexicalAnalyzer._advance_sequence(source, i, line, column, 1)
        return i, line, column

    @staticmethod
    def _advance_sequence(source: str, i: int, line: int, column: int, count: int):
        for _ in range(count):
            if i >= len(source):
                break
            if source[i] == "\n":
                line += 1
                column = 1
            else:
                column += 1
            i += 1
        return i, line, column