from dataclasses import dataclass
from enum import Enum
from typing import List
from typing import Optional


class TokenType(str, Enum):
    INTEGER = "INTEGER"
    REAL = "REAL"
    IDENTIFIER = "IDENTIFIER"
    KEYWORD = "KEYWORD"
    COMMENT_SINGLE = "COMMENT_SINGLE"
    COMMENT_MULTI = "COMMENT_MULTI"
    ARITHMETIC_OPERATOR = "ARITHMETIC_OPERATOR"
    RELATIONAL_OPERATOR = "RELATIONAL_OPERATOR"
    LOGICAL_OPERATOR = "LOGICAL_OPERATOR"
    SYMBOL = "SYMBOL"
    ASSIGNMENT = "ASSIGNMENT"
    STRING = "STRING"
    WHITESPACE = "WHITESPACE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Token:
    token_type: TokenType
    lexeme: str
    start: int
    end: int
    line: int
    column: int


@dataclass(frozen=True)
class LexicalError:
    message: str
    line: int
    column: int
    lexeme: str


@dataclass(frozen=True)
class LexicalLineTrace:
    line_number: int
    line_text: str
    scanned_up_to_column: int
    token_summaries: List[str]


@dataclass
class LexicalAnalysisResult:
    tokens: List[Token]
    errors: List[LexicalError]
    line_traces: List[LexicalLineTrace]


def token_color_group(token_type: TokenType) -> Optional[int]:
    """Return the required color group for a token type.

    Color groups are defined by the project requirements:
    1: integers and reals
    2: identifiers
    3: comments
    4: reserved words
    5: arithmetic operators
    6: relational and logical operators
    """
    if token_type in (TokenType.INTEGER, TokenType.REAL):
        return 1
    if token_type == TokenType.IDENTIFIER:
        return 2
    if token_type in (TokenType.COMMENT_SINGLE, TokenType.COMMENT_MULTI):
        return 3
    if token_type == TokenType.KEYWORD:
        return 4
    if token_type == TokenType.ARITHMETIC_OPERATOR:
        return 5
    if token_type in (TokenType.RELATIONAL_OPERATOR, TokenType.LOGICAL_OPERATOR):
        return 6
    return None
