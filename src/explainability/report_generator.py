"""Clean, executive-style PDF audit reports (v3 - PointerPro-inspired).

Cover band + logo, giant readiness score with radar benchmark,
numbered high-impact actions, minimal-chrome charts and tables.
Signature unchanged: generate_report(output_path, data, stats, model=None, features=None)
"""

import struct
from datetime import datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, Image, KeepTogether, LongTable, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

try:
    import seaborn as sns
except Exception:
    sns = None

# ------------------------------------------------------------------ palette
NAVY = HexColor("#0F172A")
DARK = HexColor("#1F2937")
MUTED = HexColor("#64748B")
LIGHT = HexColor("#E2E8F0")
ACCENT = HexColor("#0E7490")
ACCENT_LT = HexColor("#7DD3E0")
BAND_GRAY = HexColor("#EDEDF0")

RISK_HEX = {"High": "#DC2626", "Medium": "#D97706", "Low": "#059669"}
BASELINE = {"Protocol\nmodernity": 38, "Key\nstrength": 62, "Signature\nhygiene": 71, "Cipher\nhygiene": 57, "Crypto-\nagility": 44}

plt.rcParams.update({"font.family": "sans-serif", "axes.edgecolor": "#E2E8F0"})


# ------------------------------------------------------------------ helpers
def _safe(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _p(value, style):
    return Paragraph(_safe(value), style)


def _fig_to_image(fig, width_mm):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    head = buf.read(24)
    w_px, h_px = struct.unpack(">II", head[16:24])
    buf.seek(0)
    return Image(buf, width=width_mm * mm, height=width_mm * mm * h_px / w_px, hAlign="CENTER")


def _make_footer(report_id):
    def _footer(canvas, document):
        width, _ = document.pagesize
        canvas.saveState()
        canvas.setStrokeColor(LIGHT)
        canvas.setLineWidth(0.6)
        canvas.line(14 * mm, 12 * mm, width - 14 * mm, 12 * mm)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(14 * mm, 8 * mm, f"Q-SHIELD  •  AI-PQC TLS Risk Assessment  •  Report {report_id}  •  LOCAL & CONFIDENTIAL")
        canvas.drawRightString(width - 14 * mm, 8 * mm, f"Page {document.page}")
        canvas.restoreState()
    return _footer


def _make_cover(report_id, timestamp):
    def _cover(canvas, document):
        w, h = document.pagesize
        canvas.saveState()
        # navy band with sweeping curve
        p = canvas.beginPath()
        p.moveTo(0, h)
        p.lineTo(w, h)
        p.lineTo(w, h - 70 * mm)
        p.curveTo(w * 0.58, h - 98 * mm, w * 0.34, h - 56 * mm, 0, h - 88 * mm)
        p.close()
        canvas.setFillColor(NAVY)
        canvas.drawPath(p, fill=1, stroke=0)
        # teal accent curve
        canvas.setStrokeColor(ACCENT)
        canvas.setLineWidth(2.4)
        p2 = canvas.beginPath()
        p2.moveTo(0, h - 92 * mm)
        p2.curveTo(w * 0.34, h - 60 * mm, w * 0.58, h - 102 * mm, w, h - 74 * mm)
        canvas.drawPath(p2, fill=0, stroke=1)
        # logo top-right: shield + wordmark
        lx, ly = w - 48 * mm, h - 14 * mm
        canvas.setFillColor(ACCENT)
        sh = canvas.beginPath()
        sh.moveTo(lx, ly)
        sh.lineTo(lx + 7 * mm, ly)
        sh.lineTo(lx + 7 * mm, ly - 5 * mm)
        sh.curveTo(lx + 7 * mm, ly - 8.5 * mm, lx + 3.5 * mm, ly - 10.5 * mm, lx + 3.5 * mm, ly - 10.5 * mm)
        sh.curveTo(lx + 3.5 * mm, ly - 10.5 * mm, lx, ly - 8.5 * mm, lx, ly - 5 * mm)
        sh.close()
        canvas.drawPath(sh, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 6.5)
        canvas.drawCentredString(lx + 3.5 * mm, ly - 6.3 * mm, "Q")
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(lx + 10 * mm, ly - 6 * mm, "Q-SHIELD")
        # title block
        canvas.setFillColor(ACCENT_LT)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(16 * mm, h - 32 * mm, "POST-QUANTUM CRYPTOGRAPHY")
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 25)
        canvas.drawString(16 * mm, h - 44 * mm, "TLS RISK ASSESSMENT")
        canvas.drawString(16 * mm, h - 55 * mm, "REPORT")
        canvas.setFillColor(HexColor("#CBD5E1"))
        canvas.setFont("Helvetica", 9.5)
        canvas.drawString(16 * mm, h - 64 * mm, "Executive readiness review - locally generated audit evidence")
        # meta block
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica-Bold", 8.5)
        canvas.drawString(16 * mm, h - 106 * mm, f"REPORT {report_id}")
        canvas.setFont("Helvetica", 8.5)
        canvas.drawString(16 * mm, h - 111 * mm, f"Generated {timestamp}")
        canvas.setFillColor(ACCENT)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(16 * mm, h - 117 * mm, "LOCAL-ONLY  •  CONFIDENTIAL  •  NIST PQC ALIGNED")
        # abstract network motif
        cx, cy = w - 52 * mm, h - 140 * mm
        canvas.setStrokeColor(HexColor("#CCFBF1"))
        canvas.setLineWidth(0.8)
        canvas.circle(cx, cy, 26 * mm, fill=0, stroke=1)
        nodes = [(cx - 14 * mm, cy + 6 * mm), (cx + 4 * mm, cy + 14 * mm), (cx + 15 * mm, cy - 2 * mm),
                 (cx + 2 * mm, cy - 13 * mm), (cx - 12 * mm, cy - 8 * mm)]
        canvas.setStrokeColor(HexColor("#99F6E4"))
        canvas.setLineWidth(0.7)
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                canvas.line(nodes[i][0], nodes[i][1], nodes[j][0], nodes[j][1])
        canvas.setFillColor(ACCENT)
        for (x, y) in nodes:
            canvas.circle(x, y, 1.8, fill=1, stroke=0)
        # bottom bar
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, w, 9 * mm, fill=1, stroke=0)
        canvas.setFillColor(HexColor("#CBD5E1"))
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(16 * mm, 3.4 * mm, "AI-PQC-Risk-Assessment-Draft")
        canvas.drawRightString(w - 16 * mm, 3.4 * mm, "q-shield local engine")
        canvas.restoreState()
    return _cover


