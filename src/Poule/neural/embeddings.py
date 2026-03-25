"""Embedding write and read paths for the neural channel."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import numpy as np

from Poule.neural.index import EmbeddingIndex

logger = logging.getLogger(__name__)


def compute_embeddings(db_path: Path, encoder) -> None:
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("SELECT id, statement FROM declarations ORDER BY id").fetchall()

    ids = [r[0] for r in rows]
    statements = [r[1] for r in rows]

    # Encode in batches of 64
    all_vectors = []
    for i in range(0, len(statements), 64):
        batch = statements[i : i + 64]
        vectors = encoder.encode_batch(batch)
        all_vectors.extend(vectors)

    # Insert embeddings
    for decl_id, vec in zip(ids, all_vectors):
        blob = vec.astype(np.float32).tobytes()
        conn.execute("INSERT INTO embeddings (decl_id, vector) VALUES (?, ?)", (decl_id, blob))

    # Write model hash
    conn.execute(
        "INSERT OR REPLACE INTO index_meta (key, value) VALUES ('neural_model_hash', ?)",
        (encoder.model_hash(),),
    )
    conn.commit()
    conn.close()


def load_embeddings(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT decl_id, vector FROM embeddings ORDER BY decl_id").fetchall()
    except sqlite3.OperationalError:
        conn.close()
        return (None, None)

    conn.close()

    if not rows:
        return (None, None)

    id_map = np.array([r[0] for r in rows], dtype=np.int64)
    matrix = np.stack(
        [np.frombuffer(r[1], dtype=np.float32) for r in rows]
    )
    return matrix, id_map


def _faiss_sidecar_path(db_path: Path) -> Path:
    """Return the FAISS sidecar path for a given database path."""
    return db_path.with_suffix(".faiss")


def build_faiss_index(db_path: Path) -> Path | None:
    """Read embeddings from SQLite and write a FAISS sidecar file.

    Returns the sidecar path, or None if no embeddings exist.
    """
    result = load_embeddings(db_path)
    if result[0] is None:
        return None
    matrix, id_map = result

    index = EmbeddingIndex.build(matrix, id_map)
    faiss_path = _faiss_sidecar_path(db_path)
    index.save(faiss_path)
    return faiss_path


def load_faiss_index(db_path: Path) -> EmbeddingIndex | None:
    """Load embedding index from FAISS sidecar, falling back to SQLite.

    If the sidecar exists, loads from it directly. If the sidecar is
    missing but SQLite embeddings exist, builds the sidecar and returns
    the index. Returns None if no embeddings exist.
    """
    faiss_path = _faiss_sidecar_path(db_path)
    if faiss_path.exists():
        return EmbeddingIndex.from_file(faiss_path)

    # Fallback: build from SQLite
    result = load_embeddings(db_path)
    if result[0] is None:
        return None
    matrix, id_map = result

    index = EmbeddingIndex.build(matrix, id_map)
    try:
        index.save(faiss_path)
    except OSError:
        logger.warning("Failed to write FAISS sidecar to %s", faiss_path)
    return index
