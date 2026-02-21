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
# PDF REPORT GENERATOR — PREMIUM DESIGN
# ============================================================


def _clean(text):
    """
    Strip markdown and convert special chars for ReportLab's XML parser.
    """
    if not text:
        return ""
    # Convert markdown bold to ReportLab <b> tags
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', text)
    # Replace Unicode bullets
    replacements = {
        '•': '-', '✓': '[+]', '~': '[~]', '⚠': '[!]',
        '→': '->', '–': '-', '—': '-',
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '°': 'deg', '₂': '2', '≥': '>=', '≤': '<=',
    }
    for ch, sub in replacements.items():
        text = text.replace(ch, sub)
    # Strip any remaining non-ASCII that could break XML
    text = text.encode('ascii', errors='replace').decode('ascii')
    text = text.replace('?', ' ')
    # Escape XML special chars (but preserve our <b>/<i> tags)
    # Only escape & and bare < > that aren't our tags
    text = re.sub(r'&(?!amp;)', '&amp;', text)
    return text.strip()


# Brand colors
ACCENT   = colors.HexColor('#1a1a6e')   # deep navy
ACCENT2  = colors.HexColor('#2563eb')   # blue
SECTION_BG  = colors.HexColor('#eef2ff')  # light blue-tint
CONFIRM_BG  = colors.HexColor('#ecfdf5')  # light green-tint
HEADING_FG  = colors.HexColor('#1e3a5f')
BODY_FG     = colors.HexColor('#1f2937')
SUB_FG      = colors.HexColor('#4b5563')
GREEN_FG    = colors.HexColor('#15803d')


def _make_styles():
    base = getSampleStyleSheet()
    S = {}

    S['report_title'] = ParagraphStyle(
        'report_title', parent=base['Normal'],
        fontSize=28, fontName='Helvetica-Bold',
        textColor=ACCENT, alignment=TA_CENTER,
        spaceBefore=0, spaceAfter=8,
        leading=34,
    )
    S['report_subtitle'] = ParagraphStyle(
        'report_subtitle', parent=base['Normal'],
        fontSize=11, fontName='Helvetica',
        textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER,
        spaceBefore=0, spaceAfter=6,
        leading=16,
    )
    S['report_date'] = ParagraphStyle(
        'report_date', parent=base['Normal'],
        fontSize=9, fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER,
        spaceBefore=0, spaceAfter=0,
        leading=14,
    )
    S['section_heading'] = ParagraphStyle(
        'section_heading', parent=base['Normal'],
        fontSize=12, fontName='Helvetica-Bold',
        textColor=HEADING_FG,
        spaceBefore=0, spaceAfter=0,
        leading=18,
    )
    S['section_heading_green'] = ParagraphStyle(
        'section_heading_green', parent=base['Normal'],
        fontSize=12, fontName='Helvetica-Bold',
        textColor=colors.HexColor('#14532d'),
        spaceBefore=0, spaceAfter=0,
        leading=18,
    )
    S['question_text'] = ParagraphStyle(
        'question_text', parent=base['Normal'],
        fontSize=12, fontName='Helvetica-BoldOblique',
        textColor=colors.HexColor('#1d4ed8'),
        leading=20, alignment=TA_LEFT,
        spaceBefore=0, spaceAfter=0,
    )
    S['body'] = ParagraphStyle(
        'body', parent=base['Normal'],
        fontSize=10, fontName='Helvetica',
        textColor=BODY_FG, leading=16,
        alignment=TA_JUSTIFY,
        spaceBefore=0, spaceAfter=5,
    )
    S['bullet_line'] = ParagraphStyle(
        'bullet_line', parent=base['Normal'],
        fontSize=10, fontName='Helvetica',
        textColor=BODY_FG, leading=15,
        leftIndent=16, firstLineIndent=-12,
        spaceBefore=0, spaceAfter=4,
    )
    S['numbered_line'] = ParagraphStyle(
        'numbered_line', parent=base['Normal'],
        fontSize=10, fontName='Helvetica',
        textColor=BODY_FG, leading=15,
        leftIndent=20, firstLineIndent=-20,
        spaceBefore=0, spaceAfter=4,
    )
    S['verdict_text'] = ParagraphStyle(
        'verdict_text', parent=base['Normal'],
        fontSize=10.5, fontName='Helvetica',
        textColor=colors.HexColor('#064e3b'),
        leading=17, alignment=TA_JUSTIFY,
        spaceBefore=0, spaceAfter=5,
    )
    S['confidence_text'] = ParagraphStyle(
        'confidence_text', parent=base['Normal'],
        fontSize=13, fontName='Helvetica-Bold',
        textColor=GREEN_FG,
        spaceBefore=4, spaceAfter=4,
        leading=18,
    )
    S['label'] = ParagraphStyle(
        'label', parent=base['Normal'],
        fontSize=8, fontName='Helvetica-Bold',
        textColor=colors.HexColor('#6b7280'),
        spaceBefore=0, spaceAfter=2,
        leading=12, letterSpacing=1.5,
    )
    S['footer'] = ParagraphStyle(
        'footer', parent=base['Normal'],
        fontSize=8, fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER,
        spaceBefore=0, spaceAfter=0,
    )
    return S


