"""
Aerospace Domain Knowledge Base.
Standards, categories, templates, and sample requirements for the
Aerospace Test Case Generation Tool.
"""

from typing import Dict, List


# ── Aerospace System Categories ───────────────────────────────────────────────
AEROSPACE_CATEGORIES: List[str] = [
    "Avionics",
    "Flight Control Systems",
    "Navigation & Guidance",
    "Propulsion & Engine Control",
    "Communication Systems",
    "Flight Management System (FMS)",
    "Autopilot & Auto-Throttle",
    "Warning & Alert Systems (GPWS/TCAS/TAWS)",
    "Landing Gear & Braking",
    "Environmental Control System (ECS)",
    "Fuel Management System",
    "Electrical Power System",
    "Hydraulic Systems",
    "Air Data Computer (ADC)",
    "Flight Data Recorder (FDR/CVR)",
    "Structural Health Monitoring",
    "Ground Proximity Warning System",
    "Weather Radar System",
    "Satellite Systems (GPS/GNSS)",
    "UAV / Drone Systems",
    "Space Systems",
    "Missile Guidance",
    "Other",
]

# ── Applicable Standards ──────────────────────────────────────────────────────
STANDARDS: Dict[str, Dict] = {
    "DO-178C": {
        "full_name": "DO-178C – Software Considerations in Airborne Systems and Equipment Certification",
        "clauses": {
            "6.4.4": "Software Testing – Test coverage and types",
            "6.4.4.2": "Modified Condition/Decision Coverage (MC/DC)",
            "6.4.3": "Software Integration Testing",
            "6.3":   "Software Design Process",
            "Annex A": "DO-178C Process Objectives Table",
        },
        "dal_applicability": ["DAL-A", "DAL-B", "DAL-C", "DAL-D"],
    },
    "DO-254": {
        "full_name": "DO-254 – Design Assurance Guidance for Airborne Electronic Hardware",
        "clauses": {
            "5.2.1": "Hardware Verification",
            "6.1":   "Validation and Verification Process",
        },
        "dal_applicability": ["DAL-A", "DAL-B", "DAL-C", "DAL-D"],
    },
    "ARP4754A": {
        "full_name": "ARP4754A – Guidelines for Development of Civil Aircraft and Systems",
        "clauses": {
            "5.3":  "Functional Hazard Assessment (FHA)",
            "5.4":  "Safety Assessment Process",
            "6.3":  "Requirements Validation",
            "7.0":  "System Verification",
        },
        "dal_applicability": ["DAL-A", "DAL-B", "DAL-C", "DAL-D", "DAL-E"],
    },
    "ARP4761": {
        "full_name": "ARP4761 – Guidelines for Conducting Safety Assessment Process",
        "clauses": {
            "4.0": "Functional Hazard Assessment",
            "5.0": "Preliminary System Safety Assessment (PSSA)",
            "6.0": "System Safety Assessment (SSA)",
            "7.0": "FMEA / FMES",
        },
        "dal_applicability": ["DAL-A", "DAL-B", "DAL-C"],
    },
    "MIL-STD-882E": {
        "full_name": "MIL-STD-882E – System Safety",
        "clauses": {
            "Task 101": "Hazard Identification",
            "Task 202": "System Safety Analysis",
            "Task 301": "System Safety Verification",
        },
        "dal_applicability": ["DAL-A", "DAL-B", "DAL-C"],
    },
    "DO-160G": {
        "full_name": "DO-160G – Environmental Conditions and Test Procedures for Airborne Equipment",
        "clauses": {
            "Section 7":  "Operational Shock and Crash Safety",
            "Section 16": "Power Input",
            "Section 20": "Radio Frequency Susceptibility",
        },
        "dal_applicability": ["DAL-A", "DAL-B", "DAL-C", "DAL-D"],
    },
    "AS9100D": {
        "full_name": "AS9100D – Quality Management System for Aviation, Space and Defense",
        "clauses": {
            "8.3.4": "Design and Development Controls",
            "8.4":   "Control of Externally Provided Processes",
            "8.7":   "Control of Nonconforming Outputs",
        },
        "dal_applicability": ["DAL-A", "DAL-B", "DAL-C", "DAL-D", "DAL-E"],
    },
    "RTCA DO-356A": {
        "full_name": "DO-356A – Airworthiness Security Methods and Considerations",
        "clauses": {
            "4.1": "Threat Conditions",
            "5.2": "Security Risk Assessment",
        },
        "dal_applicability": ["DAL-A", "DAL-B", "DAL-C"],
    },
}