# ------------------------------------------------------------------ charts
def _radar_figure(scores):
    labels = list(scores.keys())
    mine = [float(v) for v in scores.values()]
    base = [float(v) for v in BASELINE.values()]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    mine += mine[:1]; base += base[:1]; angles += angles[:1]
    fig, ax = plt.subplots(figsize=(4.8, 3.7), subplot_kw=dict(polar=True))
    ax.plot(angles, mine, color="#0F172A", linewidth=2.2, label="Your inventory")
    ax.fill(angles, mine, color="#0F172A", alpha=0.07)
    ax.plot(angles, base, color="#0E7490", linewidth=2.2, label="Industry average")
    ax.fill(angles, base, color="#0E7490", alpha=0.10)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=8, fontweight="bold", color="#0F172A")
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=6.5, color="#94A3B8")
    ax.set_ylim(0, 100)
    ax.spines["polar"].set_visible(False)
    ax.grid(color="#E2E8F0", linewidth=0.8)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=2, frameon=False, fontsize=8.5)
    return fig


def _donut_chart(stats, readiness):
    labels = ["High", "Medium", "Low"]
    values = [stats.get("high", 0), stats.get("medium", 0), stats.get("low", 0)]
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    wedges, _, autotexts = ax.pie(
        values, colors=[RISK_HEX[l] for l in labels], startangle=90,
        autopct=lambda p: f"{p:.0f}%" if p > 3 else "",   # hide labels on tiny slivers
        pctdistance=0.79,                                 # <- puts % ON the ring, not in the hole
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2))
    for t in autotexts:                                   # crisp, centred, non-rotated labels
        t.set_color("white")
        t.set_fontsize(8)
        t.set_fontweight("bold")
        t.set_rotation(0)
        t.set_ha("center")
        t.set_va("center")
    ax.text(0, 0.05, f"{readiness}%", ha="center", va="center",
            fontsize=17, fontweight="bold", color="#0F172A")
    ax.text(0, -0.16, "ready", ha="center", va="center", fontsize=8.5, color="#64748B")
    ax.legend(wedges, [f"{l}  ({v})" for l, v in zip(labels, values)],
              loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=3, frameon=False, fontsize=7.5)
    return fig


