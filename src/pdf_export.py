from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from PIL import Image as PILImage

def create_flowchart_pdf(
    filename,
    title,
    image_path,
    mermaid_code
):

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    code_style = ParagraphStyle(
    "CodeStyle",
    parent=styles["BodyText"],
    fontSize=11,
    leading=14
)

    content = []

    content.append(
        Paragraph(
            f"<b>{title}</b>",
            styles["Title"]
        )
    )

    content.append(
        Spacer(1, 20)
    )

    content.append(
        Paragraph(
            "Mermaid Flowchart Code",
            styles["Heading2"]
        )
    )

    content.append(
        Paragraph(
            mermaid_code.replace("\n", "<br/>"),
            code_style
        )
    )

    content.append(
        Spacer(1, 20)
    )

    img = PILImage.open(image_path)

    img_width, img_height = img.size

    pdf_width = 500
    pdf_height = (img_height / img_width) * pdf_width

    content.append(
        Image(
            image_path,
            width=pdf_width,
            height=pdf_height
        )
    )

    doc.build(content)

    return filename