"""
Advanced PDF Generation Service - Court-Style Legal Documents

Professional PDF generation with:
- Court-style formatting with proper borders and tables
- Fancy captions with decorative elements
- Legal document templates (motions, briefs, pleadings)
- Multi-column layouts
- Header/footer with case information
- Signature blocks and certificate of service
- Table of contents and authorities
- Exhibits and attachments handling
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import legal, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    from reportlab.platypus import BaseDocTemplate, Frame
    from reportlab.platypus import Image as RLImage
    from reportlab.platypus import (KeepTogether, NextPageTemplate, PageBreak,
                                    PageTemplate, Paragraph, SimpleDocTemplate,
                                    Spacer, Table, TableStyle)

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class CourtStylePDFGenerator:
    """
    Generate professional court-style legal documents

    Features:
    - Proper legal formatting (14pt, double-spaced)
    - Court caption boxes with borders
    - Line numbering for motions/briefs
    - Signature blocks
    - Certificate of service
    - Table of authorities
    - Headers/footers with case info
    """

    def __init__(self, case_info: Optional[Dict] = None):
        """
        Initialize PDF generator

        Args:
            case_info: {
                'case_name': 'Barber v. State of New Jersey',
                'docket_number': 'ATL-L-002794-25',
                'court': 'Superior Court of New Jersey',
                'county': 'Atlantic County',
                'case_type': 'Civil Action'
            }
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab not installed. Run: pip install reportlab")

        self.case_info = case_info or {}
        self.styles = self._create_legal_styles()

    def _create_legal_styles(self) -> Dict:
        """Create professional legal document styles"""

        base_styles = getSampleStyleSheet()

        # Court caption style (centered, bold)
        caption_style = ParagraphStyle(
            "CourtCaption",
            parent=base_styles["Normal"],
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            fontName="Times-Bold",
            spaceAfter=6,
        )

        # Legal body text (14pt, double-spaced for readability)
        legal_body = ParagraphStyle(
            "LegalBody",
            parent=base_styles["Normal"],
            fontSize=12,
            leading=24,  # Double spacing
            alignment=TA_JUSTIFY,
            fontName="Times-Roman",
            firstLineIndent=0.5 * inch,
            spaceAfter=12,
        )

        # Legal heading (numbered sections)
        legal_heading = ParagraphStyle(
            "LegalHeading",
            parent=base_styles["Heading2"],
            fontSize=12,
            leading=14,
            fontName="Times-Bold",
            alignment=TA_CENTER,
            spaceAfter=12,
            spaceBefore=12,
        )

        # Footnote style
        footnote = ParagraphStyle(
            "Footnote",
            parent=base_styles["Normal"],
            fontSize=10,
            leading=12,
            fontName="Times-Roman",
            leftIndent=0.5 * inch,
        )

        # Signature block
        signature_block = ParagraphStyle(
            "SignatureBlock",
            parent=base_styles["Normal"],
            fontSize=12,
            leading=14,
            fontName="Times-Roman",
            leftIndent=3.5 * inch,
            spaceAfter=6,
        )

        return {
            "caption": caption_style,
            "body": legal_body,
            "heading": legal_heading,
            "footnote": footnote,
            "signature": signature_block,
            "normal": base_styles["Normal"],
            "title": base_styles["Title"],
        }

    def create_motion(
        self,
        title: str,
        content_sections: List[Dict],
        output_path: str,
        attorney_info: Optional[Dict] = None,
        exhibits: Optional[List[str]] = None,
    ) -> str:
        """
        Create a legal motion with court-style formatting

        Args:
            title: Motion title (e.g., "Motion for Summary Judgment")
            content_sections: [
                {'type': 'heading', 'text': 'INTRODUCTION'},
                {'type': 'paragraph', 'text': 'The plaintiff moves...'},
                {'type': 'table', 'data': [[...]], 'caption': 'Evidence Summary'}
            ]
            output_path: Where to save PDF
            attorney_info: Attorney contact information
            exhibits: List of exhibit labels

        Returns:
            Path to generated PDF
        """

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=1 * inch,
            leftMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
        )

        story = []

        # 1. Court Caption with Border
        story.extend(self._create_court_caption(title))

        # 2. Document Body
        for section in content_sections:
            if section["type"] == "heading":
                story.append(Paragraph(section["text"], self.styles["heading"]))
                story.append(Spacer(1, 0.2 * inch))

            elif section["type"] == "paragraph":
                story.append(Paragraph(section["text"], self.styles["body"]))

            elif section["type"] == "table":
                table = self._create_fancy_table(
                    section["data"], section.get("caption"), section.get("col_widths")
                )
                story.append(table)
                story.append(Spacer(1, 0.3 * inch))

            elif section["type"] == "numbered_list":
                for i, item in enumerate(section["items"], 1):
                    story.append(Paragraph(f"{i}. {item}", self.styles["body"]))

            elif section["type"] == "quote":
                # Block quote (indented)
                quote_style = ParagraphStyle(
                    "Quote",
                    parent=self.styles["body"],
                    leftIndent=0.5 * inch,
                    rightIndent=0.5 * inch,
                    fontName="Times-Italic",
                )
                story.append(Paragraph(section["text"], quote_style))

        # 3. Signature Block
        if attorney_info:
            story.append(Spacer(1, 0.5 * inch))
            story.extend(self._create_signature_block(attorney_info))

        # 4. Certificate of Service
        story.append(PageBreak())
        story.extend(self._create_certificate_of_service(attorney_info))

        # 5. Exhibits List
        if exhibits:
            story.append(PageBreak())
            story.extend(self._create_exhibits_list(exhibits))

        # Build PDF
        doc.build(story)

        return output_path

    def _create_court_caption(self, document_title: str) -> List:
        """Create fancy court caption with borders"""

        elements = []

        # Court name (centered, no border)
        elements.append(
            Paragraph(
                self.case_info.get("court", "SUPERIOR COURT OF NEW JERSEY"), self.styles["caption"]
            )
        )
        elements.append(
            Paragraph(
                self.case_info.get("county", "LAW DIVISION: ATLANTIC COUNTY"),
                self.styles["caption"],
            )
        )
        elements.append(Spacer(1, 0.2 * inch))

        # Caption box with fancy borders
        caption_data = [
            [
                Paragraph(
                    f"<b>{self.case_info.get('case_name', 'Plaintiff v. Defendant')}</b>",
                    self.styles["normal"],
                ),
                "",
            ],
            ["", ""],
            [Paragraph("<i>Plaintiff,</i>", self.styles["normal"]), ""],
            ["", ""],
            [
                Paragraph("<b>v.</b>", self.styles["caption"]),
                Paragraph(
                    f"<b>Docket No.:</b> {self.case_info.get('docket_number', 'XXX-L-XXXXXX-XX')}<br/>"
                    f"<b>Civil Action</b>",
                    self.styles["normal"],
                ),
            ],
            ["", ""],
            [Paragraph("<i>Defendant.</i>", self.styles["normal"]), ""],
        ]

        caption_table = Table(
            caption_data,
            colWidths=[4.5 * inch, 2 * inch],
            rowHeights=[0.3 * inch] * len(caption_data),
        )

        # Fancy border styling
        caption_table.setStyle(
            TableStyle(
                [
                    # Outer border (thick, double-line effect)
                    ("BOX", (0, 0), (-1, -1), 2, colors.black),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    # Left column alignment
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    # Right column (docket info) - boxed
                    ("BOX", (1, 0), (1, -1), 1, colors.black),
                    ("BACKGROUND", (1, 0), (1, -1), colors.lightgrey),
                    ("ALIGN", (1, 0), (1, -1), "CENTER"),
                    # Padding
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        elements.append(caption_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Document title (centered, underlined)
        elements.append(
            Paragraph(f"<u><b>{document_title.upper()}</b></u>", self.styles["caption"])
        )
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_fancy_table(
        self,
        data: List[List],
        caption: Optional[str] = None,
        col_widths: Optional[List[float]] = None,
    ) -> Table:
        """
        Create a professional table with borders and styling

        Args:
            data: 2D list of table data
            caption: Table caption/title
            col_widths: Column widths in inches
        """

        # Add caption as first row if provided
        if caption:
            caption_row = [[Paragraph(f"<b>{caption}</b>", self.styles["caption"])]]
            table_data = caption_row + data
            span_caption = True
        else:
            table_data = data
            span_caption = False

        # Convert data to Paragraphs for better formatting
        formatted_data = []
        for row in table_data:
            formatted_row = []
            for cell in row:
                if isinstance(cell, str):
                    formatted_row.append(Paragraph(cell, self.styles["normal"]))
                else:
                    formatted_row.append(cell)
            formatted_data.append(formatted_row)

        # Create table
        if col_widths:
            table = Table(formatted_data, colWidths=[w * inch for w in col_widths])
        else:
            table = Table(formatted_data)

        # Professional styling
        style_commands = [
            # Outer border (thick)
            ("BOX", (0, 0), (-1, -1), 2, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
            # Header row (if caption exists, it's row 0)
            (
                "BACKGROUND",
                (0, 0 if not span_caption else 1),
                (-1, 0 if not span_caption else 1),
                colors.lightgrey,
            ),
            (
                "TEXTCOLOR",
                (0, 0 if not span_caption else 1),
                (-1, 0 if not span_caption else 1),
                colors.black,
            ),
            (
                "FONTNAME",
                (0, 0 if not span_caption else 1),
                (-1, 0 if not span_caption else 1),
                "Times-Bold",
            ),
            # Alignment
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            # Padding
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]

        # Span caption across all columns
        if span_caption:
            style_commands.append(("SPAN", (0, 0), (-1, 0)))

        table.setStyle(TableStyle(style_commands))

        return table

    def _create_signature_block(self, attorney_info: Dict) -> List:
        """Create professional signature block"""

        elements = []

        elements.append(Paragraph("Respectfully submitted,", self.styles["signature"]))
        elements.append(Spacer(1, 0.5 * inch))  # Space for signature

        sig_lines = [
            f"_________________________________",
            f"<b>{attorney_info.get('name', 'Attorney Name')}</b>",
            f"Attorney for {attorney_info.get('representing', 'Plaintiff')}",
            f"Bar No.: {attorney_info.get('bar_number', 'XXXXXXX')}",
            f"{attorney_info.get('firm', 'Law Firm Name')}",
            f"{attorney_info.get('address', '123 Main St')}",
            f"{attorney_info.get('city_state_zip', 'City, State ZIP')}",
            f"Tel: {attorney_info.get('phone', '(555) 555-5555')}",
            f"Email: {attorney_info.get('email', 'attorney@lawfirm.com')}",
        ]

        for line in sig_lines:
            elements.append(Paragraph(line, self.styles["signature"]))

        return elements

    def _create_certificate_of_service(self, attorney_info: Dict) -> List:
        """Create certificate of service"""

        elements = []

        elements.append(Paragraph("<b><u>CERTIFICATE OF SERVICE</u></b>", self.styles["caption"]))
        elements.append(Spacer(1, 0.3 * inch))

        cert_text = (
            f"I hereby certify that on {datetime.now().strftime('%B %d, %Y')}, "
            f"a true and correct copy of the foregoing was served upon all parties "
            f"of record via electronic filing and/or email to the addresses of record."
        )

        elements.append(Paragraph(cert_text, self.styles["body"]))
        elements.append(Spacer(1, 0.5 * inch))

        # Signature line
        elements.append(Paragraph("_________________________________", self.styles["signature"]))
        elements.append(
            Paragraph(
                f"<b>{attorney_info.get('name', 'Attorney Name')}</b>", self.styles["signature"]
            )
        )

        return elements

    def _create_exhibits_list(self, exhibits: List[str]) -> List:
        """Create exhibits index"""

        elements = []

        elements.append(Paragraph("<b><u>INDEX OF EXHIBITS</u></b>", self.styles["caption"]))
        elements.append(Spacer(1, 0.3 * inch))

        exhibit_data = [["Exhibit", "Description"]]
        for i, exhibit in enumerate(exhibits, 1):
            exhibit_data.append([f"Exhibit {chr(64+i)}", exhibit])

        exhibit_table = self._create_fancy_table(exhibit_data, col_widths=[1.5, 5])
        elements.append(exhibit_table)

        return elements

    def create_brief(
        self,
        title: str,
        table_of_contents: List[Dict],
        table_of_authorities: List[Dict],
        argument_sections: List[Dict],
        output_path: str,
        attorney_info: Optional[Dict] = None,
    ) -> str:
        """
        Create appellate brief with TOC and TOA

        Args:
            title: Brief title
            table_of_contents: [{'section': 'I. Introduction', 'page': 1}, ...]
            table_of_authorities: [
                {'type': 'Cases', 'citations': ['Brown v. Board, 347 U.S. 483']},
                {'type': 'Statutes', 'citations': ['42 U.S.C. § 1983']}
            ]
            argument_sections: Same format as create_motion content_sections
            output_path: Output file path
            attorney_info: Attorney information
        """

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=1 * inch,
            leftMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
        )

        story = []

        # 1. Cover page / Caption
        story.extend(self._create_court_caption(title))
        story.append(PageBreak())

        # 2. Table of Contents
        story.append(Paragraph("<b><u>TABLE OF CONTENTS</u></b>", self.styles["caption"]))
        story.append(Spacer(1, 0.2 * inch))

        toc_data = [["Section", "Page"]]
        for item in table_of_contents:
            toc_data.append([item["section"], str(item.get("page", "..."))])

        toc_table = self._create_fancy_table(toc_data, col_widths=[5, 1.5])
        story.append(toc_table)
        story.append(PageBreak())

        # 3. Table of Authorities
        story.append(Paragraph("<b><u>TABLE OF AUTHORITIES</u></b>", self.styles["caption"]))
        story.append(Spacer(1, 0.2 * inch))

        for authority_type in table_of_authorities:
            story.append(Paragraph(f"<b>{authority_type['type']}</b>", self.styles["heading"]))

            for citation in authority_type["citations"]:
                story.append(Paragraph(f"    {citation}", self.styles["normal"]))

            story.append(Spacer(1, 0.2 * inch))

        story.append(PageBreak())

        # 4. Argument sections
        for section in argument_sections:
            if section["type"] == "heading":
                story.append(Paragraph(section["text"], self.styles["heading"]))
            elif section["type"] == "paragraph":
                story.append(Paragraph(section["text"], self.styles["body"]))
            elif section["type"] == "table":
                table = self._create_fancy_table(
                    section["data"], section.get("caption"), section.get("col_widths")
                )
                story.append(table)
                story.append(Spacer(1, 0.3 * inch))

        # 5. Signature block
        if attorney_info:
            story.append(Spacer(1, 0.5 * inch))
            story.extend(self._create_signature_block(attorney_info))

        # Build PDF
        doc.build(story)

        return output_path

    def create_pleading(
        self,
        pleading_type: str,
        paragraphs: List[str],
        prayer_for_relief: List[str],
        output_path: str,
        attorney_info: Optional[Dict] = None,
        verification: bool = False,
    ) -> str:
        """
        Create a pleading (complaint, answer, counterclaim)

        Args:
            pleading_type: 'COMPLAINT', 'ANSWER', 'COUNTERCLAIM', etc.
            paragraphs: List of numbered paragraphs
            prayer_for_relief: List of relief requests
            output_path: Output file path
            attorney_info: Attorney information
            verification: Include verification page
        """

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=1 * inch,
            leftMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
        )

        story = []

        # Caption
        story.extend(self._create_court_caption(pleading_type))

        # Numbered paragraphs
        for i, para in enumerate(paragraphs, 1):
            story.append(Paragraph(f"<b>{i}.</b> {para}", self.styles["body"]))

        # Prayer for relief
        story.append(Spacer(1, 0.5 * inch))
        story.append(
            Paragraph(
                "<b><u>WHEREFORE</u></b>, Plaintiff respectfully requests that this Court:",
                self.styles["body"],
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        for i, relief in enumerate(prayer_for_relief, 1):
            story.append(Paragraph(f"{i}. {relief}", self.styles["body"]))

        # Signature
        if attorney_info:
            story.append(Spacer(1, 0.5 * inch))
            story.extend(self._create_signature_block(attorney_info))

        # Verification (if sworn complaint)
        if verification:
            story.append(PageBreak())
            story.extend(self._create_verification())

        doc.build(story)

        return output_path

    def _create_verification(self) -> List:
        """Create verification page for sworn complaints"""

        elements = []

        elements.append(Paragraph("<b><u>VERIFICATION</u></b>", self.styles["caption"]))
        elements.append(Spacer(1, 0.3 * inch))

        verification_text = (
            "I, _________________, being duly sworn according to law, depose and say that "
            "I have read the foregoing Complaint and the statements contained therein are "
            "true to my own knowledge, information, and belief."
        )

        elements.append(Paragraph(verification_text, self.styles["body"]))
        elements.append(Spacer(1, 0.5 * inch))

        # Signature lines
        sig_data = [
            ["_________________________________", "Date: ________________"],
            ["Plaintiff/Affiant Signature", ""],
        ]

        sig_table = Table(sig_data, colWidths=[4 * inch, 2.5 * inch])
        sig_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ]
            )
        )

        elements.append(sig_table)
        elements.append(Spacer(1, 0.5 * inch))

        # Notary section
        elements.append(
            Paragraph(
                "Subscribed and sworn to before me this _____ day of ____________, 20____.",
                self.styles["body"],
            )
        )
        elements.append(Spacer(1, 0.5 * inch))

        notary_data = [
            ["_________________________________"],
            ["Notary Public"],
            ["My Commission Expires: ___________"],
        ]

        notary_table = Table(notary_data, colWidths=[4 * inch])
        elements.append(notary_table)

        return elements


# Convenience functions
def create_motion_pdf(
    title: str, sections: List[Dict], output_path: str, case_info: Dict, attorney_info: Dict
) -> str:
    """Quick function to create motion PDF"""

    generator = CourtStylePDFGenerator(case_info)
    return generator.create_motion(title, sections, output_path, attorney_info)


def create_brief_pdf(
    title: str,
    toc: List[Dict],
    toa: List[Dict],
    argument: List[Dict],
    output_path: str,
    case_info: Dict,
    attorney_info: Dict,
) -> str:
    """Quick function to create appellate brief PDF"""

    generator = CourtStylePDFGenerator(case_info)
    return generator.create_brief(title, toc, toa, argument, output_path, attorney_info)
