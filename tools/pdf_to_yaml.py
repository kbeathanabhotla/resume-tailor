#!/usr/bin/env python3
"""
PDF -> YAML converter for resumes in the "resume-tailor" schema.

Best results for PDFs that follow this structure:
- Name on first line (largest text usually)
- Contact line: "Location | email | linkedin"
- Section headers in all caps: SUMMARY, CORE COMPETENCIES, EDUCATION, SELECTED ACHIEVEMENTS, PROFESSIONAL EXPERIENCE
"""

from __future__ import annotations

import argparse
import re
from typing import Dict, List, Tuple, Optional

import pdfplumber
import yaml


SECTION_TITLES = [
    "SUMMARY",
    "CORE COMPETENCIES",
    "EDUCATION",
    "SELECTED ACHIEVEMENTS",
    "PROFESSIONAL EXPERIENCE",
]


def extract_text(pdf_path: str) -> str:
    parts: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            parts.append(txt)
    # Keep line breaks for parsing
    return "\n".join(parts)


def normalize_lines(text: str) -> List[str]:
    lines = [ln.strip() for ln in text.splitlines()]
    # Drop empty and repeated whitespace
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in lines if ln.strip()]
    return lines


def find_section_indices(lines: List[str]) -> Dict[str, int]:
    idx = {}
    for i, ln in enumerate(lines):
        up = ln.strip().upper()
        if up in SECTION_TITLES and up not in idx:
            idx[up] = i
    return idx


def slice_sections(lines: List[str], section_indices: Dict[str, int]) -> Dict[str, List[str]]:
    # order by occurrence
    ordered = sorted(section_indices.items(), key=lambda x: x[1])
    out: Dict[str, List[str]] = {}

    for j, (name, start) in enumerate(ordered):
        end = ordered[j + 1][1] if j + 1 < len(ordered) else len(lines)
        out[name] = lines[start + 1 : end]  # content after header
    return out


def parse_header(lines: List[str]) -> Tuple[str, Dict[str, str], int]:
    """
    Returns (name, contact_dict, next_index_after_header)
    Heuristic: name is first non-empty line.
    Contact line is next line that contains " | " with email or linkedin.
    """
    name = lines[0].strip()
    contact = {"location": "", "email": "", "linkedin": ""}
    next_i = 1

    # Find contact line within first ~6 lines
    for i in range(1, min(7, len(lines))):
        ln = lines[i]
        if " | " in ln or "|" in ln:
            # split on pipe
            parts = [p.strip() for p in re.split(r"\s*\|\s*", ln)]
            # crude detection
            if parts:
                contact["location"] = parts[0]
            for p in parts[1:]:
                if "@" in p:
                    contact["email"] = p
                if "linkedin" in p.lower():
                    # try to reconstruct full link if missing scheme
                    if p.startswith("http"):
                        contact["linkedin"] = p
                    else:
                        contact["linkedin"] = "https://" + p.lstrip("/")
            next_i = i + 1
            break

    return name.title(), contact, next_i


def to_bullets(lines: List[str]) -> List[str]:
    """
    Convert section text lines into bullet items.
    Accepts:
      - leading bullet symbols: •, -, *
      - or plain lines (kept as-is)
    """
    bullets: List[str] = []
    for ln in lines:
        ln = re.sub(r"^[\u2022\-\*]\s*", "", ln).strip()
        if ln:
            bullets.append(ln)
    return bullets


def parse_core_competencies(lines: List[str]) -> List[Dict[str, str]]:
    """
    Expected format per block:
      "Label: text..."
    If multiple lines belong to same label, they are joined.
    """
    blocks: List[Dict[str, str]] = []
    current_label = None
    current_text_parts: List[str] = []

    for ln in lines:
        m = re.match(r"^(.+?):\s*(.*)$", ln)
        if m:
            # flush previous
            if current_label:
                blocks.append({"label": current_label, "text": " ".join(current_text_parts).strip()})
            current_label = m.group(1).strip() + ":"
            rest = m.group(2).strip()
            current_text_parts = [rest] if rest else []
        else:
            # continuation
            if current_label:
                current_text_parts.append(ln.strip())

    if current_label:
        blocks.append({"label": current_label, "text": " ".join(current_text_parts).strip()})

    return blocks


