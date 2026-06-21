from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet


def create_flowchart_pdf(filename, title, mermaid_code):

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            f"<b>{title}</b>",
            styles["Title"]
        )
    )

    content.append(Spacer(1, 12))

    content.append(
        Paragraph(
            "Mermaid Flowchart Code",
            styles["Heading2"]
        )
    )

    content.append(
        Paragraph(
            mermaid_code.replace("\n", "<br/>"),
            styles["Code"]
        )
    )

    doc.build(content)

    return filename