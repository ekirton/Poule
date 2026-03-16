"""Output formatting for CLI search results."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wily_rooster.models.responses import LemmaDetail, Module, SearchResult


def format_search_results(
    results: list[SearchResult], *, json_mode: bool
) -> str:
    if json_mode:
        return json.dumps([asdict(r) for r in results])

    if not results:
        return ""

    blocks = []
    for r in results:
        block = (
            f"{r.name}  {r.kind}  {r.score:.4f}\n"
            f"  {r.statement}\n"
            f"  module: {r.module}"
        )
        blocks.append(block)
    return "\n\n".join(blocks)


def format_lemma_detail(detail: LemmaDetail, *, json_mode: bool) -> str:
    if json_mode:
        return json.dumps(asdict(detail))

    symbols_str = ", ".join(detail.symbols) if detail.symbols else ""
    return (
        f"{detail.name}  ({detail.kind})\n"
        f"  {detail.statement}\n"
        f"  module:       {detail.module}\n"
        f"  dependencies: {len(detail.dependencies) if detail.dependencies else 0}\n"
        f"  dependents:   {len(detail.dependents) if detail.dependents else 0}\n"
        f"  symbols:      {symbols_str}\n"
        f"  node_count:   {detail.node_count}"
    )


def format_modules(modules: list[Module], *, json_mode: bool) -> str:
    if json_mode:
        return json.dumps([asdict(m) for m in modules])

    if not modules:
        return ""

    lines = []
    for m in modules:
        lines.append(f"{m.name}  ({m.decl_count} declarations)")
    return "\n".join(lines)