# ── Sample Aerospace Requirements ─────────────────────────────────────────────
SAMPLE_REQUIREMENTS: Dict[str, List[Dict]] = {
    "Flight Control Systems": [
        {
            "id": "REQ-FCS-001",
            "text": "If the pilot applies more than 5 degrees of aileron deflection and the airspeed exceeds 250 knots, then the Flight Control Computer shall limit the roll rate to 15 degrees per second.",
            "dal": "DAL-A",
        },
        {
            "id": "REQ-FCS-002",
            "text": "When the angle of attack sensor detects a value greater than 18 degrees, the stick shaker shall activate and an audio warning shall be generated.",
            "dal": "DAL-A",
        },
        {
            "id": "REQ-FCS-003",
            "text": "If the autopilot is engaged and the pitch deviation exceeds 5 degrees from the selected altitude, then the autopilot shall issue a corrective pitch command within 200 milliseconds.",
            "dal": "DAL-B",
        },
        {
            "id": "REQ-FCS-004",
            "text": "Unless the ground proximity warning is active, the auto-throttle shall maintain the selected thrust level within ±2% of the commanded value.",
            "dal": "DAL-B",
        },
    ],
    "Navigation & Guidance": [
        {
            "id": "REQ-NAV-001",
            "text": "When GPS signal integrity is lost and the inertial navigation system is operating in standalone mode, the Flight Management System shall display a Navigation Degraded warning and update the estimated position error on the primary flight display.",
            "dal": "DAL-B",
        },
        {
            "id": "REQ-NAV-002",
            "text": "If the localizer deviation exceeds 0.5 dot during the final approach phase, then the instrument landing system shall trigger a go-around advisory.",
            "dal": "DAL-A",
        },
        {
            "id": "REQ-NAV-003",
            "text": "When the aircraft enters a terminal airspace boundary and the TCAS system detects a traffic advisory, the system shall compute a resolution advisory within 35 seconds.",
            "dal": "DAL-A",
        },
    ],
    "Warning & Alert Systems (GPWS/TCAS/TAWS)": [
        {
            "id": "REQ-WARN-001",
            "text": "If the terrain clearance falls below 500 feet AGL during a non-precision approach and the landing gear is not extended, then the GPWS shall issue a PULL UP warning.",
            "dal": "DAL-A",
        },
        {
            "id": "REQ-WARN-002",
            "text": "When an excessive descent rate exceeds 6000 feet per minute below 2500 feet AGL, the TAWS shall generate an aural and visual SINK RATE warning.",
            "dal": "DAL-A",
        },
    ],
    "Propulsion & Engine Control": [
        {
            "id": "REQ-ENG-001",
            "text": "If the engine oil pressure drops below 25 PSI during normal operation, the Full Authority Digital Engine Control (FADEC) shall reduce engine thrust to idle and generate a low oil pressure caution message.",
            "dal": "DAL-A",
        },
        {
            "id": "REQ-ENG-002",
            "text": "When the engine exhaust gas temperature exceeds 950 degrees Celsius and the N1 speed is above 95%, the FADEC shall automatically reduce fuel flow and alert the crew.",
            "dal": "DAL-A",
        },
        {
            "id": "REQ-ENG-003",
            "text": "If a compressor stall is detected via N2 oscillation greater than ±3% within 500 milliseconds, then the engine anti-icing system shall activate and the crew shall be notified.",
            "dal": "DAL-B",
        },
    ],
    "Fuel Management System": [
        {
            "id": "REQ-FUEL-001",
            "text": "When the total fuel quantity falls below the minimum reserve of 2000 kg and the aircraft is airborne, the fuel management system shall activate a LOW FUEL warning and transmit a datalink message to ATC.",
            "dal": "DAL-B",
        },
        {
            "id": "REQ-FUEL-002",
            "text": "If the fuel imbalance between left and right wing tanks exceeds 500 kg, then the automatic fuel transfer system shall initiate cross-feed balancing.",
            "dal": "DAL-C",
        },
    ],
    "Landing Gear & Braking": [
        {
            "id": "REQ-LDG-001",
            "text": "If the aircraft descends below 800 feet AGL and the landing gear is not in the locked down position, then the gear warning horn shall sound continuously.",
            "dal": "DAL-A",
        },
        {
            "id": "REQ-LDG-002",
            "text": "When the wheel speed sensor detects anti-skid activation and the brake temperature exceeds 400 degrees Celsius, the brake-by-wire system shall reduce braking pressure by 30%.",
            "dal": "DAL-B",
        },
    ],
    "Communication Systems": [
        {
            "id": "REQ-COM-001",
            "text": "When the primary VHF communication radio fails and the aircraft is operating in controlled airspace, the backup UHF radio shall automatically select the guard frequency 121.5 MHz.",
            "dal": "DAL-B",
        },
        {
            "id": "REQ-COM-002",
            "text": "If the datalink uplink buffer is full and a new ACARS message is received, the system shall discard the oldest non-safety message and log the event.",
            "dal": "DAL-C",
        },
    ],
    "Avionics": [
        {
            "id": "REQ-AVI-001",
            "text": "If the primary display unit fails and the secondary display unit is operating normally, the system shall automatically transfer all primary flight instrument symbology to the secondary display within 500 milliseconds.",
            "dal": "DAL-A",
        },
        {
            "id": "REQ-AVI-002",
            "text": "When the Integrated Modular Avionics (IMA) detects a module health failure exceeding the MTBF threshold, the system shall reroute the affected application to a spare partition and log the fault.",
            "dal": "DAL-B",
        },
    ],
}

