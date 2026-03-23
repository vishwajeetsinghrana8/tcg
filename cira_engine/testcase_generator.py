"""
CiRA-inspired Test Case Generator (Step 4).
Derives a minimal covering test suite from a CauseEffectGraph.
Enriches output with aerospace-specific metadata.
"""

import itertools
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .graph import CauseEffectGraph, CEGNode, CEGBuilder
from .labeler import LabeledSentence
from .aerospace_domain import DAL_MAP


@dataclass
class TestStep:
    step_number: int
    action: str
    expected_result: str


@dataclass
class TestCase:
    tc_id: str
    title: str
    requirement: str
    preconditions: str
    test_type: str             # Functional | Boundary | Negative | Stress | Safety | Regression
    test_level: str            # Unit | Integration | System | Acceptance
    category: str              # Avionics | Flight Control | Navigation | ...
    dal_level: str             # DAL-A … DAL-E
    priority: str
    standard_ref: str          # DO-178C 6.4.4, ARP4754A, …
    cause_configuration: Dict[str, bool]   # variable → True/False
    effect_expected: Dict[str, bool]       # variable → True/False
    steps: List[TestStep] = field(default_factory=list)
    notes: str = ""
    traceability_id: str = ""  # REQ-xxxx


def _leaf_label(node: CEGNode) -> str:
    """Clean short label for a leaf cause node."""
    t = node.label.strip().rstrip(".,;")
    # Truncate and capitalise
    return (t[:80] + "…") if len(t) > 80 else t


def _effect_label(node: CEGNode) -> str:
    t = node.label.strip().rstrip(".,;")
    return (t[:80] + "…") if len(t) > 80 else t


