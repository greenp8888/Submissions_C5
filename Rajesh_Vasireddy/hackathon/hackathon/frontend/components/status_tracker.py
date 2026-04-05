"""Pipeline progress widget – styled step tracker."""

from typing import List
import streamlit as st

PIPELINE_STEPS = ["classify", "remediate", "cookbook", "notify", "jira"]
STEP_META = {
    "classify":  ("Log Classifier",   "#3b82f6"),
    "remediate": ("Remediation",      "#6366f1"),
    "cookbook":  ("Cookbook",         "#8b5cf6"),
    "notify":    ("Notification",     "#f97316"),
    "jira":      ("JIRA Ticket",      "#ef4444"),
}


def status_tracker(completed_steps: List[str], current_step: str) -> None:
    """Render a styled horizontal pipeline progress bar."""
    total   = len(PIPELINE_STEPS)
    done    = len([s for s in PIPELINE_STEPS if s in completed_steps])
    pct     = done / total

    st.markdown(
        f"""<div style="margin-bottom:.6rem">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.4rem">
                <span style="color:#94a3b8;font-size:.75rem;font-weight:600;letter-spacing:.5px;text-transform:uppercase">
                    Pipeline Progress
                </span>
                <span style="color:#3b82f6;font-size:.75rem;font-weight:700">{done}/{total} steps</span>
            </div>
            <div style="background:#1a2540;border-radius:99px;height:6px;overflow:hidden">
                <div style="background:linear-gradient(90deg,#3b82f6,#8b5cf6);
                            width:{pct*100:.0f}%;height:100%;border-radius:99px;
                            transition:width .4s ease"></div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    cols = st.columns(total)
    for col, step in zip(cols, PIPELINE_STEPS):
        label, color = STEP_META[step]
        if step in completed_steps:
            col.markdown(
                f"""<div style="background:rgba({_hex_to_rgb(color)},.12);border:1px solid {color};
                                border-radius:10px;padding:.5rem .4rem;text-align:center">
                    <div style="color:{color};font-size:.9rem;font-weight:700">✓</div>
                    <div style="color:{color};font-size:.65rem;font-weight:600;margin-top:2px">{label}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        elif step == current_step:
            col.markdown(
                f"""<div style="background:rgba(234,179,8,.1);border:1px solid #eab308;
                                border-radius:10px;padding:.5rem .4rem;text-align:center">
                    <div style="color:#eab308;font-size:.9rem">⟳</div>
                    <div style="color:#eab308;font-size:.65rem;font-weight:600;margin-top:2px">{label}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            col.markdown(
                f"""<div style="background:#111827;border:1px solid #1e3a5f;
                                border-radius:10px;padding:.5rem .4rem;text-align:center">
                    <div style="color:#1e3a5f;font-size:.9rem">○</div>
                    <div style="color:#334155;font-size:.65rem;font-weight:600;margin-top:2px">{label}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"
