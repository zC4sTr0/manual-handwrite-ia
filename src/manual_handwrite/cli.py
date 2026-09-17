"""Entrada de linha de comando `handwrite`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from manual_handwrite import __version__

_VERSION = f"handwrite {__version__}"


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser while retaining the original version flag."""
    parser = argparse.ArgumentParser(
        prog="handwrite",
        description="Gera manuscritos na sua letra, com aspecto de papel escaneado.",
    )
    parser.add_argument("--version", action="version", version=_VERSION)
    commands = parser.add_subparsers(dest="command")

    scan_parser = commands.add_parser(
        "scanify", help="aplica um preset de aparência escaneada a uma imagem"
    )
    scan_parser.add_argument("input", type=Path, help="imagem de entrada")
    scan_parser.add_argument(
        "--preset", default="scanner-escritorio", help="preset do efeito de scan"
    )
    scan_parser.add_argument("--seed", type=int, default=0, help="semente determinística")
    scan_parser.add_argument(
        "--out", "--output", dest="out", required=True, type=Path, help="imagem de saída"
    )
    scan_parser.add_argument("--version", action="version", version=_VERSION)

    coverage_parser = commands.add_parser(
        "coverage", help="analisa a cobertura de um arquivo Python"
    )
    coverage_parser.add_argument("input", type=Path, help="arquivo Python de entrada")
    coverage_parser.add_argument(
        "--out", "--output", dest="out", required=True, type=Path, help="relatório JSON"
    )
    coverage_parser.add_argument("--version", action="version", version=_VERSION)

    source_pair_parser = commands.add_parser(
        "source-pair", help="ingere um par imagem/source.py como dados GOLD"
    )
    source_pair_parser.add_argument("image", type=Path, help="imagem da página")
    source_pair_parser.add_argument("source", type=Path, help="arquivo source.py correspondente")
    source_pair_parser.add_argument(
        "regions", type=Path, help="JSON com regions (ou line_regions) e texts"
    )
    source_pair_parser.add_argument(
        "--out", "--output", dest="out", required=True, type=Path, help="manifest JSONL"
    )
    source_pair_parser.add_argument(
        "--owner-consent",
        action="store_true",
        required=True,
        help="confirma que as amostras pertencem ao proprietário",
    )
    source_pair_parser.add_argument("--version", action="version", version=_VERSION)
    return parser


def _run_scanify(args: argparse.Namespace) -> None:
    from PIL import Image

    from manual_handwrite.export import export_image
    from manual_handwrite.scan import scanify

    with Image.open(args.input) as source:
        result = scanify(source, seed=args.seed, preset=args.preset)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    suffix = args.out.suffix.lower()
    if suffix in {".png", ".pdf"}:
        export_image(result, args.out)
    elif suffix in {".jpg", ".jpeg"}:
        result.save(args.out, format="JPEG", comment=b"generator=manual-handwrite-ia")
    else:
        raise ValueError("output format must be .png, .jpg, .jpeg, or .pdf")


def _run_coverage(args: argparse.Namespace) -> None:
    from manual_handwrite.coverage import analyze_text

    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = analyze_text(args.input.read_text(encoding="utf-8"))
    args.out.write_text(
        json.dumps(report.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _read_source_pair_regions(path: Path) -> tuple[list[object], list[str | None]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        regions = payload.get("regions", payload.get("line_regions"))
        texts = payload.get("texts")
        if not isinstance(regions, list) or not isinstance(texts, list):
            raise ValueError("regions JSON must contain list regions and texts")
        return regions, texts
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        try:
            return [item["region"] for item in payload], [item.get("text") for item in payload]
        except KeyError as exc:
            raise ValueError("regions JSON entries must contain region") from exc
    raise ValueError("regions JSON must be an object or list of entries")


def _run_source_pair(args: argparse.Namespace) -> None:
    from manual_handwrite.data import write_manifest
    from manual_handwrite.data.source_pair import ingest_source_pair

    regions, texts = _read_source_pair_regions(args.regions)
    entries = ingest_source_pair(
        args.image,
        args.source,
        regions,
        texts,
        owner_consent=args.owner_consent,
    )
    write_manifest(args.out, entries)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "scanify":
        _run_scanify(args)
    elif args.command == "coverage":
        _run_coverage(args)
    elif args.command == "source-pair":
        _run_source_pair(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
