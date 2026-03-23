"""
CiRA-inspired Causality Classifier for Aerospace Requirements.
Detects if a natural-language requirement sentence contains causal relationships.
Fully offline – no external API or model download required.
"""

import re
from dataclasses import dataclass
from typing import List, Tuple


# ── Causal-keyword patterns (mirrors CiRA's conditional detection) ──────────
CAUSAL_PATTERNS: List[Tuple[str, float]] = [
    # High-confidence conditionals
    (r"\bif\b.{2,}\bthen\b", 1.0),
    (r"\bwhen\b.{2,}\bthen\b", 1.0),
    (r"\bwhenever\b", 0.95),
    (r"\bin\s+the\s+event\s+(that|of)\b", 0.95),
    (r"\bin\s+case\s+(of|that)\b", 0.90),
    (r"\bprovided\s+that\b", 0.90),
    (r"\bgiven\s+that\b", 0.85),
    (r"\bshould\b.{2,}\bthen\b", 0.85),
    (r"\bonce\b.{2,}(shall|must|will|should)\b", 0.85),
    (r"\bif\b.{2,}(shall|must|will|should)\b", 0.90),
    (r"\bwhen\b.{2,}(shall|must|will|should)\b", 0.88),
    (r"\bafter\b.{2,}(shall|must|will|should)\b", 0.80),
    (r"\bbefore\b.{2,}(shall|must|will|should)\b", 0.80),
    (r"\bduring\b.{2,}(shall|must|will|should)\b", 0.78),
    (r"\bunless\b", 0.85),
    (r"\buntil\b.{2,}(shall|must|will|should)\b", 0.75),
    (r"\bwhile\b.{2,}(shall|must|will|should)\b", 0.75),
    (r"\b(triggers?|causes?|results?\s+in|leads?\s+to)\b", 0.80),
    (r"\b(activates?|enables?|disables?|inhibits?)\b", 0.70),
    (r"\b(exceeds?|falls?\s+below|drops?\s+below|rises?\s+above)\b", 0.72),
    # Aerospace-specific threshold patterns
    (r"\b(threshold|limit|boundary|envelope)\b.{2,}(shall|must|will)\b", 0.78),
    (r"\b(fault|failure|anomaly|error)\b.{2,}(shall|must|will|trigger)\b", 0.82),
    (r"\b(mode|state)\b.{2,}(transition|change|switch)\b", 0.80),
]

# Keywords that suggest a sentence is NOT a simple data/info statement
REQUIREMENT_KEYWORDS = re.compile(
    r"\b(shall|must|will|should|may|can|require[sd]?|ensure[sd]?|provide[sd]?|"
    r"perform[s]?|initiate[sd]?|activate[sd]?|detect[s]?|monitor[s]?|protect[s]?|"
    r"alert[s]?|display[s]?|transmit[s]?|receive[s]?|compute[s]?)\b",
    re.IGNORECASE,
)


@dataclass
class ClassificationResult:
    sentence: str
    is_causal: bool
    confidence: float
    matched_pattern: str


class CausalityClassifier:
    """Rule-based causality classifier (CiRA Step 1 – offline)."""

    def __init__(self, threshold: float = 0.65):
        self.threshold = threshold
        self._compiled = [
            (re.compile(p, re.IGNORECASE), score)
            for p, score in CAUSAL_PATTERNS
        ]

    def classify(self, sentence: str) -> ClassificationResult:
        sentence = sentence.strip()
        if not sentence:
            return ClassificationResult(sentence, False, 0.0, "")

        best_score = 0.0
        best_pattern = ""

        for pattern, score in self._compiled:
            if pattern.search(sentence):
                if score > best_score:
                    best_score = score
                    best_pattern = pattern.pattern

        # Boost if the sentence also contains a requirement keyword
        if best_score > 0 and REQUIREMENT_KEYWORDS.search(sentence):
            best_score = min(1.0, best_score + 0.05)

        is_causal = best_score >= self.threshold
        return ClassificationResult(sentence, is_causal, best_score, best_pattern)

    def classify_batch(self, sentences: List[str]) -> List[ClassificationResult]:
        return [self.classify(s) for s in sentences]
