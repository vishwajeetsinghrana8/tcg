import io
import json
import re
from datetime import datetime
from typing import List, Optional

import pandas as pd
import streamlit as st

from cira_engine import (
    AEROSPACE_CATEGORIES,
    DAL_MAP,
    PRIORITY_COLORS,
    SAMPLE_REQUIREMENTS,
    STANDARDS,
    TEST_LEVELS,
    TEST_TYPE_ICONS,
    TEST_TYPES,
    CausalityClassifier,
    RequirementLabeler,
    TestCase,
    TestCaseGenerator,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AeroTCG – Aerospace Test Case Generator",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stSidebar"]          { background: #161b22; border-right: 1px solid #30363d; }

/* ── Header banner ── */
.aero-header {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    border: 1px solid #1f6feb;
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 24px;
}
.aero-header h1 { color: #79c0ff; margin: 0; font-size: 1.9rem; letter-spacing: 1px; }
.aero-header p  { color: #8b949e; margin: 4px 0 0; font-size: 0.88rem; }

/* ── Metric cards ── */
.metric-row { display: flex; gap: 12px; margin-bottom: 16px; }
.metric-card {
    flex: 1; background: #161b22; border: 1px solid #30363d;
    border-radius: 10px; padding: 14px 18px; text-align: center;
}
.metric-card .val { font-size: 1.8rem; font-weight: 700; color: #79c0ff; }
.metric-card .lbl { font-size: 0.78rem; color: #8b949e; margin-top: 2px; }

/* ── Pipeline step badges ── */
.step-badge {
    display: inline-block; background: #1f6feb; color: #fff;
    border-radius: 50%; width: 26px; height: 26px;
    line-height: 26px; text-align: center; font-weight: 700;
    font-size: 0.82rem; margin-right: 6px;
}

/* ── Test case cards ── */
.tc-card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 10px; padding: 16px 20px; margin-bottom: 14px;
}
.tc-card-header { display: flex; justify-content: space-between; align-items: flex-start; }
.tc-id   { font-size: 0.78rem; color: #58a6ff; font-weight: 600; font-family: monospace; }
.tc-type { font-size: 0.78rem; padding: 2px 8px; border-radius: 12px;
           background: #21262d; color: #e6edf3; }

/* ── Priority badge ── */
.badge-Critical     { background: #6e1a1a; color: #ffa198; }
.badge-High         { background: #3d2b00; color: #ffa657; }
.badge-Medium       { background: #1a3a1a; color: #7ee787; }
.badge-Low          { background: #1a2d4a; color: #79c0ff; }
.badge-Informational{ background: #2d1f4a; color: #d2a8ff; }

/* ── Cause / Effect tables ── */
.bool-true  { color: #7ee787; font-weight: 600; }
.bool-false { color: #ffa198; font-weight: 600; }

/* ── Sidebar labels ── */
.sidebar-section {
    font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 1px; color: #8b949e; margin: 16px 0 6px;
}

/* ── CEG graph node ── */
.ceg-node {
    display: inline-block; padding: 4px 10px; border-radius: 6px;
    font-size: 0.80rem; margin: 3px; font-family: monospace;
}
.ceg-cause  { background: #1f3d2c; border: 1px solid #238636; color: #7ee787; }
.ceg-effect { background: #1f2d4a; border: 1px solid #1f6feb; color: #79c0ff; }
.ceg-neg    { background: #3d1f1f; border: 1px solid #b91c1c; color: #ffa198; }

/* ── Standard badge ── */
.std-badge {
    display: inline-block; background: #21262d; border: 1px solid #30363d;
    border-radius: 6px; font-size: 0.72rem; padding: 2px 8px;
    color: #d2a8ff; margin: 2px;
}

/* ── Step table ── */
.step-row { display: flex; gap: 12px; margin-bottom: 8px; align-items: flex-start; }
.step-num { min-width: 26px; height: 26px; background: #21262d;
            border-radius: 50%; text-align: center; line-height: 26px;
            font-size: 0.78rem; color: #79c0ff; font-weight: 700; }
.step-action   { flex: 1; font-size: 0.84rem; color: #e6edf3; }
.step-expected { flex: 1; font-size: 0.84rem; color: #7ee787; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "generated_tcs"  not in st.session_state: st.session_state.generated_tcs  = []
if "last_req_text"  not in st.session_state: st.session_state.last_req_text  = ""
if "classification" not in st.session_state: st.session_state.classification = None
if "labeled_sent"   not in st.session_state: st.session_state.labeled_sent   = None

# ── Instantiate pipeline ──────────────────────────────────────────────────────
@st.cache_resource
def load_pipeline():
    return (
        CausalityClassifier(threshold=0.60),
        RequirementLabeler(),
        TestCaseGenerator(),
    )

classifier, labeler, generator = load_pipeline()

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ✈️ AeroTCG")
    st.markdown("<div class='sidebar-section'>System Domain</div>", unsafe_allow_html=True)

    selected_category = st.selectbox(
        "Aerospace Category",
        AEROSPACE_CATEGORIES,
        index=0,
        help="Select the aerospace system category for contextual test enrichment.",
    )

    st.markdown("<div class='sidebar-section'>DO-178C Design Assurance Level</div>",
                unsafe_allow_html=True)
    dal_options = list(DAL_MAP.keys())
    selected_dal = st.selectbox(
        "DAL Level",
        dal_options,
        index=2,
        format_func=lambda x: f"{x} – {DAL_MAP[x]['label'].split('–')[1].strip()}",
        help="Higher DAL = more rigorous testing (DO-178C / ARP4754A).",
    )
    dal_info = DAL_MAP[selected_dal]
    st.markdown(
        f"<span class='std-badge'>Priority: {dal_info['priority']}</span>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='sidebar-section'>Test Level</div>", unsafe_allow_html=True)
    selected_test_level = st.selectbox(
        "Test Level",
        list(TEST_LEVELS.keys()),
        index=2,
        format_func=lambda x: x,
        help="Corresponds to DO-178C testing levels.",
    )
    st.caption(TEST_LEVELS[selected_test_level])

    st.markdown("<div class='sidebar-section'>Applicable Standards</div>",
                unsafe_allow_html=True)
    all_stds = list(STANDARDS.keys())
    selected_standards = st.multiselect(
        "Standards References",
        all_stds,
        default=["DO-178C", "ARP4754A"],
        help="Selected standards will appear in test case references.",
    )

    st.markdown("<div class='sidebar-section'>Requirement ID</div>",
                unsafe_allow_html=True)
    req_id = st.text_input("Requirement ID", value="REQ-001",
                           help="Used for test case ID and traceability.")

    st.divider()
    st.markdown("<div class='sidebar-section'>Sample Requirements</div>",
                unsafe_allow_html=True)
    sample_cat = st.selectbox(
        "Load sample from",
        [c for c in SAMPLE_REQUIREMENTS.keys()],
        index=0,
    )
    sample_reqs = SAMPLE_REQUIREMENTS.get(sample_cat, [])
    if sample_reqs:
        sample_choice = st.selectbox(
            "Select requirement",
            sample_reqs,
            format_func=lambda r: r["id"],
        )
        if st.button("📥  Load Sample", width='content'):
            st.session_state.load_sample = sample_choice
    else:
        st.info("No samples for this category.")

    st.divider()
    st.markdown(
        "<div style='font-size:0.72rem;color:#8b949e'>"
        "Built on the <b>CiRA</b> initiative by J.Frattini et al.<br>"
        "Pipeline: Classifier → Labeler → CEG → TestGen<br>"
        "Fully offline · No API required"
        "</div>",
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class='aero-header'>
  <h1>✈️ AeroTCG – Aerospace Software Test Case Generator</h1>
  <p>
    Offline test case generation from natural language requirements &nbsp;|&nbsp;
    Powered by the <b>CiRA</b> causality pipeline &nbsp;|&nbsp;
    DO-178C · ARP4754A · MIL-STD-882E · DO-254
  </p>
</div>
""", unsafe_allow_html=True)

# ── Tab layout ────────────────────────────────────────────────────────────────
tab_gen, tab_batch, tab_ref = st.tabs(
    ["🔬 Generate Test Cases", "📋 Batch Processing", "📚 Standards Reference"]
)

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 – GENERATE
# ══════════════════════════════════════════════════════════════════════════════
with tab_gen:

    # Load sample if requested
    if hasattr(st.session_state, "load_sample"):
        smp = st.session_state.load_sample
        st.session_state.last_req_text = smp["text"]
        del st.session_state.load_sample

    col_input, col_opts = st.columns([3, 1])

    with col_input:
        st.markdown(
            "<span class='step-badge'>1</span> **Enter Aerospace Requirement**",
            unsafe_allow_html=True,
        )
        req_text = st.text_area(
            "Requirement Text",
            value=st.session_state.last_req_text,
            height=130,
            placeholder=(
                "Example: If the engine oil pressure drops below 25 PSI during normal "
                "operation, the FADEC shall reduce engine thrust to idle and generate a "
                "low oil pressure caution message."
            ),
            label_visibility="collapsed",
        )

    with col_opts:
        st.markdown("**Generation Options**")
        show_steps = st.checkbox("Show test steps", value=True)
        show_ceg   = st.checkbox("Show CEG graph",  value=True)
        show_calib = st.checkbox("Show classifier analysis", value=False)

    generate_btn = st.button(
        "⚙️  Generate Test Cases", type="primary", width='content'
    )

    # ── Classification preview ────────────────────────────────────────────────
    if req_text and (generate_btn or show_calib):
        result = classifier.classify(req_text)
        st.session_state.classification = result

        if show_calib or generate_btn:
            with st.expander(
                f"{'✅' if result.is_causal else '⚠️'} "
                f"Classifier Analysis  (confidence: {result.confidence:.0%})",
                expanded=not result.is_causal,
            ):
                col_a, col_b = st.columns(2)
                col_a.metric("Causal?",    "YES ✅" if result.is_causal else "NO ⚠️")
                col_b.metric("Confidence", f"{result.confidence:.0%}")
                if result.matched_pattern:
                    st.code(f"Matched pattern: {result.matched_pattern}", language="text")
                if not result.is_causal:
                    st.warning(
                        "⚠️ This requirement was not classified as strongly causal. "
                        "Test cases will still be generated using a fallback strategy. "
                        "Consider rephrasing with explicit causal language "
                        "(e.g., 'If … then …', 'When … shall …')."
                    )

    # ── Main generation ───────────────────────────────────────────────────────
    if generate_btn:
        if not req_text.strip():
            st.error("Please enter a requirement text.")
        else:
            st.session_state.last_req_text = req_text

            with st.spinner("Running CiRA pipeline…"):
                # Step 1 – Classify
                cls_result = classifier.classify(req_text)

                # Step 2 – Label
                labeled = labeler.label(req_text)
                st.session_state.labeled_sent = labeled

                # Step 3+4 – Build CEG & generate test cases
                test_cases = generator.generate(
                    labeled=labeled,
                    category=selected_category,
                    dal_level=selected_dal,
                    test_level=selected_test_level,
                    standard_refs=selected_standards if selected_standards else ["DO-178C"],
                    req_id=req_id,
                )
                st.session_state.generated_tcs = test_cases

            st.success(
                f"✅ Generated **{len(test_cases)} test cases** for `{req_id}` "
                f"({selected_category} · {selected_dal} · {selected_test_level})"
            )

    # ── Display generated test cases ──────────────────────────────────────────
    tcs: List[TestCase] = st.session_state.generated_tcs

    if tcs:
        labeled = st.session_state.labeled_sent

        # ── Summary metrics ───────────────────────────────────────────────────
        type_counts = {}
        for tc in tcs:
            type_counts[tc.test_type] = type_counts.get(tc.test_type, 0) + 1

        st.markdown(f"""
        <div class='metric-row'>
          <div class='metric-card'><div class='val'>{len(tcs)}</div><div class='lbl'>Test Cases</div></div>
          <div class='metric-card'><div class='val'>{len(set(tc.test_type for tc in tcs))}</div><div class='lbl'>Test Types</div></div>
          <div class='metric-card'><div class='val'>{len(set(tc.traceability_id for tc in tcs))}</div><div class='lbl'>Requirements</div></div>
          <div class='metric-card'><div class='val'>{tcs[0].dal_level}</div><div class='lbl'>DAL Level</div></div>
          <div class='metric-card'><div class='val'>{tcs[0].test_level}</div><div class='lbl'>Test Level</div></div>
        </div>
        """, unsafe_allow_html=True)

        # ── Cause-Effect Graph ────────────────────────────────────────────────
        if show_ceg and labeled:
            with st.expander("<span class='step-badge'>3</span> Cause-Effect Graph (CEG)",expanded=True):
                st.markdown(
                    "<span class='step-badge'>3</span> **Cause-Effect Graph (CEG)**",
                    unsafe_allow_html=True,
                )
                col_c, col_e = st.columns(2)
                with col_c:
                    st.markdown("**🟢 Cause Nodes**")
                    for ev in labeled.causes:
                        neg = "ceg-neg" if ev.negated else "ceg-cause"
                        neg_lbl = " [NEGATED]" if ev.negated else ""
                        st.markdown(
                            f"<div class='ceg-node {neg}'>{ev.text[:90]}{neg_lbl}</div>",
                            unsafe_allow_html=True,
                        )
                        if ev.sub_events:
                            for sub in ev.sub_events:
                                st.markdown(
                                    f"&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#8b949e'>"
                                    f"└ [{ev.connector}]</span> "
                                    f"<div class='ceg-node ceg-cause' style='display:inline'>"
                                    f"{sub.text[:80]}</div>",
                                    unsafe_allow_html=True,
                                )
                with col_e:
                    st.markdown("**🔵 Effect Nodes**")
                    for ev in labeled.effects:
                        st.markdown(
                            f"<div class='ceg-node ceg-effect'>{ev.text[:90]}</div>",
                            unsafe_allow_html=True,
                        )
                st.caption(f"Connector type: **{labeled.connector_type}**")

        # ── Filter bar ────────────────────────────────────────────────────────
        st.markdown(
            "<span class='step-badge'>4</span> **Generated Test Suite**",
            unsafe_allow_html=True,
        )
        fcol1, fcol2 = st.columns([2, 2])
        with fcol1:
            filter_types = st.multiselect(
                "Filter by test type",
                list(set(tc.test_type for tc in tcs)),
                default=list(set(tc.test_type for tc in tcs)),
            )
        with fcol2:
            filter_priority = st.multiselect(
                "Filter by priority",
                list(set(tc.priority for tc in tcs)),
                default=list(set(tc.priority for tc in tcs)),
            )

        filtered = [
            tc for tc in tcs
            if tc.test_type in filter_types and tc.priority in filter_priority
        ]

        # ── Test case cards ───────────────────────────────────────────────────
        for tc in filtered:
            icon  = TEST_TYPE_ICONS.get(tc.test_type, "🔬")
            p_cls = f"badge-{tc.priority}"
            color = PRIORITY_COLORS.get(tc.priority, "#8b949e")

            with st.expander(
                f"{icon} `{tc.tc_id}` — {tc.title}", expanded=False
            ):
                hcol1, hcol2, hcol3, hcol4 = st.columns([2, 1, 1, 1])
                hcol1.markdown(
                    f"<span class='std-badge'>{tc.test_type}</span> "
                    f"<span class='std-badge'>{tc.test_level}</span> "
                    f"<span class='std-badge'>{tc.category}</span>",
                    unsafe_allow_html=True,
                )
                hcol2.markdown(
                    f"<span class='std-badge {p_cls}'>⚡ {tc.priority}</span>",
                    unsafe_allow_html=True,
                )
                hcol3.markdown(
                    f"<span class='std-badge'>{tc.dal_level}</span>",
                    unsafe_allow_html=True,
                )
                hcol4.markdown(
                    f"<span class='std-badge'>{tc.traceability_id}</span>",
                    unsafe_allow_html=True,
                )

                st.markdown(f"**Requirement:** _{tc.requirement}_")
                st.markdown(f"**Standard Ref:** {tc.standard_ref}")

                # Cause / Effect tables
                col_cause, col_effect = st.columns(2)
                with col_cause:
                    st.markdown("**Cause Configuration**")
                    rows = [
                        {"Variable": v,
                         "State": "✅ TRUE" if s else "❌ FALSE"}
                        for v, s in tc.cause_configuration.items()
                    ]
                    st.dataframe(pd.DataFrame(rows), hide_index=True, width='content')

                with col_effect:
                    st.markdown("**Expected Effects**")
                    rows = [
                        {"Effect": v,
                         "Expected": "✅ TRIGGERED" if s else "❌ NOT TRIGGERED"}
                        for v, s in tc.effect_expected.items()
                    ]
                    st.dataframe(pd.DataFrame(rows), hide_index=True, width='content')

                # Preconditions
                with st.expander("📋 Preconditions"):
                    st.markdown(tc.preconditions)

                # Steps
                if show_steps and tc.steps:
                    with st.expander(f"🧪 Test Steps ({len(tc.steps)})"):
                        step_df = pd.DataFrame([
                            {"#": s.step_number, "Action": s.action,
                             "Expected Result": s.expected_result}
                            for s in tc.steps
                        ])
                        st.dataframe(step_df, hide_index=True, width='content')

                # Notes
                if tc.notes:
                    st.info(f"📝 **Notes:** {tc.notes}")

        # ── Export ────────────────────────────────────────────────────────────
        st.divider()
        st.markdown("### 📤 Export Test Suite")
        exp_col1, exp_col2, exp_col3 = st.columns(3)

        # CSV export
        with exp_col1:
            csv_rows = []
            for tc in filtered:
                causes_str  = "; ".join(f"{k}={'TRUE' if v else 'FALSE'}"
                                        for k, v in tc.cause_configuration.items())
                effects_str = "; ".join(f"{k}={'TRIGGERED' if v else 'NOT TRIGGERED'}"
                                        for k, v in tc.effect_expected.items())
                csv_rows.append({
                    "TC ID":           tc.tc_id,
                    "Title":           tc.title,
                    "Requirement":     tc.requirement,
                    "Test Type":       tc.test_type,
                    "Test Level":      tc.test_level,
                    "Category":        tc.category,
                    "DAL Level":       tc.dal_level,
                    "Priority":        tc.priority,
                    "Standard Ref":    tc.standard_ref,
                    "Traceability ID": tc.traceability_id,
                    "Cause Config":    causes_str,
                    "Effects":         effects_str,
                    "Preconditions":   tc.preconditions,
                    "Notes":           tc.notes,
                })
            csv_df  = pd.DataFrame(csv_rows)
            csv_buf = io.StringIO()
            csv_df.to_csv(csv_buf, index=False)
            st.download_button(
                "⬇️ Download CSV",
                data=csv_buf.getvalue(),
                file_name=f"aerotcg_{req_id}_{datetime.now():%Y%m%d_%H%M%S}.csv",
                mime="text/csv",
                width='content',
            )

        # JSON export
        with exp_col2:
            json_data = []
            for tc in filtered:
                json_data.append({
                    "tc_id":             tc.tc_id,
                    "title":             tc.title,
                    "requirement":       tc.requirement,
                    "test_type":         tc.test_type,
                    "test_level":        tc.test_level,
                    "category":          tc.category,
                    "dal_level":         tc.dal_level,
                    "priority":          tc.priority,
                    "standard_ref":      tc.standard_ref,
                    "traceability_id":   tc.traceability_id,
                    "cause_config":      tc.cause_configuration,
                    "effects_expected":  tc.effect_expected,
                    "preconditions":     tc.preconditions,
                    "steps": [
                        {"step": s.step_number,
                         "action": s.action,
                         "expected": s.expected_result}
                        for s in tc.steps
                    ],
                    "notes": tc.notes,
                })
            st.download_button(
                "⬇️ Download JSON",
                data=json.dumps(json_data, indent=2),
                file_name=f"aerotcg_{req_id}_{datetime.now():%Y%m%d_%H%M%S}.json",
                mime="application/json",
                width='content',
            )

        # Markdown export
        with exp_col3:
            md_lines = [
                f"# AeroTCG – Test Suite for `{req_id}`",
                f"*Generated: {datetime.now():%Y-%m-%d %H:%M:%S}*",
                f"\n**Requirement:** {tcs[0].requirement if tcs else ''}",
                f"**Category:** {selected_category}  |  "
                f"**DAL:** {selected_dal}  |  **Level:** {selected_test_level}",
                "\n---\n",
            ]
            for tc in filtered:
                md_lines += [
                    f"## {tc.tc_id} – {tc.title}",
                    f"- **Type:** {tc.test_type}  |  **Priority:** {tc.priority}",
                    f"- **Standard:** {tc.standard_ref}",
                    f"\n### Cause Configuration",
                    *[f"- `{k}` = {'TRUE ✅' if v else 'FALSE ❌'}"
                      for k, v in tc.cause_configuration.items()],
                    f"\n### Expected Effects",
                    *[f"- `{k}` = {'TRIGGERED ✅' if v else 'NOT TRIGGERED ❌'}"
                      for k, v in tc.effect_expected.items()],
                    f"\n### Preconditions",
                    tc.preconditions,
                ]
                if tc.steps:
                    md_lines.append("\n### Test Steps")
                    for s in tc.steps:
                        md_lines.append(
                            f"{s.step_number}. **Action:** {s.action}  \n"
                            f"   **Expected:** {s.expected_result}"
                        )
                if tc.notes:
                    md_lines.append(f"\n> 📝 {tc.notes}")
                md_lines.append("\n---\n")

            st.download_button(
                "⬇️ Download Markdown",
                data="\n".join(md_lines),
                file_name=f"aerotcg_{req_id}_{datetime.now():%Y%m%d_%H%M%S}.md",
                mime="text/markdown",
                width='content',
            )

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 – BATCH PROCESSING
# ══════════════════════════════════════════════════════════════════════════════
with tab_batch:
    st.markdown("### 📋 Batch Requirement Processing")
    st.info(
        "Enter multiple requirements (one per line). "
        "The pipeline will classify and generate test cases for all causal requirements."
    )

    batch_text = st.text_area(
        "Requirements (one per line)",
        height=220,
        placeholder=(
            "REQ-FCS-001: If the pilot applies more than 5 degrees of aileron deflection, then the FCC shall limit roll rate.\n"
            "REQ-ENG-001: When the oil pressure drops below 25 PSI, the FADEC shall reduce thrust to idle.\n"
            "REQ-NAV-001: If GPS signal is lost and INS is in standalone mode, the FMS shall display Navigation Degraded."
        ),
    )

    batch_dal   = st.selectbox("Batch DAL Level",   dal_options, index=2, key="b_dal")
    batch_level = st.selectbox("Batch Test Level",  list(TEST_LEVELS.keys()), index=2, key="b_lvl")
    batch_cat   = st.selectbox("Batch Category",    AEROSPACE_CATEGORIES, index=0, key="b_cat")
    batch_stds  = st.multiselect("Batch Standards", all_stds,
                                 default=["DO-178C", "ARP4754A"], key="b_std")

    if st.button("⚙️  Run Batch Generation", type="primary", width='content'):
        lines = [l.strip() for l in batch_text.strip().splitlines() if l.strip()]
        if not lines:
            st.error("Please enter at least one requirement.")
        else:
            all_results = []
            progress    = st.progress(0, text="Processing…")

            for i, line in enumerate(lines):
                # Extract optional REQ-ID prefix
                m = re.match(r"^(REQ-[A-Z0-9\-]+)\s*:\s*(.+)$", line, re.IGNORECASE)
                if m:
                    r_id, r_text = m.group(1), m.group(2)
                else:
                    r_id, r_text = f"REQ-{i+1:03d}", line

                cls_res = classifier.classify(r_text)
                lbl     = labeler.label(r_text)
                tcs_b   = generator.generate(
                    lbl, batch_cat, batch_dal, batch_level,
                    batch_stds or ["DO-178C"], r_id,
                )
                for tc in tcs_b:
                    all_results.append({
                        "TC ID":       tc.tc_id,
                        "Req ID":      r_id,
                        "Title":       tc.title,
                        "Type":        tc.test_type,
                        "Level":       tc.test_level,
                        "DAL":         tc.dal_level,
                        "Priority":    tc.priority,
                        "Causal?":     "YES" if cls_res.is_causal else "NO",
                        "Confidence":  f"{cls_res.confidence:.0%}",
                    })

                progress.progress((i + 1) / len(lines),
                                  text=f"Processed {i+1}/{len(lines)}: {r_id}")

            progress.empty()

            if all_results:
                df = pd.DataFrame(all_results)
                st.success(f"✅ Generated **{len(df)} test cases** from {len(lines)} requirements.")
                st.dataframe(df, width='content', hide_index=True)

                csv_b = io.StringIO()
                df.to_csv(csv_b, index=False)
                st.download_button(
                    "⬇️ Download Batch CSV",
                    data=csv_b.getvalue(),
                    file_name=f"aerotcg_batch_{datetime.now():%Y%m%d_%H%M%S}.csv",
                    mime="text/csv",
                )

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 – STANDARDS REFERENCE
# ══════════════════════════════════════════════════════════════════════════════
with tab_ref:
    st.markdown("### 📚 Aerospace Standards Reference")

    for std_key, std_data in STANDARDS.items():
        with st.expander(f"**{std_key}** – {std_data['full_name']}", expanded=False):
            dal_badges = " ".join(
                f"<span class='std-badge'>{d}</span>"
                for d in std_data.get("dal_applicability", [])
            )
            st.markdown(f"**Applicable DALs:** {dal_badges}", unsafe_allow_html=True)

            clause_rows = [
                {"Clause": c, "Description": desc}
                for c, desc in std_data.get("clauses", {}).items()
            ]
            if clause_rows:
                st.dataframe(
                    pd.DataFrame(clause_rows), hide_index=True, width='content'
                )

    st.divider()
    st.markdown("### 🔢 DO-178C Design Assurance Levels")
    dal_rows = []
    for k, v in DAL_MAP.items():
        dal_rows.append({
            "DAL": k,
            "Failure Condition": v["label"],
            "Test Priority":     v["priority"],
            "MC/DC Required":    "Yes" if k in ("DAL-A",) else
                                 "Recommended" if k == "DAL-B" else "No",
        })
    st.dataframe(pd.DataFrame(dal_rows), hide_index=True, width='content')

    st.divider()
    st.markdown("### 🧪 Test Types")
    tt_rows = [{"Type": k, "Description": v} for k, v in TEST_TYPES.items()]
    st.dataframe(pd.DataFrame(tt_rows), hide_index=True, width='content')
