# app/render_text.py
from __future__ import annotations
from typing import Dict, Any, List


def resume_to_text(resume: Dict[str, Any]) -> str:
    """
    Flatten the structured resume into plain text for scoring/diff.
    Deterministic ordering matters so scores/diffs are stable.
    """
    out: List[str] = []

    out.append(resume.get("name", "").strip())
    contact = resume.get("contact", {}) or {}
    out.append(
        " | ".join(
            [
                contact.get("location", "").strip(),
                contact.get("email", "").strip(),
                contact.get("linkedin", "").strip(),
            ]
        ).strip(" |")
    )

    for sec in resume.get("sections", []):
        title = (sec.get("title") or "").strip()
        sec_type = (sec.get("type") or "").strip()
        out.append("")
        out.append(title.upper())

        if sec_type in ("bullets", "education"):
            for item in sec.get("items", []) or []:
                out.append(f"- {item}".strip())

        elif sec_type == "core_competencies":
            for block in sec.get("blocks", []) or []:
                label = (block.get("label") or "").strip()
                text = (block.get("text") or "").strip()
                out.append(f"{label} {text}".strip())

        elif sec_type == "experience":
            for job in sec.get("jobs", []) or []:
                role = (job.get("role") or "").strip()
                company = (job.get("company") or "").strip()
                location = (job.get("location") or "").strip()
                dates = (job.get("dates") or "").strip()
                out.append(f"{role} - {company}, {location}".strip(" -,"))

                if dates:
                    out.append(f"[{dates}]")

                for b in job.get("bullets", []) or []:
                    out.append(f"- {b}".strip())

                tech = (job.get("tech_stack") or "").strip()
                if tech:
                    out.append(f"Tech stack: {tech}")

        else:
            # fallback
            for p in sec.get("paragraphs", []) or []:
                out.append(p)

    # Remove empty trailing lines
    text = "\n".join([ln.rstrip() for ln in out]).strip() + "\n"
    return text
