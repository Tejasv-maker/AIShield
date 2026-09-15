from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

import os
from datetime import datetime


def create_report(
    scan_type,
    content,
    label,
    risk,
    confidence,
    reasons
):

    filename = (
        "reports/"
        "AIShield_Security_Report.pdf"
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER

    document = SimpleDocTemplate(
        filename,
        pagesize=A4
    )

    story = []

    story.append(
        Paragraph(
            "AIShield Security Report",
            title_style
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "AI-Based Scam & Phishing Detection System",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 15))

    scan_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    table_data = [
        ["Scan Type", scan_type],
        ["Detection", label],
        ["Risk Score", f"{risk}%"],
        ["Confidence", f"{confidence}%"],
        ["Scan Time", scan_time]
    ]

    table = Table(
        table_data,
        colWidths=[150, 300]
    )

    table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 8)
        ])
    )

    story.append(table)

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "<b>Analyzed Content</b>",
            styles["Heading3"]
        )
    )

    story.append(
        Paragraph(
            str(content)[:1500],
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "<b>AI Explanation</b>",
            styles["Heading3"]
        )
    )

    for reason in reasons:

        story.append(
            Paragraph(
                "• " + str(reason),
                styles["BodyText"]
            )
        )

        story.append(
            Spacer(1, 5)
        )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "AIShield provides an automated risk assessment. "
            "This report should be treated as a security-assistance "
            "tool rather than a guarantee that content is safe.",
            styles["BodyText"]
        )
    )

    document.build(story)

    return filename