# ── Test Level Definitions ────────────────────────────────────────────────────
TEST_LEVELS: Dict[str, str] = {
    "Unit":        "Unit / Low-Level Test – verifies individual software components/modules",
    "Integration": "Integration Test – verifies interfaces between components/subsystems",
    "System":      "System Test – verifies the complete integrated system against requirements",
    "Acceptance":  "Acceptance Test / Qualification – formal certification-level testing",
}

# ── Test Type Definitions ─────────────────────────────────────────────────────
TEST_TYPES: Dict[str, str] = {
    "Functional":  "Verify normal operation with all conditions met",
    "Boundary":    "Exercise boundary / edge values of conditions",
    "Negative":    "Verify correct response when conditions are NOT met",
    "Stress":      "Verify stability under high load / rapid cycling",
    "Safety":      "Verify safe-state transition on failure/fault injection",
    "Regression":  "Re-verify existing behaviour after a change",
}

# ── Priority colours ──────────────────────────────────────────────────────────
PRIORITY_COLORS: Dict[str, str] = {
    "Critical":      "#d62728",
    "High":          "#ff7f0e",
    "Medium":        "#2ca02c",
    "Low":           "#1f77b4",
    "Informational": "#9467bd",
}

TEST_TYPE_ICONS: Dict[str, str] = {
    "Functional":  "✅",
    "Boundary":    "⚠️",
    "Negative":    "❌",
    "Stress":      "🔥",
    "Safety":      "🛡️",
    "Regression":  "🔄",
}

# ── DO-178C Design Assurance Levels (also used by testcase_generator) ────────
DAL_MAP: Dict[str, Dict] = {
    "DAL-A": {"label": "Level A – Catastrophic", "priority": "Critical", "color": "#d62728"},
    "DAL-B": {"label": "Level B – Hazardous",    "priority": "High",     "color": "#ff7f0e"},
    "DAL-C": {"label": "Level C – Major",        "priority": "Medium",   "color": "#2ca02c"},
    "DAL-D": {"label": "Level D – Minor",        "priority": "Low",      "color": "#1f77b4"},
    "DAL-E": {"label": "Level E – No Effect",    "priority": "Informational", "color": "#9467bd"},
}
