from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from datetime import datetime
import os
import re

# ============================================================
# PDF REPORT GENERATOR — UPGRADED
#
# Problems fixed vs old version:
#  1. No page margins (text ran to edges) → explicit margins added
#  2. Single giant paragraph for summary/verdict → split into
#     individual lines so each wraps independently
#  3. Bullet chars (•, ✓, ~, ?) broke rendering → cleaned
#  4. No visual hierarchy → cover banner, section dividers added
#  5. Font/style was browser default → custom styles defined
#  6. Special chars like ** (bold markdown) passed raw → stripped
# ============================================================


def _clean(text):
    """
    Strip characters and markdown that confuse reportlab's XML parser,
    and convert common Unicode bullets to ASCII-safe equivalents.
    """
    if not text:
        return ""
    # Replace markdown bold/italic markers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*',     r'\1', text)
    # Replace Unicode bullets and icons with ASCII equivalents
    replacements = {
        '•': '-', '✓': '[+]', '~': '[~]', '⚠': '[!]',
        '?': '?', '→': '->', '–': '-', '—': '-',
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '°': 'deg', '₂': '2', '≥': '>=', '≤': '<=',
    }
    for ch, sub in replacements.items():
        text = text.replace(ch, sub)
    # Strip any remaining non-ASCII that could break XML
    text = text.encode('ascii', errors='replace').decode('ascii')
    text = text.replace('?', ' ')   # replace substitution markers
    # Escape XML special chars for reportlab
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text.strip()


def _make_styles():
    """Build and return a dict of custom ParagraphStyles."""
    base = getSampleStyleSheet()

    styles = {}

    styles['report_title'] = ParagraphStyle(
        'report_title',
        parent=base['Normal'],
        fontSize=22,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1a1a2e'),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles['report_subtitle'] = ParagraphStyle(
        'report_subtitle',
        parent=base['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor('#555555'),
        alignment=TA_CENTER,
        spaceAfter=0,
    )
    styles['section_heading'] = ParagraphStyle(
        'section_heading',
        parent=base['Normal'],
        fontSize=13,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1a1a2e'),
        spaceBefore=16,
        spaceAfter=6,
    )
    styles['question_text'] = ParagraphStyle(
        'question_text',
        parent=base['Normal'],
        fontSize=12,
        fontName='Helvetica-BoldOblique',
        textColor=colors.HexColor('#2c3e50'),
        leading=18,
        alignment=TA_JUSTIFY,
    )
    styles['body'] = ParagraphStyle(
        'body',
        parent=base['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor('#333333'),
        leading=15,
        alignment=TA_JUSTIFY,
        spaceAfter=4,
    )
    styles['bullet_line'] = ParagraphStyle(
        'bullet_line',
        parent=base['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor('#333333'),
        leading=15,
        leftIndent=12,
        firstLineIndent=-12,
        spaceAfter=3,
    )
    styles['verdict_text'] = ParagraphStyle(
        'verdict_text',
        parent=base['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor('#1a1a2e'),
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=4,
    )
    styles['confidence_text'] = ParagraphStyle(
        'confidence_text',
        parent=base['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=4,
    )
    styles['footer'] = ParagraphStyle(
        'footer',
        parent=base['Normal'],
        fontSize=8,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER,
    )

    return styles


def _divider():
    """Thin horizontal rule used between sections."""
    return HRFlowable(
        width="100%",
        thickness=0.5,
        color=colors.HexColor('#cccccc'),
        spaceAfter=8,
        spaceBefore=4,
    )


def _section_banner(text, styles):
    """Colored label used as a section header."""
    return Table(
        [[Paragraph(text, styles['section_heading'])]],
        colWidths=['100%'],
        style=TableStyle([
            ('BACKGROUND',  (0, 0), (-1, -1), colors.HexColor('#eef2ff')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING',(0, 0), (-1, -1), 10),
            ('TOPPADDING',  (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING',(0,0), (-1, -1), 6),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), 4),
        ])
    )


def _render_text_block(text, styles):
    """
    Convert a multi-line text block into a list of Paragraph flowables.
    Each non-empty line becomes its own Paragraph so it wraps correctly.
    Lines that start with a bullet indicator get the bullet_line style.
    """
    BULLET_PREFIXES = ('-', '[+]', '[~]', '[!]', '?', '*')
    paragraphs = []
    for line in text.splitlines():
        line = _clean(line)
        if not line:
            paragraphs.append(Spacer(1, 4))
            continue
        stripped = line.lstrip()
        if any(stripped.startswith(p) for p in BULLET_PREFIXES):
            paragraphs.append(Paragraph(line, styles['bullet_line']))
        else:
            paragraphs.append(Paragraph(line, styles['body']))
    return paragraphs


def generate_pdf(question, summary, verdict):

    if not os.path.exists("reports"):
        os.makedirs("reports")

    filename = f"reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    # A4 with comfortable margins: 2.5cm left/right, 2cm top/bottom
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
    )

    S = _make_styles()
    story = []

    # ---- COVER HEADER ----
    now = datetime.now()
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("ResearchPilot AI", S['report_title']))
    story.append(Paragraph("Autonomous Research Report", S['report_subtitle']))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(now.strftime("%d %B %Y  |  %H:%M"), S['report_subtitle']))
    story.append(Spacer(1, 0.6 * cm))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=colors.HexColor('#1a1a2e'),
                             spaceAfter=16))

    # ---- RESEARCH QUESTION ----
    story.append(KeepTogether([
        _section_banner("Research Question", S),
        Spacer(1, 6),
        Paragraph(_clean(question), S['question_text']),
        Spacer(1, 10),
    ]))

    # ---- ANALYSIS SUMMARY ----
    story.append(KeepTogether([
        _section_banner("Intelligence Analysis", S),
        Spacer(1, 6),
    ]))
    story.extend(_render_text_block(summary, S))
    story.append(Spacer(1, 10))

    # ---- VERDICT ----
    story.append(KeepTogether([
        _section_banner("Final Verdict", S),
        Spacer(1, 6),
    ]))

    # Split verdict into lines and apply special styling to key lines
    for line in verdict.splitlines():
        line_clean = _clean(line)
        if not line_clean:
            story.append(Spacer(1, 4))
            continue
        if line_clean.lower().startswith('confidence:'):
            story.append(Paragraph(line_clean, S['confidence_text']))
        else:
            story.append(Paragraph(line_clean, S['verdict_text']))

    story.append(Spacer(1, 1.0 * cm))

    # ---- FOOTER ----
    story.append(_divider())
    story.append(Paragraph(
        f"Generated by ResearchPilot AI Agent  |  {now.strftime('%Y-%m-%d %H:%M:%S')}",
        S['footer']
    ))

    doc.build(story)
    return filename