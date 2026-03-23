"""
CiRA-inspired Labeler for Aerospace Requirements.
Extracts cause-clauses and effect-clauses from causal sentences.
Fully offline – rule-based NLP, no external models required.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ── Connector patterns: split sentence into (cause, connector, effect) ───────
CONNECTORS = [
    # (regex pattern, cause-side, effect-side)
    # "if/when/whenever ... then ..."
    (re.compile(r"^(.*?)\bif\b\s+(.+?)\s*,?\s*then\s+(.+)$", re.IGNORECASE | re.DOTALL),
     "if_then", ["cause"], ["effect"]),

    (re.compile(r"^(.*?)\bwhen\b\s+(.+?)\s*,?\s*then\s+(.+)$", re.IGNORECASE | re.DOTALL),
     "when_then", ["cause"], ["effect"]),

    # "if ... [modal] ..."  (then implied)
    (re.compile(
        r"^(?:.*?)\bif\b\s+(.+?)\s*,\s*((?:(?:the|a|an)\s+)?(?:\w+\s+){0,4}(?:shall|must|will|should|may)\b.+)$",
        re.IGNORECASE | re.DOTALL),
        "if_modal", ["cause"], ["effect"]),

    # "when ... [modal] ..."
    (re.compile(
        r"^(?:.*?)\bwhen\b\s+(.+?)\s*,\s*((?:(?:the|a|an)\s+)?(?:\w+\s+){0,4}(?:shall|must|will|should|may)\b.+)$",
        re.IGNORECASE | re.DOTALL),
        "when_modal", ["cause"], ["effect"]),

    # "in the event that ..."
    (re.compile(
        r"^(?:.*?)\bin\s+the\s+event\s+(?:that\s+)?(.+?)\s*,\s*(.+)$",
        re.IGNORECASE | re.DOTALL),
        "in_event", ["cause"], ["effect"]),

    # "in case of ..."
    (re.compile(
        r"^(?:.*?)\bin\s+case\s+(?:of\s+|that\s+)?(.+?)\s*,\s*(.+)$",
        re.IGNORECASE | re.DOTALL),
        "in_case", ["cause"], ["effect"]),

    # "provided that ..."
    (re.compile(
        r"^(?:.*?)\bprovided\s+that\b\s+(.+?)\s*,\s*(.+)$",
        re.IGNORECASE | re.DOTALL),
        "provided_that", ["cause"], ["effect"]),

    # "given that ..."
    (re.compile(
        r"^(?:.*?)\bgiven\s+that\b\s+(.+?)\s*,\s*(.+)$",
        re.IGNORECASE | re.DOTALL),
        "given_that", ["cause"], ["effect"]),

    # "once X, Y shall"
    (re.compile(
        r"^(?:.*?)\bonce\b\s+(.+?)\s*,\s*((?:(?:the|a|an)\s+)?(?:\w+\s+){0,4}(?:shall|must|will|should|may)\b.+)$",
        re.IGNORECASE | re.DOTALL),
        "once", ["cause"], ["effect"]),

    # "unless X, Y"
    (re.compile(
        r"^(?:.*?)\bunless\b\s+(.+?)\s*,\s*(.+)$",
        re.IGNORECASE | re.DOTALL),
        "unless", ["negated_cause"], ["effect"]),

    # "after X, Y shall"
    (re.compile(
        r"^(?:.*?)\bafter\b\s+(.+?)\s*,\s*((?:(?:the|a|an)\s+)?(?:\w+\s+){0,4}(?:shall|must|will|should).+)$",
        re.IGNORECASE | re.DOTALL),
        "after", ["cause"], ["effect"]),

    # "before X, Y shall"
    (re.compile(
        r"^(?:.*?)\bbefore\b\s+(.+?)\s*,\s*((?:(?:the|a|an)\s+)?(?:\w+\s+){0,4}(?:shall|must|will|should).+)$",
        re.IGNORECASE | re.DOTALL),
        "before", ["precondition"], ["effect"]),

    # "during X, Y shall"
    (re.compile(
        r"^(?:.*?)\bduring\b\s+(.+?)\s*,\s*((?:(?:the|a|an)\s+)?(?:\w+\s+){0,4}(?:shall|must|will|should).+)$",
        re.IGNORECASE | re.DOTALL),
        "during", ["context"], ["effect"]),

    # "whenever X, Y"
    (re.compile(
        r"^(?:.*?)\bwhenever\b\s+(.+?)\s*,?\s*(.+)$",
        re.IGNORECASE | re.DOTALL),
        "whenever", ["cause"], ["effect"]),
]

# ── Logical connectors within a clause ──────────────────────────────────────
AND_PATTERN = re.compile(r"\band\b|\b&\b|,\s*(?=\w)", re.IGNORECASE)
OR_PATTERN  = re.compile(r"\bor\b", re.IGNORECASE)

# ── Negation ─────────────────────────────────────────────────────────────────
NEGATION_PATTERN = re.compile(
    r"\b(not|no|never|without|absent|fail[s]?|failure|fault|loss\s+of|disconnect[ed]*)\b",
    re.IGNORECASE
)


@dataclass
class Event:
    """A single cause or effect event extracted from a requirement."""
    text: str
    event_type: str          # "cause" | "effect" | "negated_cause" | "precondition" | "context"
    negated: bool = False
    sub_events: List["Event"] = field(default_factory=list)
    connector: str = ""      # "AND" | "OR" | "" (single)


@dataclass
class LabeledSentence:
    sentence: str
    connector_type: str
    causes: List[Event]
    effects: List[Event]
    raw_cause_text: str = ""
    raw_effect_text: str = ""


def _split_by_logical(text: str, event_type: str) -> List[Event]:
    """Split a clause into individual events joined by AND/OR."""
    text = text.strip()

    # Try OR first (lower precedence)
    or_parts = [p.strip() for p in OR_PATTERN.split(text) if p.strip()]
    if len(or_parts) > 1:
        events = []
        for part in or_parts:
            and_parts = [p.strip() for p in AND_PATTERN.split(part) if p.strip()]
            if len(and_parts) > 1:
                sub = [Event(a, event_type, bool(NEGATION_PATTERN.search(a))) for a in and_parts]
                events.append(Event(part, event_type, bool(NEGATION_PATTERN.search(part)),
                                    sub_events=sub, connector="AND"))
            else:
                events.append(Event(part, event_type, bool(NEGATION_PATTERN.search(part))))
        # Wrap in a single OR parent
        return [Event(text, event_type, False, sub_events=events, connector="OR")]

    and_parts = [p.strip() for p in AND_PATTERN.split(text) if p.strip()]
    if len(and_parts) > 1:
        events = [Event(a, event_type, bool(NEGATION_PATTERN.search(a))) for a in and_parts]
        return [Event(text, event_type, False, sub_events=events, connector="AND")]

    # Single event
    return [Event(text, event_type, bool(NEGATION_PATTERN.search(text)))]


class RequirementLabeler:
    """
    CiRA Step 2: Labels tokens in a causal sentence as cause / effect.
    Returns a LabeledSentence with structured cause and effect events.
    """

    def label(self, sentence: str) -> Optional[LabeledSentence]:
        sentence = sentence.strip()

        for pattern, conn_type, cause_roles, effect_roles in CONNECTORS:
            m = pattern.match(sentence)
            if not m:
                continue

            groups = m.groups()

            if conn_type == "if_then":
                # groups: (preamble?, cause, effect)
                cause_text  = groups[1].strip() if len(groups) == 3 else groups[0].strip()
                effect_text = groups[2].strip() if len(groups) == 3 else groups[1].strip()
            elif conn_type in ("if_modal", "when_modal", "whenever",
                               "in_event", "in_case", "provided_that",
                               "given_that", "once", "unless", "after",
                               "before", "during", "when_then"):
                cause_text  = groups[0].strip()
                effect_text = groups[1].strip()
            else:
                cause_text  = groups[0].strip()
                effect_text = groups[1].strip()

            role = cause_roles[0]   # "cause" | "negated_cause" | "precondition" | "context"
            causes  = _split_by_logical(cause_text, role)
            effects = _split_by_logical(effect_text, "effect")

            return LabeledSentence(
                sentence=sentence,
                connector_type=conn_type,
                causes=causes,
                effects=effects,
                raw_cause_text=cause_text,
                raw_effect_text=effect_text,
            )

        # Fallback: treat entire sentence as an undivided causal statement
        return LabeledSentence(
            sentence=sentence,
            connector_type="implicit",
            causes=[Event(sentence, "cause", bool(NEGATION_PATTERN.search(sentence)))],
            effects=[Event("system shall respond as specified", "effect", False)],
            raw_cause_text=sentence,
            raw_effect_text="system shall respond as specified",
        )