def _divider(thick=0.5, color='#d1d5db', before=8, after=8):
    return HRFlowable(
        width='100%', thickness=thick,
        color=colors.HexColor(color),
        spaceAfter=after, spaceBefore=before,
    )


def _accent_divider():
    """Bold colored divider under the cover title."""
    return HRFlowable(
        width='100%', thickness=2.5,
        color=ACCENT2,
        spaceAfter=18, spaceBefore=10,
    )


def _section_banner(text, S, green=False):
    """Colored section header banner with left accent bar."""
    key = 'section_heading_green' if green else 'section_heading'
    bg  = CONFIRM_BG if green else SECTION_BG
    bar = colors.HexColor('#15803d') if green else ACCENT2
    inner = Table(
        [[Paragraph(text, S[key])]],
        colWidths=['100%'],
        style=TableStyle([
            ('BACKGROUND',   (0, 0), (-1, -1), bg),
            ('LEFTPADDING',  (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING',   (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 7),
        ])
    )
    # Left accent bar
    wrapper = Table(
        [[Table([[""]],
                colWidths=[4],
                style=TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), bar),
                    ('TOPPADDING',    (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
                    ('LEFTPADDING',  (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ])),
          inner]],
        colWidths=[4, '100%'],
        style=TableStyle([
            ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',   (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
            ('LEFTPADDING',  (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BACKGROUND',   (1, 0), (1, 0), bg),
        ])
    )
    return wrapper


def _render_text_block(text, S):
    """
    Convert a multi-line text block into styled Paragraph flowables.
    Handles numbered lists, bullets, section headers, and body text.
    """
    BULLET_PREFIXES = ('-', '[+]', '[~]', '[!]', 'o', '*')
    paragraphs = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw:
            paragraphs.append(Spacer(1, 3))
            continue
        cl = _clean(raw)
        # Numbered list  "1. text"
        if re.match(r'^\d+\.\s', cl):
            paragraphs.append(Paragraph(cl, S['numbered_line']))
        elif any(cl.startswith(p + ' ') for p in BULLET_PREFIXES):
            paragraphs.append(Paragraph(cl, S['bullet_line']))
        # Bold heading lines like "Key Conclusions:"
        elif cl.endswith(':') and len(cl) < 50:
            paragraphs.append(Spacer(1, 4))
            paragraphs.append(Paragraph('<b>' + cl + '</b>', S['body']))
        else:
            paragraphs.append(Paragraph(cl, S['body']))
    return paragraphs


def generate_pdf(question, summary, verdict):

    if not os.path.exists('reports'):
        os.makedirs('reports')

    filename = f"reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
    )

    S = _make_styles()
    story = []

    # ---- COVER HEADER ----
    now = datetime.now()
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph('ResearchPilot AI', S['report_title']))
    story.append(Spacer(1, 0.20 * cm))   # <-- explicit gap prevents overlap
    story.append(Paragraph('Autonomous Research Report', S['report_subtitle']))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(now.strftime('%d %B %Y  \u00b7  %H:%M'), S['report_date']))
    story.append(_accent_divider())

    # ---- RESEARCH QUESTION ----
    story.append(KeepTogether([
        _section_banner('Research Question', S),
        Spacer(1, 8),
        Paragraph(_clean(question), S['question_text']),
        Spacer(1, 12),
    ]))

    # ---- INTELLIGENCE ANALYSIS ----
    story.append(KeepTogether([
        _section_banner('Intelligence Analysis', S),
        Spacer(1, 8),
    ]))
    story.extend(_render_text_block(summary, S))
    story.append(Spacer(1, 12))

    # ---- FINAL CONCLUSION ----
    story.append(KeepTogether([
        _section_banner('Final Conclusion', S, green=True),
        Spacer(1, 8),
    ]))

    # Split verdict into lines
    for line in verdict.splitlines():
        raw = line.strip()
        if not raw:
            story.append(Spacer(1, 4))
            continue
        line_clean = _clean(raw)
        if line_clean.lower().startswith('confidence'):
            story.append(Paragraph(line_clean, S['confidence_text']))
        elif line_clean.lower().startswith('reasoning:') or line_clean.lower().startswith('final conclusion:'):
            story.append(Paragraph('<b>' + line_clean[:line_clean.index(':') + 1] + '</b>' + line_clean[line_clean.index(':') + 1:], S['verdict_text']))
        else:
            story.append(Paragraph(line_clean, S['verdict_text']))

    story.append(Spacer(1, 1.0 * cm))

    # ---- FOOTER ----
    story.append(_divider(thick=0.5, color='#e5e7eb', before=4, after=6))
    story.append(Paragraph(
        f'Generated by ResearchPilot AI Agent  \u00b7  {now.strftime("%Y-%m-%d %H:%M:%S")}',
        S['footer']
    ))

    doc.build(story)
    return filename



