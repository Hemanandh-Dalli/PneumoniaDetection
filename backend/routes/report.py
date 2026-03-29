from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
import io
import os
from utils.config import public_to_filesystem_path

router = APIRouter()

class ReportRequest(BaseModel):
    predicted_class: str
    confidence: float
    explanation: str
    image_path: str
    heatmap_path: str


@router.post("/report")
def generate_report(data: ReportRequest):

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>Pneumonia Detection Report</b>", styles["Title"]))
    elements.append(Spacer(1, 20))

    # Diagnosis Table
    table_data = [
        ["Diagnosis", data.predicted_class],
        ["Confidence", f"{data.confidence * 100:.2f}%"],
    ]

    table = Table(table_data, colWidths=[150, 250])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>Explanation:</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(data.explanation.replace("\n", "<br/>"), styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Add Original Image
    image_fs_path = None
    heatmap_fs_path = None
    try:
        image_fs_path = public_to_filesystem_path(data.image_path)
    except ValueError:
        image_fs_path = None

    if data.heatmap_path:
        try:
            heatmap_fs_path = public_to_filesystem_path(data.heatmap_path)
        except ValueError:
            heatmap_fs_path = None

    if image_fs_path and os.path.exists(image_fs_path):
        elements.append(Paragraph("<b>Original X-ray:</b>", styles["Heading2"]))
        elements.append(Spacer(1, 10))
        elements.append(Image(str(image_fs_path), width=4*inch, height=4*inch))
        elements.append(Spacer(1, 20))

    # Add Heatmap
    if heatmap_fs_path and os.path.exists(heatmap_fs_path):
        elements.append(Paragraph("<b>AI Focus Areas (Grad-CAM):</b>", styles["Heading2"]))
        elements.append(Spacer(1, 10))
        elements.append(Image(str(heatmap_fs_path), width=4*inch, height=4*inch))
        elements.append(Spacer(1, 20))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=pneumonia_report.pdf"},
    )
