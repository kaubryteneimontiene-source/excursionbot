from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, Table, TableStyle
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import io
import os
import re
import urllib.request
import tempfile


def get_fonts():
    """Download and register DejaVu fonts for Lithuanian character support."""
    font_path = os.path.join(tempfile.gettempdir(), "DejaVuSans.ttf")
    font_bold_path = os.path.join(tempfile.gettempdir(), "DejaVuSans-Bold.ttf")

    try:
        if not os.path.exists(font_path):
            urllib.request.urlretrieve(
                "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf",
                font_path
            )
        if not os.path.exists(font_bold_path):
            urllib.request.urlretrieve(
                "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf",
                font_bold_path
            )

        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', font_bold_path))
        return 'DejaVuSans', 'DejaVuSans-Bold'

    except Exception as e:
        print(f"Font loading failed, using default: {e}")
        return 'Helvetica', 'Helvetica-Bold'


def generate_pdf(chat_history: list, total_messages: int, total_tokens: int) -> bytes:
    """Generate a formatted PDF from chat history."""

    buffer = io.BytesIO()
    base_font, bold_font = get_fonts()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=24,
        textColor=colors.HexColor("#2E7D32"),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName=bold_font
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#666666"),
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName=base_font
    )

    date_style = ParagraphStyle(
        "Date",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#999999"),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName=base_font
    )

    teacher_style = ParagraphStyle(
        "Teacher",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#1565C0"),
        backColor=colors.HexColor("#E3F2FD"),
        borderPadding=(6, 8, 6, 8),
        spaceAfter=8,
        leftIndent=0,
        fontName=bold_font
    )

    bot_style = ParagraphStyle(
        "Bot",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#1B5E20"),
        backColor=colors.HexColor("#F1F8E9"),
        borderPadding=(6, 8, 6, 8),
        spaceAfter=12,
        leftIndent=0,
        fontName=base_font
    )

    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#ffffff"),
        backColor=colors.HexColor("#2E7D32"),
        spaceBefore=8,
        spaceAfter=0,
        fontName=bold_font,
        borderPadding=(8, 8, 8, 8),
        leading=20,
    )

    story = []

    # Header
    story.append(Paragraph("ExcursionBot", title_style))
    story.append(Paragraph("AI-powered School Excursion Plan", subtitle_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        date_style
    ))
    story.append(HRFlowable(
        width="100%",
        thickness=2,
        color=colors.HexColor("#2E7D32"),
        spaceAfter=16
    ))

    # Stats table
    stats_data = [
        ["Total Messages", "Total Tokens", "Date"],
        [
            str(total_messages),
            str(total_tokens),
            datetime.now().strftime('%Y-%m-%d')
        ]
    ]
    stats_table = Table(stats_data, colWidths=[5*cm, 5*cm, 5*cm])
    stats_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E7D32")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), bold_font),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F1F8E9")),
        ("FONTSIZE", (0, 1), (-1, 1), 12),
        ("FONTNAME", (0, 1), (-1, 1), bold_font),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#2E7D32")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C8E6C9")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 20))

    # Conversation
    story.append(Paragraph("Conversation", styles["Heading2"]))
    story.append(HRFlowable(
        width="100%",
        thickness=1,
        color=colors.HexColor("#C8E6C9"),
        spaceAfter=12
    ))

    for message in chat_history:
        if message["role"] == "user":
            story.append(Spacer(1, 8))
            story.append(Paragraph("TEACHER:", label_style))
            text = message["content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(text, teacher_style))

        elif message["role"] == "assistant":
            story.append(Spacer(1, 4))
            story.append(Paragraph("EXCURSIONBOT:", label_style))
            text = message["content"]
            text = text.replace("### ", "").replace("## ", "").replace("# ", "")
            text = text.replace("---", "")
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            text = text.replace("*", "")
            text = text.replace("• ", "- ")
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Spacer(1, 4))
            story.append(Paragraph(text, bot_style))

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(
        width="100%",
        thickness=1,
        color=colors.HexColor("#C8E6C9"),
        spaceAfter=8
    ))
    story.append(Paragraph(
        "Generated by ExcursionBot | Built with LangChain + Streamlit | Powered by OpenAI GPT-4o-mini",
        date_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()