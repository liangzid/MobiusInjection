"""Ingress-phase prompt defenses for Mobius grafting carriers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol


class IngressGuard(Protocol):
    name: str

    def score(self, text: str) -> float:
        ...

    def detect(self, text: str, threshold: float = 0.5) -> bool:
        ...


@dataclass(frozen=True)
class RegexPromptBoundaryGuard:
    """Lightweight prompt-boundary filter (repositioned trigger-prompt guard)."""

    name: str = "Trigger prompt guard (ingress)"

    def __post_init__(self) -> None:
        patterns = (
            r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
            r"disregard\s+(all\s+)?(previous|prior)",
            r"forget\s+(all\s+)?(previous|prior)\s+instructions",
            r"you\s+are\s+now\s+(in\s+)?(developer|admin|root)\s+mode",
            r"reveal\s+(your\s+)?system\s+prompt",
            r"<\s*/?\s*system\s*>",
            r"do\s+not\s+follow\s+(the\s+)?(user|developer)",
        )
        object.__setattr__(
            self,
            "_patterns",
            tuple(re.compile(pattern, re.IGNORECASE) for pattern in patterns),
        )

    def score(self, text: str) -> float:
        return 1.0 if any(pattern.search(text) for pattern in self._patterns) else 0.0

    def detect(self, text: str, threshold: float = 0.5) -> bool:
        del threshold
        return bool(self.score(text))


class PromptGuard86M:
    """Meta Prompt-Guard-86M indirect-injection scorer."""

    name = "Prompt-Guard-86M (ingress)"

    def __init__(
        self,
        model_id: str = "meta-llama/Prompt-Guard-86M",
        device: str = "cpu",
        chunk_tokens: int = 512,
        threshold: float = 0.5,
    ) -> None:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.model_id = model_id
        self.device = device
        self.chunk_tokens = chunk_tokens
        self.threshold = threshold
        self._torch = torch
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self._model = AutoModelForSequenceClassification.from_pretrained(self.model_id)
        self._model.to(self.device)
        self._model.eval()

    def _chunk_texts(self, text: str) -> list[str]:
        token_ids = self._tokenizer.encode(text, add_special_tokens=False)
        if len(token_ids) <= self.chunk_tokens:
            return [text]
        chunks: list[str] = []
        for start in range(0, len(token_ids), self.chunk_tokens):
            piece = token_ids[start : start + self.chunk_tokens]
            chunks.append(self._tokenizer.decode(piece, skip_special_tokens=True))
        return chunks

    def _indirect_injection_score(self, text: str) -> float:
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.chunk_tokens,
        ).to(self.device)
        with self._torch.no_grad():
            logits = self._model(**inputs).logits
        probabilities = self._torch.nn.functional.softmax(logits, dim=-1)
        return float((probabilities[0, 1] + probabilities[0, 2]).item())

    def score(self, text: str) -> float:
        if not text:
            return 0.0
        return max(self._indirect_injection_score(chunk) for chunk in self._chunk_texts(text))

    def detect(self, text: str, threshold: float | None = None) -> bool:
        cutoff = self.threshold if threshold is None else threshold
        return self.score(text) >= cutoff
