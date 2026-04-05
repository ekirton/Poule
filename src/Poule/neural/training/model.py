"""Tactic family classifier for neural tactic prediction.

CodeBERT encoder with mean pooling and a linear classification head,
producing logits over a fixed set of tactic families.

Requires: torch, transformers (training-only dependencies).
"""

from __future__ import annotations

from typing import Any

import torch
import torch.nn as nn
from transformers import AutoModel


def _layer_indices(num_hidden_layers: int) -> list[int]:
    """Compute evenly spaced layer indices for layer dropping.

    Selects ``num_hidden_layers`` layers from a 12-layer source at
    evenly spaced positions: ``[i * 12 // num_hidden_layers for i ...]``.
    """
    return [i * 12 // num_hidden_layers for i in range(num_hidden_layers)]


class TacticClassifier(nn.Module):
    """CodeBERT encoder with mean pooling and classification head.

    Architecture: CodeBERT -> mean pooling -> Linear -> [B, num_classes] logits.
    """

    def __init__(
        self,
        model_name: str = "microsoft/codebert-base",
        num_classes: int = 1,
        vocab_size: int | None = None,
        num_hidden_layers: int = 6,
        embedding_dim: int = 128,
    ):
        super().__init__()
        self.num_classes = num_classes
        encoder = AutoModel.from_pretrained(model_name)

        # Layer dropping: select a subset of transformer layers
        if num_hidden_layers < 12:
            indices = _layer_indices(num_hidden_layers)
            new_layers = torch.nn.ModuleList(
                [encoder.encoder.layer[i] for i in indices]
            )
            encoder.encoder.layer = new_layers
            encoder.config.num_hidden_layers = num_hidden_layers

        self.encoder = encoder
        hidden_size = self.encoder.config.hidden_size

        # Replace embedding layer if a custom vocab size is provided
        if vocab_size is not None:
            old_embeddings = self.encoder.embeddings.word_embeddings
            new_embeddings = nn.Embedding(vocab_size, embedding_dim)
            # Initialize randomly (σ=0.02), then copy overlapping tokens
            nn.init.normal_(new_embeddings.weight, mean=0.0, std=0.02)
            overlap = min(vocab_size, old_embeddings.num_embeddings)
            copy_dim = min(embedding_dim, old_embeddings.embedding_dim)
            with torch.no_grad():
                new_embeddings.weight[:overlap, :copy_dim] = (
                    old_embeddings.weight[:overlap, :copy_dim]
                )
            self.encoder.embeddings.word_embeddings = new_embeddings
            # Free the old embedding tensor immediately
            del old_embeddings
            import gc; gc.collect()

        # Embedding projection for factorized embeddings (ALBERT-style)
        if embedding_dim < hidden_size:
            self.embedding_projection = nn.Linear(
                embedding_dim, hidden_size, bias=False,
            )
        else:
            self.embedding_projection = None

        self.classifier = nn.Linear(hidden_size, num_classes)

    @classmethod
    def from_checkpoint(cls, checkpoint: dict) -> "TacticClassifier":
        """Instantiate a TacticClassifier from a checkpoint dict.

        Builds the encoder from a RoBERTa config (no network access),
        infers vocab_size from the embedding weight shape, reads
        num_hidden_layers from the checkpoint (defaults to 12 for
        backward compatibility), and loads weights with strict=False
        to tolerate missing keys (e.g. pooler weights absent from
        MLX-converted checkpoints).
        """
        from transformers import RobertaConfig, RobertaModel

        state_dict = checkpoint["model_state_dict"]
        num_classes = checkpoint["num_classes"]
        num_hidden_layers = checkpoint.get("num_hidden_layers", 12)
        embedding_dim = checkpoint.get("embedding_dim", 768)

        emb_key = "encoder.embeddings.word_embeddings.weight"
        vocab_size = state_dict[emb_key].shape[0] if emb_key in state_dict else None

        hidden_size = 768
        config = RobertaConfig(
            vocab_size=vocab_size or 50265,
            hidden_size=hidden_size,
            num_hidden_layers=num_hidden_layers,
            num_attention_heads=12,
            intermediate_size=3072,
            max_position_embeddings=514,
            type_vocab_size=1,
            pad_token_id=1,
            bos_token_id=0,
            eos_token_id=2,
        )
        model = cls.__new__(cls)
        nn.Module.__init__(model)
        model.num_classes = num_classes
        model.encoder = RobertaModel(config)

        # Embedding factorization: resize embedding and add projection
        if embedding_dim < hidden_size:
            if vocab_size is not None:
                model.encoder.embeddings.word_embeddings = nn.Embedding(
                    vocab_size, embedding_dim,
                )
            model.embedding_projection = nn.Linear(
                embedding_dim, hidden_size, bias=False,
            )
        else:
            model.embedding_projection = None

        model.classifier = nn.Linear(hidden_size, num_classes)

        model.load_state_dict(state_dict, strict=False)
        return model

    @property
    def label_map(self) -> dict[str, int] | None:
        """Return the label map if one was saved, else None."""
        return getattr(self, "_label_map", None)

    @label_map.setter
    def label_map(self, mapping: dict[str, int]) -> None:
        self._label_map = mapping

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        """Classify proof states into tactic families.

        Args:
            input_ids: [B, seq_len] token IDs.
            attention_mask: [B, seq_len] attention mask.

        Returns:
            [B, num_classes] unnormalized logits.
        """
        # Apply embedding projection for factorized embeddings
        if self.embedding_projection is not None:
            word_embs = self.encoder.embeddings.word_embeddings(input_ids)
            projected = self.embedding_projection(word_embs)
            # Pass projected embeddings via inputs_embeds; the encoder
            # adds position embeddings and layer norm internally.
            outputs = self.encoder(
                inputs_embeds=projected, attention_mask=attention_mask,
            )
        else:
            outputs = self.encoder(
                input_ids=input_ids, attention_mask=attention_mask,
            )
        token_embs = outputs.last_hidden_state  # [B, seq_len, dim]

        # Mean pooling over non-padding tokens
        mask = attention_mask.unsqueeze(-1).float()
        summed = (token_embs * mask).sum(dim=1)
        counts = mask.sum(dim=1).clamp(min=1e-9)
        pooled = summed / counts  # [B, dim]

        return self.classifier(pooled)

    def save_checkpoint(
        self,
        path: str,
        label_map: dict[str, int],
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Save model weights, num_classes, and label_map to a checkpoint file.

        Args:
            path: Destination file path.
            label_map: Mapping from tactic family name to class index.
            extra: Optional additional metadata to include in the checkpoint.
        """
        emb_dim = self.encoder.embeddings.word_embeddings.weight.shape[1]
        checkpoint: dict[str, Any] = {
            "model_state_dict": self.state_dict(),
            "num_classes": self.num_classes,
            "num_hidden_layers": self.encoder.config.num_hidden_layers,
            "embedding_dim": emb_dim,
            "label_map": label_map,
        }
        if extra:
            checkpoint.update(extra)
        torch.save(checkpoint, path)