def parse_experience(lines: List[str]) -> List[Dict]:
    """
    Parse experience jobs from a block of lines.

    Recognizes job start lines like:
      "<Role> - <Company>, <Location>"
    Then expects dates like:
      "[01/2024 - Present]"
    Bullets until "Tech stack:" line
    """
    jobs: List[Dict] = []
    i = 0

    job_title_re = re.compile(r"^(.*?)\s-\s(.*?),\s(.+)$")
    date_re = re.compile(r"^\[(.+?)\]$")
    tech_re = re.compile(r"^Tech stack:\s*(.*)$", re.IGNORECASE)

    while i < len(lines):
        ln = lines[i]

        m_title = job_title_re.match(ln)
        if not m_title:
            i += 1
            continue

        role = m_title.group(1).strip()
        company = m_title.group(2).strip()
        location = m_title.group(3).strip()

        # dates line (optional but expected)
        dates = ""
        if i + 1 < len(lines) and date_re.match(lines[i + 1]):
            dates = date_re.match(lines[i + 1]).group(1).strip()
            i += 2
        else:
            i += 1

        bullets: List[str] = []
        tech_stack = ""

        # gather until next job title or end
        while i < len(lines):
            ln2 = lines[i]

            # next job begins
            if job_title_re.match(ln2):
                break

            mt = tech_re.match(ln2)
            if mt:
                tech_stack = mt.group(1).strip()
                i += 1
                # some PDFs wrap tech stack across lines; keep grabbing until blank or next job/section-like
                while i < len(lines):
                    peek = lines[i]
                    if job_title_re.match(peek) or peek.upper() in SECTION_TITLES:
                        break
                    # stop if it looks like a bullet line (usually tech stack ends before bullets resume)
                    if peek.startswith("•") or peek.startswith("-") or peek.startswith("*"):
                        break
                    tech_stack += " " + peek.strip()
                    i += 1
                tech_stack = re.sub(r"\s+", " ", tech_stack).strip()
                continue

            # bullet-ish line
            if ln2.startswith("•") or ln2.startswith("-") or ln2.startswith("*"):
                bullets.append(re.sub(r"^[\u2022\-\*]\s*", "", ln2).strip())
            else:
                # sometimes bullets lose the bullet symbol in extraction; treat short lines as continuation
                if bullets:
                    bullets[-1] = (bullets[-1] + " " + ln2).strip()
                else:
                    # ignore stray line
                    pass
            i += 1

        jobs.append(
            {
                "role": role,
                "company": company,
                "location": location,
                "dates": dates,
                "bullets": bullets,
                "tech_stack": tech_stack,
            }
        )

    return jobs


def build_yaml(name: str, contact: Dict[str, str], sections: Dict[str, List[str]]) -> Dict:
    out = {
        "name": name,
        "contact": contact,
        "sections": [],
    }

    # SUMMARY
    if "SUMMARY" in sections:
        out["sections"].append(
            {"title": "Summary", "type": "bullets", "items": to_bullets(sections["SUMMARY"])}
        )

    # CORE COMPETENCIES
    if "CORE COMPETENCIES" in sections:
        out["sections"].append(
            {"title": "Core Competencies", "type": "core_competencies", "blocks": parse_core_competencies(sections["CORE COMPETENCIES"])}
        )

    # EDUCATION
    if "EDUCATION" in sections:
        out["sections"].append(
            {"title": "Education", "type": "education", "items": to_bullets(sections["EDUCATION"])}
        )

    # SELECTED ACHIEVEMENTS
    if "SELECTED ACHIEVEMENTS" in sections:
        out["sections"].append(
            {"title": "Selected Achievements", "type": "bullets", "items": to_bullets(sections["SELECTED ACHIEVEMENTS"])}
        )

    # PROFESSIONAL EXPERIENCE
    if "PROFESSIONAL EXPERIENCE" in sections:
        out["sections"].append(
            {"title": "Professional Experience", "type": "experience", "jobs": parse_experience(sections["PROFESSIONAL EXPERIENCE"])}
        )

    # If we missed sections (different template), stash remaining text to avoid losing content.
    known = set(SECTION_TITLES)
    extras = [k for k in sections.keys() if k not in known]
    if extras:
        for k in extras:
            out["sections"].append(
                {"title": k.title(), "type": "bullets", "items": to_bullets(sections[k])}
            )

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, help="Input resume PDF")
    ap.add_argument("--out", required=True, help="Output YAML path")
    args = ap.parse_args()

    raw = extract_text(args.pdf)
    lines = normalize_lines(raw)

    name, contact, header_end = parse_header(lines)

    # Find sections after the header area
    body_lines = lines[header_end:]
    section_indices = find_section_indices(body_lines)

    if not section_indices:
        # fallback: dump as a single section
        data = {
            "name": name,
            "contact": contact,
            "sections": [{"title": "Content", "type": "bullets", "items": to_bullets(body_lines)}],
        }
    else:
        sections = slice_sections(body_lines, section_indices)
        data = build_yaml(name, contact, sections)

    with open(args.out, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

    print(f"Wrote YAML -> {args.out}")


if __name__ == "__main__":
    main()
