"""Métricas determinísticas de cobertura do corpus manuscrito."""

from __future__ import annotations

import io
import tokenize
from collections import Counter
from dataclasses import dataclass

CORE_TOKENS = frozenset(
    [
        "print",
        "input",
        "int",
        "float",
        "str",
        "if",
        "elif",
        "else",
        "for",
        "while",
        "range",
        "len",
        "def",
        "return",
        "True",
        "False",
        "None",
        "list",
        "dict",
        "tuple",
        "set",
        "enumerate",
    ]
)
CORE_OPERATORS = frozenset(
    [
        ":",
        ";",
        ",",
        ".",
        "_",
        "=",
        "==",
        "!=",
        "<",
        ">",
        "<=",
        ">=",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        "'",
        '"',
        "#",
        "\\",
        "+",
        "-",
        "*",
        "/",
        "%",
    ]
)


@dataclass(frozen=True)
class CoverageReport:
    characters: Counter[str]
    tokens: Counter[str]
    operators: Counter[str]
    missing_tokens: tuple[str, ...]
    missing_operators: tuple[str, ...]

    @property
    def observed_characters(self) -> frozenset[str]:
        return frozenset(self.characters)

    def as_dict(self) -> dict[str, object]:
        return {
            "characters": dict(sorted(self.characters.items())),
            "tokens": dict(sorted(self.tokens.items())),
            "operators": dict(sorted(self.operators.items())),
            "missing_tokens": list(self.missing_tokens),
            "missing_operators": list(self.missing_operators),
        }


def analyze_text(text: str) -> CoverageReport:
    """Conta cobertura sem corrigir o texto nem inferir tokens ausentes."""
    characters = Counter(text)
    tokens: Counter[str] = Counter()
    operators: Counter[str] = Counter()
    try:
        stream = tokenize.generate_tokens(io.StringIO(text).readline)
        for token in stream:
            if token.type in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING):
                tokens[token.string] += 1
            elif token.type == tokenize.OP:
                operators[token.string] += 1
    except (IndentationError, tokenize.TokenError):
        # Cobertura de caracteres continua útil para texto em edição.
        pass
    return CoverageReport(
        characters=characters,
        tokens=tokens,
        operators=operators,
        missing_tokens=tuple(sorted(CORE_TOKENS - tokens.keys())),
        missing_operators=tuple(sorted(CORE_OPERATORS - operators.keys())),
    )
