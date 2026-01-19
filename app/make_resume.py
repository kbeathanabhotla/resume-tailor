#!/usr/bin/env python3
"""
Generate a resume PDF in the same style as the provided sample.

Usage:
  pip install reportlab pyyaml
  python make_resume.py --input base_resume.yaml --output resume.pdf
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
    KeepTogether,
)

BLUE = colors.HexColor("#4F81BD")  # close match to the sample PDF


def _styles():
    base = getSampleStyleSheet()

    name = ParagraphStyle(
        "Name",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14.5,
        leading=17,
        textColor=BLUE,
        alignment=1,  # center
        spaceAfter=6,
    )

    contact = ParagraphStyle(
        "Contact",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=12,
        alignment=1,  # center
        textColor=colors.black,
        spaceAfter=14,
    )

    section = ParagraphStyle(
        "Section",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=BLUE,
        spaceBefore=6,
        spaceAfter=6,
    )

    body = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10.2,
        leading=13.2,
        textColor=colors.black,
    )

    body_bold = ParagraphStyle(
        "BodyBold",
        parent=body,
        fontName="Helvetica-Bold",
    )

    small = ParagraphStyle(
        "Small",
        parent=body,
        fontSize=10.0,
        leading=12.8,
    )

    job_title = ParagraphStyle(
        "JobTitle",
        parent=body,
        spaceBefore=4,
        spaceAfter=2,
    )

    job_dates = ParagraphStyle(
        "JobDates",
        parent=body,
        spaceAfter=4,
    )

    tech = ParagraphStyle(
        "Tech",
        parent=body,
        spaceBefore=2,
        spaceAfter=10,
    )

    comp_label = ParagraphStyle(
        "CompLabel",
        parent=body,
        fontName="Helvetica-Bold",
        spaceAfter=2,
        spaceBefore=2,
    )

    comp_text = ParagraphStyle(
        "CompText",
        parent=body,
        spaceAfter=6,
    )

    return {
        "name": name,
        "contact": contact,
        "section": section,
        "body": body,
        "body_bold": body_bold,
        "small": small,
        "job_title": job_title,
        "job_dates": job_dates,
        "tech": tech,
        "comp_label": comp_label,
        "comp_text": comp_text,
    }


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    """
    ReportLab Paragraph supports a small HTML subset: <b>, <i>, <u>, <br/>, <link>.
    We rely on that for bold emphasis and clickable links.
    """
    return Paragraph(text, style)


def _bullets(items: List[str], style: ParagraphStyle) -> ListFlowable:
    """
    Match the sample's bullet look: solid dot + generous indent.
    """
    bullet_style = ParagraphStyle(
        "BulletItem",
        parent=style,
        leftIndent=18,
        firstLineIndent=-8,
        spaceAfter=4,
    )

    flow_items = []
    for s in items:
        flow_items.append(ListItem(_p(s, bullet_style), leftIndent=0))

    return ListFlowable(
        flow_items,
        bulletType="bullet",
        start="•",
        leftIndent=0,
        bulletFontName="Helvetica",
        bulletFontSize=12,
        bulletOffsetY=1,
    )


def build_resume(data: Dict[str, Any], output_pdf: str) -> None:
    st = _styles()

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=letter,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=f"{data.get('name', 'Resume')}",
        author=data.get("name", ""),
    )

    story = []

    # Header
    story.append(_p(data["name"].upper(), st["name"]))

    # Contact line with links (email + LinkedIn). Keep the same " | " separators.
    location = data["contact"]["location"]
    email = data["contact"]["email"]
    linkedin = data["contact"]["linkedin"]

    contact_html = (
        f"{location} | "
        f'<link href="mailto:{email}" color="blue"><u>{email}</u></link> | '
        f'<link href="{linkedin}" color="blue"><u>{linkedin.replace("https://", "")}</u></link>'
    )
    story.append(_p(contact_html, st["contact"]))

    # Sections (order matters to match the sample)
    for section in data["sections"]:
        title = section["title"].upper()
        story.append(_p(title, st["section"]))

        if section["type"] == "bullets":
            story.append(_bullets(section["items"], st["body"]))
            story.append(Spacer(1, 6))

        elif section["type"] == "core_competencies":
            # Each item: {label: "...", text: "..."}
            for block in section["blocks"]:
                story.append(_p(f"{block['label']}", st["comp_label"]))
                story.append(_p(block["text"], st["comp_text"]))
            story.append(Spacer(1, 2))

        elif section["type"] == "education":
            story.append(_bullets(section["items"], st["body"]))
            story.append(Spacer(1, 6))

        elif section["type"] == "experience":
            # Each job rendered like the sample:
            # <b>Role</b> - Company, Location
            # [dates]
            # bullets...
            # <b>Tech stack:</b> ...
            for job in section["jobs"]:
                role = job["role"]
                company = job["company"]
                loc = job["location"]
                dates = job["dates"]

                title_line = f"<b>{role}</b> - {company}, {loc}"
                job_block = [
                    _p(title_line, st["job_title"]),
                    _p(f"[{dates}]", st["job_dates"]),
                    _bullets(job["bullets"], st["body"]),
                    _p(f"<b>Tech stack:</b> {job['tech_stack']}", st["tech"]),
                ]

                # Keep job header + first bits together so it doesn't split awkwardly
                story.append(KeepTogether(job_block))

        else:
            # Fallback: treat as simple paragraphs
            for para in section.get("paragraphs", []):
                story.append(_p(para, st["body"]))
            story.append(Spacer(1, 6))

    doc.build(story)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="YAML file with resume content")
    ap.add_argument("--output", required=True, help="Output PDF path")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    build_resume(data, args.output)


if __name__ == "__main__":
    main()
