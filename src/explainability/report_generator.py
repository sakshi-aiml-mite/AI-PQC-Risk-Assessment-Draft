"""
report_generator.py
Generates PDF reports with SHAP explanations and recommendations.
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_report(output_path: str, findings: list, recommendations: list):
    """
    Generate a PDF report summarizing findings and recommendations.
    
    Args:
        output_path (str): Path to save PDF
        findings (list): List of rule/anomaly findings
        recommendations (list): List of PQC recommendations
    """
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "TLS Risk Assessment Report")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, "Findings:")
    y = height - 120
    for f in findings:
        c.drawString(70, y, f)
        y -= 20

    c.drawString(50, y - 20, "Recommendations:")
    y -= 40
    for r in recommendations:
        c.drawString(70, y, r)
        y -= 20

    c.save()
