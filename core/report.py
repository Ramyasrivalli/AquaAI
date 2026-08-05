"""
report.py — Professional PDF Laboratory Report Generator using ReportLab.
"""

from io import BytesIO
import time
from typing import Any, Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_pdf_report(
    username: str,
    feature_dict: Dict[str, float],
    is_potable: bool,
    confidence_pct: float,
    quality_score: float,
    quality_status: str,
    parameter_evals: List[Dict[str, Any]],
    recommendations: List[str],
    suitable_uses: List[str],
    model_name: str = "Support Vector Machine",
) -> bytes:
    """Generate a complete, professional laboratory PDF report."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E3A8A"),
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
    )
    h2_style = ParagraphStyle(
        "Heading2Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1A56DB"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#0F172A"),
    )
    table_hdr_style = ParagraphStyle(
        "TableHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white,
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
    )

    # 1. Header Section
    date_str = time.strftime("%Y-%m-%d %H:%M:%S UTC")
    header_table = Table(
        [
            [
                Paragraph("<b>AquaAI Laboratory Report</b><br/><font size=8 color='#64748B'>Water Quality & Potability Intelligence</font>", title_style),
                Paragraph(f"<b>Issued To:</b> {username}<br/><b>Date:</b> {date_str}<br/><b>Model:</b> {model_name}", subtitle_style),
            ]
        ],
        colWidths=[320, 220],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A56DB"), spaceAfter=12))

    # 2. Executive Summary Verdict Banner
    verdict_text = "SAFE / POTABLE" if is_potable else "UNSAFE / NON-POTABLE"
    verdict_bg = colors.HexColor("#ECFDF5") if is_potable else colors.HexColor("#FEF2F2")
    verdict_fg = colors.HexColor("#059669") if is_potable else colors.HexColor("#DC2626")

    summary_data = [
        [
            Paragraph(f"<font color='{verdict_fg.hexval()}'><b>VERDICT: {verdict_text}</b></font>", ParagraphStyle("Verdict", fontName="Helvetica-Bold", fontSize=14, leading=16)),
            Paragraph(f"<b>Quality Score:</b> {quality_score} / 100 ({quality_status})", body_style),
            Paragraph(f"<b>Confidence:</b> {confidence_pct}%", body_style),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[240, 160, 140])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), verdict_bg),
                ("BOX", (0, 0), (-1, -1), 1, verdict_fg),
                ("PADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 12))

    # 3. Parameter Diagnostics Table
    story.append(Paragraph("1. Detailed Parameter Laboratory Diagnostics", h2_style))

    table_data = [
        [
            Paragraph("Parameter", table_hdr_style),
            Paragraph("Measured Value", table_hdr_style),
            Paragraph("WHO Standard", table_hdr_style),
            Paragraph("Status", table_hdr_style),
            Paragraph("Diagnostic Action", table_hdr_style),
        ]
    ]

    for ev in parameter_evals:
        status_txt = ev.get("status", "Ideal")
        val_str = f"{ev.get('value')} {ev.get('unit', '')}".strip()
        ref_str = ev.get("reference", "-")
        rec_str = ev.get("recommendation", "-")

        table_data.append(
            [
                Paragraph(f"<b>{ev.get('label')}</b>", table_cell_style),
                Paragraph(val_str, table_cell_style),
                Paragraph(ref_str, table_cell_style),
                Paragraph(f"<b>{status_txt}</b>", table_cell_style),
                Paragraph(rec_str, table_cell_style),
            ]
        )

    diag_table = Table(table_data, colWidths=[90, 80, 80, 80, 210])
    diag_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A56DB")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(diag_table)
    story.append(Spacer(1, 12))

    # 4. AI Treatment Recommendations
    story.append(Paragraph("2. AI Treatment & Mitigation Recommendations", h2_style))
    if recommendations:
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", body_style))
    else:
        story.append(Paragraph("• Water meets WHO drinking safety guidelines. Routine monitoring recommended.", body_style))

    story.append(Spacer(1, 10))

    # 5. Recommended Applications
    story.append(Paragraph("3. Recommended Water Applications", h2_style))
    if suitable_uses:
        for use in suitable_uses:
            story.append(Paragraph(f"• {use}", body_style))
    else:
        story.append(Paragraph("• Suitable for non-potable industrial utility operations.", body_style))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=10))

    # 6. Official Footer
    footer_text = "Official Quality Inspection Certificate • Generated by AquaAI Machine Learning Intelligence"
    story.append(Paragraph(f"<font color='#64748B' size=8><i>{footer_text}</i></font>", ParagraphStyle("Footer", alignment=1)))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
