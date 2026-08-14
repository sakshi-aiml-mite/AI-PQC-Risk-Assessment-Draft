"""Dashboard-style PDF audit report generation."""

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#102A43")
MUTED = colors.HexColor("#627D98")
TEXT = colors.HexColor("#243B53")
PALE_BLUE = colors.HexColor("#EAF2FF")
RISK_COLORS = {"High": colors.HexColor("#B42318"), "Medium": colors.HexColor("#B54708"), "Low": colors.HexColor("#027A48")}


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


def generate_report(output_path, data, stats):
    """Create a clean landscape PDF that mirrors the dashboard hierarchy."""
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

    story = [
        Paragraph("AI-PQC TLS Risk Assessment", title),
        Paragraph("Post-quantum readiness assessment, migration priorities, and configuration evidence", subtitle),
        Spacer(1, 7),
    ]
    card_data = [[
        [Paragraph("CONFIGURATIONS", card_label), Paragraph(f"<b>{stats['total']}</b>", card_count)],
        [Paragraph("HIGH RISK", card_label), Paragraph(f"<b>{stats['high']}</b>", ParagraphStyle("high", parent=card_count, textColor=RISK_COLORS["High"]))],
        [Paragraph("MEDIUM RISK", card_label), Paragraph(f"<b>{stats['medium']}</b>", ParagraphStyle("medium", parent=card_count, textColor=RISK_COLORS["Medium"]))],
        [Paragraph("LOW RISK", card_label), Paragraph(f"<b>{stats['low']}</b>", ParagraphStyle("low", parent=card_count, textColor=RISK_COLORS["Low"]))],
    ]]
    cards = Table(card_data, colWidths=[63 * mm] * 4)
    cards.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE), ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BED3F3")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([cards, Paragraph("Executive summary", section)])
    story.append(Paragraph("This locally generated report prioritizes configurations that retain quantum-vulnerable public-key cryptography or deprecated TLS settings. Address High risk items first, then use the recommended actions to improve crypto-agility.", body))
    story.append(Paragraph(f"Generated locally on {datetime.now().strftime('%d %b %Y, %H:%M')}. No assessment data left this computer.", subtitle))

    story.append(Paragraph("Migration priorities", section))
    priorities = [
        [_p("Priority", header), _p("Recommended action", header), _p("Outcome", header)],
        [_p("High", cell), _p("Replace RSA/DH key exchange with a hybrid TLS design using NIST FIPS 203 ML-KEM.", cell), _p("Reduces exposure to future quantum attacks.", cell)],
        [_p("Medium", cell), _p("Upgrade TLS 1.2 endpoints and CBC suites to TLS 1.3 AEAD configurations.", cell), _p("Improves crypto-agility before PQC rollout.", cell)],
        [_p("Low", cell), _p("Maintain the inventory and review configurations periodically.", cell), _p("Keeps the migration plan current.", cell)],
    ]
    priority_table = Table(priorities, colWidths=[35 * mm, 130 * mm, 87 * mm], repeatRows=1)
    priority_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([priority_table, Paragraph("Configuration assessment", section)])

    rows = [[_p(label, header) for label in ["#", "TLS", "Key exchange", "Key size", "Risk", "Confidence", "Findings", "Recommended action"]]]
    for index, (_, row) in enumerate(data.iterrows(), start=1):
        risk = str(row.get("predicted_risk", "Unknown"))
        risk_color = RISK_COLORS.get(risk, TEXT).hexval()
        rows.append([
            _p(index, cell), _p(row.get("protocol_version", "-"), cell), _p(row.get("key_exchange_algorithm", "-"), cell), _p(row.get("key_size", "-"), cell),
            Paragraph(f"<font color='{risk_color}'><b>{_safe(risk)}</b></font>", cell), _p(f"{float(row.get('risk_confidence', 0)):.0%}", cell),
            _p(row.get("rule_findings", "No issues"), cell), _p(row.get("recommendations", "No action required"), cell),
        ])
    assessment = LongTable(rows, colWidths=[8 * mm, 19 * mm, 30 * mm, 18 * mm, 19 * mm, 22 * mm, 65 * mm, 71 * mm], repeatRows=1)
    assessment.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E2EC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
    ]))
    story.append(assessment)
    document = SimpleDocTemplate(str(destination), pagesize=landscape(A4), leftMargin=14 * mm, rightMargin=14 * mm, topMargin=16 * mm, bottomMargin=19 * mm, title="AI-PQC TLS Risk Assessment")
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