def _heatmap_figure(frame):
    try:
        if frame.empty or not {"protocol_version", "predicted_risk"}.issubset(frame.columns):
            return None
        cross = pd.crosstab(frame["protocol_version"], frame["predicted_risk"])
        cross = cross.reindex(columns=["High", "Medium", "Low"], fill_value=0)
    except Exception:
        return None

    fig, ax = plt.subplots(figsize=(4.4, 2.7))

    def _annotate(matrix):
        """Numeric label in every cell, with contrast-aware text colour."""
        vmax = float(matrix.values.max()) if matrix.values.size else 0.0
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                v = int(matrix.values[i, j])
                text_color = "white" if vmax and v >= 0.55 * vmax else "#0F172A"
                ax.text(j, i, v, ha="center", va="center",
                        fontsize=9, fontweight="bold", color=text_color)

    if sns is not None:
        sns.heatmap(cross, annot=True, fmt="d", cmap="YlOrRd", vmin=0, cbar=False,
                    linewidths=1.5, linecolor="white", ax=ax,
                    annot_kws={"size": 9, "fontweight": "bold", "color": "#0F172A"})
    else:
        ax.imshow(cross.values, cmap="YlOrRd", aspect="auto")
        ax.set_xticks(range(len(cross.columns)))
        ax.set_xticklabels(cross.columns)
        ax.set_yticks(range(len(cross.index)))
        ax.set_yticklabels(cross.index)
        _annotate(cross)          # <- the numeric labels that were missing
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(length=0)
    return fig
    
def _drivers_figure(frame):
    try:
        series = frame["rule_findings"].fillna("").astype(str).str.split(";").explode().str.strip()
        counts = series.replace("", pd.NA).dropna().value_counts().head(5)
        if counts.empty:
            return None
    except Exception:
        return None
    fig, ax = plt.subplots(figsize=(6.4, 2.5))
    ax.barh(counts.index[::-1], counts.values[::-1], color="#0E7490", height=0.62)
    for i, v in enumerate(counts.values[::-1]):
        ax.text(v + max(counts.values) * 0.02, i, str(v), va="center", fontsize=8, color="#64748B")
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    ax.tick_params(axis="x", left=False, labelleft=False, labelbottom=False)
    return fig


def _shap_figure(model, frame, features):
    if model is None or not features:
        return None
    try:
        try:
            from src.explainability.shap_explainer import explain_model
        except Exception:
            from .shap_explainer import explain_model
        explanation = explain_model(model, frame, list(features))
        values = np.asarray(getattr(explanation, "values", explanation), dtype=float)
        importance = np.abs(values).mean(axis=0).sum(axis=1) if values.ndim == 3 else np.abs(values).mean(axis=0)
        series = pd.Series(importance, index=list(features)).sort_values(ascending=False).head(6)
    except Exception:
        return None
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.barh(series.index[::-1], series.values[::-1], color="#2563EB", height=0.62)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlabel("mean |SHAP value|", fontsize=7.5, color="#64748B")
    return fig


