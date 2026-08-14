"""Polished PDF audit-report generation for PQC risk assessments."""

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#102A43")
BLUE = colors.HexColor("#1F6FEB")
PALE_BLUE = colors.HexColor("#EAF2FF")
TEXT = colors.HexColor("#243B53")
RISK_COLORS = {"High": colors.HexColor("#B42318"), "Medium": colors.HexColor("#B54708"), "Low": colors.HexColor("#027A48")}


def _footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D9E2EC"))
    canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#627D98"))
    canvas.drawString(18 * mm, 9 * mm, "AI-PQC Risk Assessment • Offline audit report")
    canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Page {document.page}")
    canvas.restoreState()


def _paragraph(value, style):
    return Paragraph(str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), style)


def generate_report(output_path, data, stats):
    """Create a readable multi-page PDF with summary cards and aligned tables."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=27, textColor=NAVY, spaceAfter=4)
    subtitle = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=9, leading=13, textColor=colors.HexColor("#627D98"))
    section = ParagraphStyle("Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, textColor=NAVY, spaceBefore=12, spaceAfter=7)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=8.5, leading=12, textColor=TEXT)
    small = ParagraphStyle("Small", parent=body, fontSize=7.5, leading=10)
    cell = ParagraphStyle("Cell", parent=body, fontSize=7.2, leading=9)
    centered = ParagraphStyle("Centered", parent=body, alignment=TA_CENTER, fontSize=8)

    story = [
        Paragraph("AI-PQC TLS Risk Assessment", title),
        Paragraph("Post-quantum readiness, prioritized migration guidance, and configuration-level evidence", subtitle),
        Spacer(1, 7),
    ]
    cards = [[
        [Paragraph("CONFIGURATIONS", small), Paragraph(f"<b>{stats['total']}</b>", ParagraphStyle("Count", parent=centered, fontSize=20, textColor=NAVY))],
        [Paragraph("HIGH RISK", small), Paragraph(f"<b>{stats['high']}</b>", ParagraphStyle("High", parent=centered, fontSize=20, textColor=RISK_COLORS["High"]))],
        [Paragraph("MEDIUM RISK", small), Paragraph(f"<b>{stats['medium']}</b>", ParagraphStyle("Medium", parent=centered, fontSize=20, textColor=RISK_COLORS["Medium"]))],
        [Paragraph("LOW RISK", small), Paragraph(f"<b>{stats['low']}</b>", ParagraphStyle("Low", parent=centered, fontSize=20, textColor=RISK_COLORS["Low"]))],
    ]]
    card_table = Table(cards, colWidths=[42 * mm] * 4)
    card_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE), ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BED3F3")), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white), ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story.extend([card_table, Spacer(1, 10), Paragraph("Executive summary", section)])
    priority = "Immediate action is required for high-risk configurations, especially weak RSA/DH keys, SHA-1 signatures, and incomplete cryptographic metadata."
    story.append(Paragraph(priority, body))
    story.append(Paragraph(f"Generated locally on {datetime.now().strftime('%d %b %Y, %H:%M')} • No external services were used.", subtitle))

    story.append(Paragraph("Migration priorities", section))
    priority_rows = [[_paragraph("Priority", cell), _paragraph("Action", cell), _paragraph("Reason", cell)]]
    priority_rows.extend([
        [_paragraph("1 · High", cell), _paragraph("Replace RSA/DH key exchange with a hybrid TLS design using NIST FIPS 203 ML-KEM.", cell), _paragraph("Classical public-key exchange is vulnerable to future quantum attacks.", cell)],
        [_paragraph("2 · Medium", cell), _paragraph("Upgrade TLS 1.2 endpoints and CBC suites to TLS 1.3 AEAD configurations.", cell), _paragraph("Improves crypto-agility and prepares systems for PQC migration.", cell)],
        [_paragraph("3 · Low", cell), _paragraph("Maintain inventory and review configurations periodically.", cell), _paragraph("Supports continuous PQC readiness monitoring.", cell)],
    ])
    priorities = Table(priority_rows, colWidths=[27 * mm, 80 * mm, 61 * mm], repeatRows=1)
    priorities.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 1), (-1, -1), colors.white), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.extend([priorities, Paragraph("Configuration assessment", section)])

    headers = ["#", "TLS", "Key exchange / size", "Risk", "Confidence", "Findings", "Recommended action"]
    rows = [[_paragraph(header, cell) for header in headers]]
    for index, (_, row) in enumerate(data.iterrows(), start=1):
        risk = str(row.get("predicted_risk", "Unknown"))
        confidence = f"{float(row.get('risk_confidence', 0)):.0%}"
        key = f"{row.get('key_exchange_algorithm', '—')} / {row.get('key_size', '—')}"
        rows.append([
            _paragraph(index, cell), _paragraph(row.get("protocol_version", "—"), cell), _paragraph(key, cell),
            _paragraph(f"<font color='{RISK_COLORS.get(risk, TEXT).hexval()}'><b>{risk}</b></font>", cell), _paragraph(confidence, cell),
            _paragraph(row.get("rule_findings", "No issues"), cell), _paragraph(row.get("recommendations", "No action required"), cell),
        ])
    assessment = LongTable(rows, colWidths=[8 * mm, 15 * mm, 27 * mm, 16 * mm, 18 * mm, 43 * mm, 41 * mm], repeatRows=1)
    assessment.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E2EC")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story.append(assessment)
    document = SimpleDocTemplate(str(destination), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=17 * mm, bottomMargin=20 * mm, title="AI-PQC TLS Risk Assessment")
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
