"""
CiRA Engine – Aerospace Test Case Generation.
Offline, rule-based pipeline inspired by the CiRA initiative
(JulianFrattini/cira on GitHub).
"""

from .classifier import CausalityClassifier, ClassificationResult
from .labeler import RequirementLabeler, LabeledSentence, Event
from .graph import CEGBuilder, CauseEffectGraph, CEGNode, CEGEdge
from .testcase_generator import TestCaseGenerator, TestCase, TestStep
from .aerospace_domain import (
    AEROSPACE_CATEGORIES,
    STANDARDS,
    SAMPLE_REQUIREMENTS,
    TEST_LEVELS,
    TEST_TYPES,
    PRIORITY_COLORS,
    TEST_TYPE_ICONS,
    DAL_MAP,
)

__all__ = [
    "CausalityClassifier", "ClassificationResult",
    "RequirementLabeler", "LabeledSentence", "Event",
    "CEGBuilder", "CauseEffectGraph", "CEGNode", "CEGEdge",
    "TestCaseGenerator", "TestCase", "TestStep",
    "AEROSPACE_CATEGORIES", "STANDARDS", "SAMPLE_REQUIREMENTS",
    "TEST_LEVELS", "TEST_TYPES", "PRIORITY_COLORS",
    "TEST_TYPE_ICONS", "DAL_MAP",
]