class TestCaseGenerator:
    """
    CiRA Step 4: Generate a minimal test suite covering all cause-effect
    combinations.  Each cause variable is Boolean (True = condition holds,
    False = condition does NOT hold).
    """

    def __init__(self):
        self.builder = CEGBuilder()

    # ── Public API ────────────────────────────────────────────────────────────

    def generate(
        self,
        labeled: LabeledSentence,
        category: str,
        dal_level: str,
        test_level: str,
        standard_refs: List[str],
        req_id: str = "REQ-001",
    ) -> List[TestCase]:

        graph = self.builder.build(labeled)
        leaf_causes = self.builder.get_leaf_causes(graph)
        effect_nodes = [graph.nodes[eid] for eid in graph.effect_ids if eid in graph.nodes]

        if not leaf_causes:
            leaf_causes = [CEGNode("C_fallback", labeled.raw_cause_text, "cause")]
        if not effect_nodes:
            effect_nodes = [CEGNode("E_fallback", labeled.raw_effect_text, "effect")]

        dal_info   = DAL_MAP.get(dal_level, DAL_MAP["DAL-C"])
        std_ref    = " / ".join(standard_refs) if standard_refs else "DO-178C"
        connector  = labeled.connector_type

        test_cases: List[TestCase] = []

        # ── Determine which Boolean combos to cover ───────────────────────────
        combos = self._minimal_combinations(leaf_causes, connector)

        for idx, combo in enumerate(combos, start=1):
            # Evaluate which effects should be True / False for this combo
            active = all(v for v in combo.values())
            effect_config = {_effect_label(e): active for e in effect_nodes}

            tc_type = self._infer_test_type(combo, idx, len(combos))
            tc_id   = f"TC-{req_id.replace('REQ-', '')}-{idx:03d}"
            title   = self._make_title(combo, effect_config, tc_type)

            steps = self._build_steps(combo, effect_config, labeled, tc_type)
            notes = self._build_notes(dal_level, tc_type, connector)

            tc = TestCase(
                tc_id=tc_id,
                title=title,
                requirement=labeled.sentence,
                preconditions=self._build_preconditions(category, dal_level),
                test_type=tc_type,
                test_level=test_level,
                category=category,
                dal_level=dal_level,
                priority=dal_info["priority"],
                standard_ref=std_ref,
                cause_configuration=combo,
                effect_expected=effect_config,
                steps=steps,
                notes=notes,
                traceability_id=req_id,
            )
            test_cases.append(tc)

        # ── Add boundary / negative / safety variants ─────────────────────────
        extras = self._add_supplemental_tests(
            leaf_causes, effect_nodes, labeled, category,
            dal_level, test_level, std_ref, req_id,
            base_count=len(test_cases),
        )
        test_cases.extend(extras)

        return test_cases

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _minimal_combinations(
        self, causes: List[CEGNode], connector: str
    ) -> List[Dict[str, bool]]:
        """
        Generate minimal set of Boolean combinations to achieve MC/DC-style
        coverage (each variable flipped independently) as required by DO-178C.
        """
        labels = [_leaf_label(c) for c in causes]
        combos: List[Dict[str, bool]] = []

        if len(labels) == 1:
            combos.append({labels[0]: True})
            combos.append({labels[0]: False})
            return combos

        # All-True baseline
        all_true  = {l: True  for l in labels}
        all_false = {l: False for l in labels}
        combos.append(all_true)
        combos.append(all_false)

        # MC/DC – flip each variable while others stay True
        for i, lbl in enumerate(labels):
            variant = {l: (False if l == lbl else True) for l in labels}
            if variant not in combos:
                combos.append(variant)

        return combos

    def _infer_test_type(self, combo: Dict[str, bool], idx: int, total: int) -> str:
        vals = list(combo.values())
        if all(vals):
            return "Functional"
        if not any(vals):
            return "Negative"
        if idx == total:
            return "Safety"
        return "Boundary"

    def _make_title(
        self,
        cause_cfg: Dict[str, bool],
        effect_cfg: Dict[str, bool],
        tc_type: str,
    ) -> str:
        active_causes = [k for k, v in cause_cfg.items() if v]
        inactive_causes = [k for k, v in cause_cfg.items() if not v]
        active_effects = [k for k, v in effect_cfg.items() if v]

        if tc_type == "Functional":
            return f"[{tc_type}] All causes active → effects triggered"
        if tc_type == "Negative":
            return f"[{tc_type}] No causes active → effects NOT triggered"
        if inactive_causes:
            return f"[{tc_type}] Partial causes – {', '.join(inactive_causes[:2])} inactive"
        return f"[{tc_type}] Mixed cause state – verify effect response"

    def _build_steps(
        self,
        cause_cfg: Dict[str, bool],
        effect_cfg: Dict[str, bool],
        labeled: LabeledSentence,
        tc_type: str,
    ) -> List[TestStep]:
        steps: List[TestStep] = []
        step_num = 1

        # Step 1 – Setup
        steps.append(TestStep(
            step_number=step_num,
            action="Initialize the system to its nominal / safe ground state. "
                   "Confirm all Built-In Test (BIT) checks pass and no active faults are present.",
            expected_result="System in nominal state. BIT PASS. No faults detected.",
        ))
        step_num += 1

        # Steps per cause variable
        for var, active in cause_cfg.items():
            if active:
                action = f"Inject / stimulate cause condition: «{var}»."
                expected = f"System registers that «{var}» is ACTIVE / TRUE."
            else:
                action = f"Ensure cause condition is NOT present / suppressed: «{var}»."
                expected = f"System registers that «{var}» is INACTIVE / FALSE."
            steps.append(TestStep(step_num, action, expected))
            step_num += 1

        # Observe effects
        for var, active in effect_cfg.items():
            if active:
                action = f"Observe system response for effect: «{var}»."
                expected = f"Effect «{var}» is TRIGGERED / ACTIVE as required."
            else:
                action = f"Monitor that effect «{var}» is NOT triggered."
                expected = f"Effect «{var}» remains INACTIVE / suppressed."
            steps.append(TestStep(step_num, action, expected))
            step_num += 1

        # Final step – teardown
        steps.append(TestStep(
            step_number=step_num,
            action="Return system to nominal state. Log all observations and captured data.",
            expected_result="System in nominal state. Test artifacts persisted for traceability.",
        ))

        return steps

    def _build_preconditions(self, category: str, dal_level: str) -> str:
        base = (
            "1. System under test is powered and in nominal operating mode.\n"
            "2. All prerequisite subsystems are initialized and reporting healthy status.\n"
            "3. Test environment is calibrated and traceable to NIST/ISO standards.\n"
            "4. Test data is pre-loaded and verified.\n"
        )
        if "DAL-A" in dal_level or "DAL-B" in dal_level:
            base += "5. Independent safety observer is present. Safety net / inhibit verified.\n"
        if category == "Flight Control":
            base += "6. Flight control simulation rig is at zero-deflection baseline.\n"
        elif category == "Navigation":
            base += "6. GPS/INS simulator is set to reference trajectory.\n"
        elif category == "Propulsion":
            base += "6. Engine simulation is at idle state; fuel system pressurised (simulated).\n"
        return base.strip()

    def _build_notes(self, dal_level: str, tc_type: str, connector: str) -> str:
        notes = []
        if dal_level in ("DAL-A", "DAL-B"):
            notes.append("MC/DC coverage required per DO-178C §6.4.4.2.c.")
        if tc_type == "Safety":
            notes.append("Failure-mode test – capture all anomalous outputs for FMEA record.")
        if connector == "unless":
            notes.append("Note: 'unless' implies negated cause; verify inhibit logic carefully.")
        return " | ".join(notes) if notes else ""

    def _add_supplemental_tests(
        self,
        causes: List[CEGNode],
        effects: List[CEGNode],
        labeled: LabeledSentence,
        category: str,
        dal_level: str,
        test_level: str,
        std_ref: str,
        req_id: str,
        base_count: int,
    ) -> List[TestCase]:
        extras: List[TestCase] = []
        dal_info = DAL_MAP.get(dal_level, DAL_MAP["DAL-C"])

        supplemental_types = []
        if dal_level in ("DAL-A", "DAL-B"):
            supplemental_types = ["Stress", "Regression"]
        elif dal_level == "DAL-C":
            supplemental_types = ["Regression"]

        for idx, stype in enumerate(supplemental_types, start=base_count + 1):
            cause_cfg   = {_leaf_label(c): True for c in causes}
            effect_cfg  = {_effect_label(e): True for e in effects}

            if stype == "Stress":
                title = "[Stress] Rapid repeated activation – verify no timing violations"
                precond = self._build_preconditions(category, dal_level) + (
                    "\n5. High-rate stimulus generator configured for 10× nominal cycle rate."
                )
                steps = [
                    TestStep(1, "Set stimulus rate to 10× nominal operational rate.",
                             "Stimulus generator active at accelerated rate."),
                    TestStep(2, "Activate all cause conditions simultaneously for 60 seconds.",
                             "System maintains correct state throughout stress period."),
                    TestStep(3, "Verify effects remain continuously active / correctly toggled.",
                             "No spurious de-activation, timing violation, or watchdog trip."),
                    TestStep(4, "Return to nominal rate and confirm recovery.",
                             "System resumes nominal behaviour within recovery time spec."),
                ]
            else:
                title = "[Regression] Re-verify nominal path post-configuration change"
                precond = self._build_preconditions(category, dal_level)
                steps = [
                    TestStep(1, "Apply latest software / hardware configuration patch.",
                             "Configuration change applied and logged."),
                    TestStep(2, "Re-execute nominal functional test (all causes active).",
                             "All effects triggered as specified."),
                    TestStep(3, "Compare results against baseline test record.",
                             "No regression detected. Results within tolerance."),
                ]

            tc = TestCase(
                tc_id=f"TC-{req_id.replace('REQ-', '')}-{idx:03d}",
                title=title,
                requirement=labeled.sentence,
                preconditions=precond,
                test_type=stype,
                test_level=test_level,
                category=category,
                dal_level=dal_level,
                priority=dal_info["priority"],
                standard_ref=std_ref,
                cause_configuration=cause_cfg,
                effect_expected=effect_cfg,
                steps=steps,
                notes=f"Supplemental test – {stype}. Required by {std_ref}.",
                traceability_id=req_id,
            )
            extras.append(tc)

        return extras
