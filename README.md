# ✈️ AeroTCG – Aerospace Software Test Case Generator

> **Offline · Streamlit · DO-178C · ARP4754A · MIL-STD-882E**

Inspired by the [CiRA (Causality in Requirements Artifacts) initiative](https://github.com/JulianFrattini/cira) by Julian Frattini et al., this tool automatically generates structured software test cases from natural-language aerospace requirements — **with zero internet dependency at runtime**.

---

## 🏗️ Architecture: CiRA Pipeline (Offline)

```
Natural Language Requirement
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ Step 1 – Causality Classifier                           │
│  Rule-based pattern matching (regex)                    │
│  Detects: if/then, when/shall, in-case-of, unless …    │
└─────────────────┬───────────────────────────────────────┘
                  │ is_causal + confidence score
                  ▼
┌─────────────────────────────────────────────────────────┐
│ Step 2 – Requirement Labeler                            │
│  Splits sentence into cause-clause / effect-clause      │
│  Handles: AND/OR compound causes, negated clauses       │
└─────────────────┬───────────────────────────────────────┘
                  │ LabeledSentence (cause events + effect events)
                  ▼
┌─────────────────────────────────────────────────────────┐
│ Step 3 – Cause-Effect Graph (CEG) Builder               │
│  Constructs directed graph: cause nodes → effect nodes  │
│  Nodes: cause | effect | intermediate | negated_cause   │
└─────────────────┬───────────────────────────────────────┘
                  │ CauseEffectGraph
                  ▼
┌─────────────────────────────────────────────────────────┐
│ Step 4 – Test Case Generator                            │
│  Derives minimal covering test suite (MC/DC coverage)   │
│  Enriches with aerospace metadata (DAL, standards, …)   │
│  Generates: Functional | Boundary | Negative |          │
│             Safety | Stress | Regression test cases     │
└─────────────────────────────────────────────────────────┘
                  │
                  ▼
         Structured Test Cases
         (CSV / JSON / Markdown export)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- No internet required at runtime

### Installation

```bash
git clone <this-repo>
cd aerospace_tcg

# Create virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## 🛩️ Aerospace Coverage

### System Categories (23)
- Avionics, Flight Control Systems, Navigation & Guidance
- Propulsion & Engine Control, Communication Systems
- Warning & Alert Systems (GPWS/TCAS/TAWS), Landing Gear & Braking
- Fuel Management, Electrical Power, Hydraulic Systems
- Air Data Computer, FMS, Autopilot, ECS, FDR/CVR
- Structural Health Monitoring, Weather Radar, GPS/GNSS
- UAV/Drone, Space Systems, Missile Guidance, and more

### Standards Referenced
| Standard      | Focus                                          |
|---------------|------------------------------------------------|
| DO-178C       | Airborne software certification (DAL A–E)      |
| DO-254        | Airborne electronic hardware                   |
| ARP4754A      | Aircraft & systems development guidelines      |
| ARP4761       | Safety assessment processes                    |
| MIL-STD-882E  | System safety (defense)                        |
| DO-160G       | Environmental test procedures                  |
| AS9100D       | Aerospace quality management                   |
| DO-356A       | Airworthiness security                         |

### DO-178C Design Assurance Levels
| DAL   | Failure Condition | MC/DC Required |
|-------|-------------------|----------------|
| DAL-A | Catastrophic      | ✅ Yes          |
| DAL-B | Hazardous         | Recommended     |
| DAL-C | Major             | No              |
| DAL-D | Minor             | No              |
| DAL-E | No Effect         | No              |

---

## 📦 Project Structure

```
aerospace_tcg/
├── app.py                          # Streamlit frontend
├── requirements.txt
├── README.md
└── cira_engine/
    ├── __init__.py
    ├── classifier.py               # Step 1: Causality classifier
    ├── labeler.py                  # Step 2: Cause/effect labeler
    ├── graph.py                    # Step 3: CEG builder
    ├── testcase_generator.py       # Step 4: Test case generator
    └── aerospace_domain.py         # Domain knowledge & standards
```

---

## 💡 Supported Requirement Patterns

| Pattern                     | Example                                             |
|-----------------------------|-----------------------------------------------------|
| `If … then …`               | If oil pressure < 25 PSI, then FADEC shall …        |
| `When … shall …`            | When AOA > 18°, the stick shaker shall activate     |
| `If … shall …` (implicit)   | If GPS is lost, the FMS shall display warning        |
| `Unless … shall …`          | Unless GPWS is active, auto-throttle shall maintain |
| `In the event that …`       | In the event that engine stalls, FADEC shall …      |
| `In case of …`              | In case of hydraulic failure, the system shall …    |
| `Provided that …`           | Provided that airspeed > 250 kts, FCC shall limit … |
| `Given that …`              | Given that gear is retracted, system shall …        |
| `Once … shall …`            | Once gear is locked down, warning shall cease       |
| `After … shall …`           | After takeoff thrust set, FMS shall compute …       |
| Compound (AND/OR causes)    | If A and B, then … / If A or B, then …             |

---

## 🧪 Test Case Structure

Each generated test case includes:

- **TC ID** — Traceable identifier (`TC-001-001`)
- **Title** — Descriptive test case title
- **Test Type** — Functional / Boundary / Negative / Safety / Stress / Regression
- **Test Level** — Unit / Integration / System / Acceptance
- **DAL Level** — DO-178C design assurance level
- **Priority** — Critical / High / Medium / Low
- **Standard References** — DO-178C clause, ARP4754A section, etc.
- **Cause Configuration** — Boolean table of cause conditions
- **Expected Effects** — Boolean table of expected system responses
- **Preconditions** — Setup requirements including safety constraints
- **Test Steps** — Numbered action → expected result pairs
- **Traceability ID** — Links back to source requirement

---

## 📤 Export Formats

- **CSV** — Import into Excel, DOORS, JIRA Xray, TestRail, Polarion
- **JSON** — Machine-readable for CI/CD pipeline integration
- **Markdown** — Documentation-ready format

---

## 🔬 CiRA Research Reference

This tool implements the 4-step pipeline described in:

> Frattini, J., Fischbach, J., & Vogelsang, A. (2023).
> *CiRA: An Open-Source Python Package for Automated Generation of Test Case Descriptions from Natural Language Requirements.*
> IEEE REFSQ 2023. DOI: 10.1109/REQ-2023.xxx

Original repository: https://github.com/JulianFrattini/cira

---

## 📄 License
MIT License — see LICENSE file.
