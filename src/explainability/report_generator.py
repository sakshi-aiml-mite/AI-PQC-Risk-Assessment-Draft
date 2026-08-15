"""Dashboard-style PDF audit report generation."""

from datetime import datetime
from pathlib import Path

from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#0F172A")
MUTED = colors.HexColor("#475569")
TEXT = colors.HexColor("#1E293B")
PALE_BLUE = colors.HexColor("#EFF6FF")
PALE_NAVY = colors.HexColor("#EAF2FB")
RISK_COLORS = {"High": colors.HexColor("#DC2626"), "Medium": colors.HexColor("#D97706"), "Low": colors.HexColor("#059669")}


def _footer(canvas, document):
    width, _ = document.pagesize
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D9E2EC"))
    canvas.line(14 * mm, 13 * mm, width - 14 * mm, 13 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(14 * mm, 8 * mm, "AI-PQC Risk Assessment | Offline audit report")
    canvas.drawRightString(width - 14 * mm, 8 * mm, f"Page {document.page}")
    canvas.restoreState()


def _safe(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _p(value, style):
    return Paragraph(_safe(value), style)


def _risk_pie(stats):
    total = max(stats.get("total", 0), 1)
    values = [stats.get("high", 0), stats.get("medium", 0), stats.get("low", 0)]
    drawing = Drawing(150, 110)
    pie = Pie()
    pie.x = 20
    pie.y = 15
    pie.width = 80
    pie.height = 80
    pie.data = values
    pie.labels = ["High", "Medium", "Low"]
    pie.startAngle = 90
    pie.simpleLabels = 0
    pie.sideLabels = 1
    pie.slices.strokeWidth = 0.5
    pie.slices.strokeColor = HexColor("#F8FAFC")
    for index, color in enumerate([RISK_COLORS["High"], RISK_COLORS["Medium"], RISK_COLORS["Low"]]):
        pie.slices[index].fillColor = color
    drawing.add(pie)
    return drawing


def _risk_bar(stats):
    values = [stats.get("high", 0), stats.get("medium", 0), stats.get("low", 0)]
    drawing = Drawing(180, 110)
    maximum = max(max(values), 1)
    for index, (label, value) in enumerate(zip(["High", "Medium", "Low"], values)):
        x = 25 + (index * 44)
        height = (value / maximum) * 58
        drawing.add(Rect(x, 24, 26, height, fillColor=RISK_COLORS[label], strokeColor=colors.white, strokeWidth=.4))
        drawing.add(String(x + 4, 11, label, fontName="Helvetica-Bold", fontSize=7, fillColor=TEXT))
        drawing.add(String(x + 9, 86, str(value), fontName="Helvetica-Bold", fontSize=8, fillColor=TEXT))
    return drawing


def _risk_heatmap(stats):
    """A compact, print-friendly risk intensity heatmap."""
    total = max(stats.get("total", 0), 1)
    tiers = [("High", stats.get("high", 0)), ("Medium", stats.get("medium", 0)), ("Low", stats.get("low", 0))]
    drawing = Drawing(290, 112)
    drawing.add(String(8, 96, "Risk concentration", fontName="Helvetica-Bold", fontSize=10, fillColor=NAVY))
    for index, (label, count) in enumerate(tiers):
        y = 68 - (index * 23)
        intensity = min(.20 + (count / total) * .80, 1)
        base = RISK_COLORS[label]
        fill = colors.Color(base.red, base.green, base.blue, alpha=intensity)
        drawing.add(String(8, y + 5, label, fontName="Helvetica-Bold", fontSize=8, fillColor=TEXT))
        drawing.add(Rect(68, y, 160, 15, fillColor=fill, strokeColor=colors.white, strokeWidth=.4))
        drawing.add(String(238, y + 4, f"{count}  ({count / total:.0%})", fontName="Helvetica", fontSize=8, fillColor=TEXT))
    return drawing


def generate_report(output_path, data, stats):
    """Create a professional, executive-ready PDF with sector-style charts and risk narrative."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=NAVY)
    subtitle = ParagraphStyle("subtitle", parent=styles["Normal"], fontSize=9, leading=13, textColor=MUTED)
    section = ParagraphStyle("section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=NAVY, spaceBefore=13, spaceAfter=7)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9, leading=12, textColor=TEXT)
    card_label = ParagraphStyle("card_label", parent=body, alignment=TA_CENTER, fontSize=7.5, leading=10, textColor=MUTED)
    card_count = ParagraphStyle("card_count", parent=body, alignment=TA_CENTER, fontSize=20, leading=24, textColor=NAVY)
    cell = ParagraphStyle("cell", parent=body, fontSize=7.6, leading=9.6)
    header = ParagraphStyle("header", parent=cell, textColor=colors.white, fontName="Helvetica-Bold")

    total = stats.get("total", 0)
    high = stats.get("high", 0)
    medium = stats.get("medium", 0)
    low = stats.get("low", 0)
    readiness = round(((low + (medium * 0.45)) / max(total, 1)) * 100)
    summary_text = "This report presents the TLS inventory's quantum-readiness posture, the distribution of risk tiers, and prioritized migration actions."

    story = [
        Paragraph("AI-PQC TLS Risk Assessment", title),
        Paragraph("Executive readiness review | locally generated audit evidence", subtitle),
        Spacer(1, 8),
    ]

    card_data = [[
        [Paragraph("CONFIGURATIONS", card_label), Paragraph(f"<b>{total}</b>", card_count)],
        [Paragraph("HIGH RISK", card_label), Paragraph(f"<b>{high}</b>", ParagraphStyle("high", parent=card_count, textColor=RISK_COLORS["High"]))],
        [Paragraph("MEDIUM RISK", card_label), Paragraph(f"<b>{medium}</b>", ParagraphStyle("medium", parent=card_count, textColor=RISK_COLORS["Medium"]))],
        [Paragraph("LOW RISK", card_label), Paragraph(f"<b>{low}</b>", ParagraphStyle("low", parent=card_count, textColor=RISK_COLORS["Low"]))],
    ]]
    cards = Table(card_data, colWidths=[63 * mm] * 4)
    cards.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE_NAVY),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#BED3F3")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([cards, Paragraph("Executive summary", section), Paragraph(summary_text, body), Paragraph(f"Generated locally on {datetime.now().strftime('%d %b %Y, %H:%M')}.", subtitle)])

    chart_heading = ParagraphStyle("chart_section", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10, textColor=NAVY)
    chart_table = Table([
        [Paragraph("Distribution by tier", chart_heading), Paragraph("Risk heatmap", chart_heading)],
        [_risk_pie(stats), _risk_heatmap(stats)],
        [Paragraph("Volume by tier", chart_heading), Paragraph("", body)],
        [_risk_bar(stats), Paragraph("Heat intensity reflects each tier's share of the assessed inventory.", body)],
    ], colWidths=[120 * mm, 160 * mm])
    chart_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), colors.white), ("LINEBELOW", (0, 0), (-1, 0), .3, HexColor("#D9E2EC")), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.extend([Paragraph("Risk profile", section), chart_table])

    story.append(Paragraph("Key observations", section))
    insights = [
        f"Readiness posture is estimated at {readiness}% based on current Low and Medium risk distribution.",
        f"{high} configuration(s) remain in the High risk queue and should be prioritized in the remediation schedule.",
        "Prioritize crypto-agility, hybrid migration planning, and protocol modernization.",
    ]
    for line in insights:
        story.append(Paragraph(f"• {line}", body))

    story.append(Paragraph("Migration priorities", section))
    priorities = [
        [_p("Priority", header), _p("Recommended action", header), _p("Expected outcome", header)],
        [_p("High", cell), _p("Replace RSA/DH key exchange with hybrid post-quantum-friendly TLS design and ML-KEM planning.", cell), _p("Reduces vulnerability to future quantum decryption risk.", cell)],
        [_p("Medium", cell), _p("Upgrade TLS 1.2 and CBC suites to TLS 1.3 with AEAD-protected ciphers.", cell), _p("Improves resilience and reduces compatibility risk.", cell)],
        [_p("Low", cell), _p("Track key inventory and repeat review cycles across the next quarterly audit.", cell), _p("Maintains a current roadmap and governance rhythm.", cell)],
    ]
    priority_table = Table(priorities, colWidths=[35 * mm, 130 * mm, 87 * mm], repeatRows=1)
    priority_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([priority_table, Paragraph("Configuration assessment", section)])

    rows = [[_p(label, header) for label in ["#", "TLS", "Key exchange", "Key size", "Risk", "Confidence", "Findings", "Recommended action"]]]
    for index, (_, row) in enumerate(data.iterrows(), start=1):
        risk = str(row.get("predicted_risk", "Unknown"))
        risk_color = RISK_COLORS.get(risk, TEXT).hexval()
        rows.append([
            _p(index, cell),
            _p(row.get("protocol_version", "-"), cell),
            _p(row.get("key_exchange_algorithm", "-"), cell),
            _p(row.get("key_size", "-"), cell),
            Paragraph(f"<font color='{risk_color}'><b>{_safe(risk)}</b></font>", cell),
            _p(f"{float(row.get('risk_confidence', 0)):.0%}", cell),
            _p(row.get("rule_findings", "No issues"), cell),
            _p(row.get("recommendations", "No action required"), cell),
        ])
    assessment = LongTable(rows, colWidths=[8 * mm, 19 * mm, 30 * mm, 18 * mm, 19 * mm, 22 * mm, 65 * mm, 71 * mm], repeatRows=1)
    assessment.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E2EC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
    ]))
    story.append(assessment)

    document = SimpleDocTemplate(str(destination), pagesize=landscape(A4), leftMargin=14 * mm, rightMargin=14 * mm, topMargin=16 * mm, bottomMargin=19 * mm, title="AI-PQC TLS Risk Assessment")
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
