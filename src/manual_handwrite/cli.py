"""Entrada de linha de comando `handwrite`."""

import argparse

from manual_handwrite import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="handwrite",
        description="Gera manuscritos na sua letra, com aspecto de papel escaneado.",
    )
    parser.add_argument("--version", action="version", version=f"handwrite {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