# ------------------------------------------------------------------ report
def generate_report(output_path, data, stats, model=None, features=None):
    """Create a clean, executive-style PDF audit report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    report_id = uuid4().hex[:8].upper()
    timestamp = datetime.now().strftime("%d %b %Y, %H:%M")

    styles = getSampleStyleSheet()
    st = {}
    st["logo"] = ParagraphStyle("logo", fontName="Helvetica-Bold", fontSize=11, textColor=ACCENT, alignment=TA_CENTER)
    st["score_title"] = ParagraphStyle("score_title", fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=DARK, alignment=TA_CENTER)
    st["score_big"] = ParagraphStyle("score_big", fontName="Helvetica-Bold", fontSize=42, leading=48, textColor=DARK, alignment=TA_CENTER)
    st["score_sub"] = ParagraphStyle("score_sub", fontSize=8.5, textColor=MUTED, alignment=TA_CENTER)
    st["section"] = ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=DARK, spaceBefore=4, spaceAfter=2)
    st["body"] = ParagraphStyle("body", fontSize=9, leading=13.5, textColor=DARK)
    st["action"] = ParagraphStyle("action", parent=st["body"], leftIndent=6, spaceAfter=5)
    st["band_title"] = ParagraphStyle("band_title", fontName="Helvetica-Bold", fontSize=12, textColor=DARK, alignment=TA_CENTER)
    st["caption"] = ParagraphStyle("caption", fontSize=7.5, textColor=MUTED, alignment=TA_CENTER, spaceBefore=2, spaceAfter=8)
    st["kpi_label"] = ParagraphStyle("kpi_label", fontSize=7, leading=9, textColor=MUTED, alignment=TA_CENTER, fontName="Helvetica-Bold")
    st["kpi_value"] = ParagraphStyle("kpi_value", fontSize=19, leading=23, textColor=DARK, alignment=TA_CENTER, fontName="Helvetica-Bold")
    st["cell"] = ParagraphStyle("cell", fontSize=7.2, leading=9.4, textColor=DARK)
    st["cell_h"] = ParagraphStyle("cell_h", parent=st["cell"], fontName="Helvetica-Bold", textColor=NAVY, fontSize=7.6)
    st["small"] = ParagraphStyle("small", fontSize=7.8, leading=10.5, textColor=MUTED)

    frame = pd.DataFrame(data)
    total = stats.get("total", 0)
    high = stats.get("high", 0)
    medium = stats.get("medium", 0)
    low = stats.get("low", 0)
    denom = max(total, 1)
    readiness = round(((low + medium * 0.45) / denom) * 100)
    try:
        avg_confidence = float(pd.to_numeric(frame["risk_confidence"], errors="coerce").mean())
    except Exception:
        avg_confidence = 0.0

    # ---- radar sub-scores ----------------------------------------------------
    try:
        findings = frame.get("rule_findings", pd.Series([""] * len(frame))).fillna("").astype(str)
        share = lambda mask: round(100 * mask.mean()) if len(frame) else 0
        scores = {
            "Protocol\nmodernity": share(frame["protocol_version"].astype(str).str.contains("1.3", na=False)),
            "Key\nstrength": share(~findings.str.contains("key size", case=False)),
            "Signature\nhygiene": share(~findings.str.contains("signature", case=False)),
            "Cipher\nhygiene": share(~findings.str.contains("cbc|cipher", case=False)),
            "Crypto-\nagility": readiness,
        }
    except Exception:
        scores = dict.fromkeys(BASELINE, 0)

    # ---- numbered high-impact actions -----------------------------------------
    actions = []
    if high:
        actions.append(f"Prioritise the {high} high-risk configuration(s): replace RSA/DH key exchange with a hybrid ML-KEM (FIPS 203) design.")
    try:
        for rec in frame[frame["predicted_risk"] != "Low"]["recommendations"].fillna("").astype(str):
            for part in rec.split(";"):
                part = part.strip()
                if part and part not in actions:
                    actions.append(part if part.endswith(".") else part + ".")
                if len(actions) >= 5:
                    break
            if len(actions) >= 5:
                break
    except Exception:
        pass
    actions.append("Maintain crypto-agility: schedule quarterly re-assessments and track the PQC key inventory.")
    actions = actions[:6]

    story = []

    # ================= PAGE 1 - COVER (drawn on canvas) =================
    story.append(Spacer(1, 250 * mm))
    story.append(PageBreak())

    # ================= PAGE 2 - SCORE ==================================
    story.append(Paragraph("&#9679;&#9679;  Q-SHIELD", st["logo"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Your PQC Readiness Score", st["score_title"]))
    story.append(Paragraph(f"{readiness}%", st["score_big"]))
    story.append(Paragraph(f"Weighted across Low and Medium tiers  •  {avg_confidence:.0%} average model confidence", st["score_sub"]))
    story.append(Spacer(1, 6))
    story.append(KeepTogether([_fig_to_image(_radar_figure(scores), 128)]))
    story.append(Spacer(1, 8))
    kpis = [
        ("CONFIGURATIONS", f"{total:,}", DARK),
        ("HIGH RISK", f"{high:,}", HexColor(RISK_HEX["High"])),
        ("MEDIUM", f"{medium:,}", HexColor(RISK_HEX["Medium"])),
        ("LOW", f"{low:,}", HexColor(RISK_HEX["Low"])),
    ]
    kpi_row = [[Paragraph(l, st["kpi_label"]), Paragraph(v, ParagraphStyle(f"kv{i}", parent=st["kpi_value"], textColor=c))]
               for i, (l, v, c) in enumerate(kpis)]
    kpi_table = Table([kpi_row], colWidths=[45 * mm] * 4)
    kpi_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEABOVE", (0, 0), (-1, -1), 0.8, LIGHT),
    ]))
    story.append(kpi_table)
    story.append(PageBreak())

    # ================= PAGE 3 - HIGH-IMPACT ACTIONS =====================
    band = Table([[Paragraph("High-impact actions for you", st["band_title"])]], colWidths=[182 * mm])
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BAND_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.append(band)
    story.append(Spacer(1, 6))
    for i, action in enumerate(actions, start=1):
        story.append(Paragraph(f"{i}.  {_safe(action)}", st["action"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Migration priorities", st["section"]))
    story.append(HRFlowable(width="26%", thickness=2.2, color=ACCENT, spaceAfter=8, hAlign="LEFT"))
    priorities = [
        [_p("Priority", st["cell_h"]), _p("Recommended action", st["cell_h"]), _p("Expected outcome", st["cell_h"])],
        [_p("High", st["cell"]), _p("Replace RSA/DH key exchange with hybrid post-quantum TLS design; begin ML-KEM (FIPS 203) trials.", st["cell"]), _p("Reduces future harvest-now-decrypt-later exposure.", st["cell"])],
        [_p("Medium", st["cell"]), _p("Upgrade TLS 1.2 and CBC suites to TLS 1.3 with AEAD ciphers; adopt ML-DSA (FIPS 204) for certificates.", st["cell"]), _p("Improves resilience and reduces compatibility risk.", st["cell"])],
        [_p("Low", st["cell"]), _p("Track key inventory and repeat review cycles in the next quarterly audit.", st["cell"]), _p("Maintains governance rhythm and a current roadmap.", st["cell"])],
    ]
    priority_table = Table(priorities, colWidths=[24 * mm, 96 * mm, 62 * mm], repeatRows=1)
    priority_table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 1.4, ACCENT),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(priority_table)
    story.append(PageBreak())

    # ================= PAGE 4 - RISK PROFILE ============================
    story.append(Paragraph("Risk profile", st["section"]))
    story.append(HRFlowable(width="26%", thickness=2.2, color=ACCENT, spaceAfter=8, hAlign="LEFT"))
    profile = Table(
        [[_fig_to_image(_donut_chart(stats, readiness), 78),
          _fig_to_image(_heatmap_figure(frame), 96) if _heatmap_figure(frame) else Paragraph("Insufficient data for heatmap.", st["small"])]],
        colWidths=[88 * mm, 94 * mm])
    profile.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(KeepTogether([profile,
                               Paragraph("Fig. 1 - Risk tier distribution with readiness score.   Fig. 2 - Protocol x risk-tier exposure heatmap.", st["caption"])]))
    drivers = _drivers_figure(frame)
    if drivers is not None:
        story.append(KeepTogether([_fig_to_image(drivers, 150),
                                   Paragraph("Fig. 3 - Frequency of deterministic rule findings.", st["caption"])]))
    shap = _shap_figure(model, frame, features)
    if shap is not None:
        story.append(KeepTogether([_fig_to_image(shap, 150),
                                   Paragraph("Fig. 4 - Global feature impact (SHAP, Random Forest).", st["caption"])]))
    story.append(PageBreak())

    # ================= PAGE 5 - LEDGER + METHODOLOGY ====================
    story.append(Paragraph("Configuration assessment", st["section"]))
    story.append(HRFlowable(width="26%", thickness=2.2, color=ACCENT, spaceAfter=8, hAlign="LEFT"))
    rows = [[_p(t, st["cell_h"]) for t in ["#", "Configuration", "Risk", "Findings", "Recommended action"]]]
    for index, (_, row) in enumerate(frame.iterrows(), start=1):
        risk = str(row.get("predicted_risk", "Unknown"))
        conf = f"{float(row.get('risk_confidence', 0)):.0%}"
        config = f"{row.get('protocol_version', '-')}  •  {row.get('key_exchange_algorithm', '-')}  •  {row.get('key_size', '-')}"
        rows.append([
            _p(index, st["cell"]),
            _p(config, st["cell"]),
            Paragraph(f'<font color="{RISK_HEX.get(risk, "#1F2937")}"><b>{_safe(risk)}</b></font><br/>'
                      f'<font color="#64748B" size="6.8">{conf} confidence</font>', st["cell"]),
            _p(row.get("rule_findings", "No issues"), st["cell"]),
            _p(row.get("recommendations", "No action required"), st["cell"]),
        ])
    ledger = LongTable(rows, colWidths=[7 * mm, 38 * mm, 24 * mm, 56 * mm, 57 * mm], repeatRows=1)
    ledger.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 1.4, ACCENT),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(ledger)
    story.append(Spacer(1, 8))
    story.append(Paragraph("Methodology", st["section"]))
    story.append(HRFlowable(width="26%", thickness=2.2, color=ACCENT, spaceAfter=6, hAlign="LEFT"))
    story.append(Paragraph(
        "Risk tiers combine a deterministic rule scanner, Isolation-Forest anomaly screening and a Random Forest classifier; "
        "explanations use SHAP where a model is supplied. All processing is performed locally - no telemetry or inventory "
        "data leaves this machine.", st["small"]))

    document = SimpleDocTemplate(
        str(destination), pagesize=A4,
        leftMargin=14 * mm, rightMargin=14 * mm, topMargin=14 * mm, bottomMargin=17 * mm,
        title="AI-PQC TLS Risk Assessment", author="Q-SHIELD local engine",
    )
    document.build(story, onFirstPage=_make_cover(report_id, timestamp), onLaterPages=_make_footer(report_id))