# app/diff.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple
import difflib
import json

from app.render_text import resume_to_text


def _index_experience(resume: Dict[str, Any]) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
    """
    Index jobs by (role, company, dates) for matching base vs tailored.
    """
    idx = {}
    for sec in resume.get("sections", []):
        if sec.get("type") != "experience":
            continue
        for job in sec.get("jobs", []) or []:
            key = (
                (job.get("role") or "").strip(),
                (job.get("company") or "").strip(),
                (job.get("dates") or "").strip(),
            )
            idx[key] = job
    return idx


def make_diff_markdown(base: Dict[str, Any], tailored: Dict[str, Any]) -> str:
    """
    Human-friendly diff grouped by sections and experience jobs.
    """
    lines: List[str] = []
    lines.append("# Resume Diff")
    lines.append("")
    lines.append("## High-level")
    lines.append(f"- Name: `{base.get('name','')}` → `{tailored.get('name','')}`")
    lines.append("")

    # Diff sections by title
    base_secs = { (s.get("title") or "").strip().lower(): s for s in base.get("sections", []) }
    tail_secs = { (s.get("title") or "").strip().lower(): s for s in tailored.get("sections", []) }

    all_titles = sorted(set(base_secs.keys()) | set(tail_secs.keys()))

    for t in all_titles:
        b = base_secs.get(t)
        a = tail_secs.get(t)
        title = (a or b or {}).get("title", t).strip()

        if b is None:
            lines.append(f"## {title}")
            lines.append("- ✅ Added section")
            lines.append("")
            continue

        if a is None:
            lines.append(f"## {title}")
            lines.append("- ❌ Removed section")
            lines.append("")
            continue

        btype = b.get("type")
        atype = a.get("type")
        lines.append(f"## {title}")

        if btype != atype:
            lines.append(f"- Type changed: `{btype}` → `{atype}`")

        # bullets / education
        if atype in ("bullets", "education"):
            bitems = b.get("items", []) or []
            aitems = a.get("items", []) or []
            added = [x for x in aitems if x not in bitems]
            removed = [x for x in bitems if x not in aitems]

            if not added and not removed:
                lines.append("- No change")
            else:
                if added:
                    lines.append("### Added")
                    for x in added:
                        lines.append(f"- {x}")
                if removed:
                    lines.append("### Removed")
                    for x in removed:
                        lines.append(f"- {x}")

        elif atype == "core_competencies":
            # coarse diff: show blocks changed
            bblocks = b.get("blocks", []) or []
            ablocks = a.get("blocks", []) or []
            if json.dumps(bblocks, sort_keys=True) == json.dumps(ablocks, sort_keys=True):
                lines.append("- No change")
            else:
                lines.append("- Updated competency blocks (review below)")
                lines.append("")
                lines.append("### Tailored")
                for bl in ablocks:
                    lines.append(f"- **{bl.get('label','')}** {bl.get('text','')}".strip())

        elif atype == "experience":
            bidx = _index_experience(base)
            aidx = _index_experience(tailored)
            keys = sorted(set(bidx.keys()) | set(aidx.keys()))

            for k in keys:
                bj = bidx.get(k)
                aj = aidx.get(k)
                role, company, dates = k
                header = f"### {role} - {company} [{dates}]".strip()

                if bj is None:
                    lines.append(header)
                    lines.append("- ✅ Added job block")
                    lines.append("")
                    continue
                if aj is None:
                    lines.append(header)
                    lines.append("- ❌ Removed job block")
                    lines.append("")
                    continue

                bbul = bj.get("bullets", []) or []
                abul = aj.get("bullets", []) or []
                added = [x for x in abul if x not in bbul]
                removed = [x for x in bbul if x not in abul]

                btech = (bj.get("tech_stack") or "").strip()
                atech = (aj.get("tech_stack") or "").strip()

                if not added and not removed and btech == atech:
                    lines.append(header)
                    lines.append("- No change")
                    lines.append("")
                else:
                    lines.append(header)
                    if added:
                        lines.append("**Added bullets**")
                        for x in added:
                            lines.append(f"- {x}")
                    if removed:
                        lines.append("**Removed bullets**")
                        for x in removed:
                            lines.append(f"- {x}")
                    if btech != atech:
                        lines.append(f"**Tech stack**: `{btech}` → `{atech}`")
                    lines.append("")

        else:
            lines.append("- (Section type not diffed in detail yet)")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def make_unified_diff(base: Dict[str, Any], tailored: Dict[str, Any]) -> str:
    """
    Unified diff of normalized text forms (fast to scan).
    """
    a = resume_to_text(base).splitlines(keepends=True)
    b = resume_to_text(tailored).splitlines(keepends=True)
    diff = difflib.unified_diff(
        a, b,
        fromfile="base_resume.txt",
        tofile="tailored_resume.txt",
        lineterm="",
    )
    return "\n".join(diff).strip() + "\n"
