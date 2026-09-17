"""Safe metadata contracts for local handwriting styles."""

from .stylepack import (
    StylePack,
    StylePackError,
    StyleReference,
    load_manifest,
    load_stylepack,
    load_stylepack_manifest,
    write_manifest,
    write_stylepack,
    write_stylepack_manifest,
)

__all__ = [
    "StylePack",
    "StylePackError",
    "StyleReference",
    "load_manifest",
    "load_stylepack",
    "load_stylepack_manifest",
    "write_stylepack",
    "write_stylepack_manifest",
    "write_manifest",
]
