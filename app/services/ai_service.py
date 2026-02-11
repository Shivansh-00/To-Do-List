from __future__ import annotations

import math
import re
from datetime import datetime, timedelta

from app.schemas import Task

KEYWORD_RE = re.compile(r"\b[a-zA-Z]{4,}\b")


class AIService:
    """Lightweight heuristics that mimic AI endpoints.

    Swap these methods with model calls once model serving is available.
    """

    def summarize(self, description: str) -> str:
        if len(description) <= 140:
            return description
        return description[:137].rstrip() + "..."

    def extract_keywords(self, text: str, limit: int = 5) -> list[str]:
        counts: dict[str, int] = {}
        for token in KEYWORD_RE.findall(text.lower()):
            counts[token] = counts.get(token, 0) + 1
        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        return [word for word, _ in ranked[:limit]]

    def generate_subtasks(self, task: Task) -> list[str]:
        seeds = [
            "Define acceptance criteria",
            "Break work into 30-minute focus blocks",
            "Schedule first execution block",
            "Review and refine output",
        ]
        if task.description:
            seeds[0] = f"Clarify: {self.summarize(task.description)}"
        return seeds

    def estimate_effort(self, task: Task) -> tuple[int, float]:
        text = " ".join(filter(None, [task.title, task.description or ""]))
        complexity = max(1, len(self.extract_keywords(text, limit=10)))
        minutes = min(8 * 60, 20 + complexity * 18)
        confidence = max(0.35, min(0.92, 1.0 - (1 / (complexity + 2))))
        return minutes, round(confidence, 3)

    def predict_deadline(self, task: Task) -> datetime | None:
        if task.due_at:
            return task.due_at
        minutes, _ = self.estimate_effort(task)
        return datetime.utcnow() + timedelta(minutes=math.ceil(minutes * 1.15))
