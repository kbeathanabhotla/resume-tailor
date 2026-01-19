from __future__ import annotations
from typing import Dict, Any, Optional
import json

from app.scrape import scrape_job_description
from app.align import align_resume
from app.pdf import generate_pdf
from app.score import compute_ats_score_llm
from app.diff import make_diff_markdown, make_unified_diff
from app.ollama_client import OllamaClient


def run_pipeline(
    base_resume: Dict[str, Any],
    job_url: str,
    output_pdf: str,
    diff_md_out: Optional[str] = None,
    diff_patch_out: Optional[str] = None,
    score_out: Optional[str] = None,
    ollama_client: Optional[OllamaClient] = None,
) -> Dict[str, Any]:
    """
    Run the full resume tailoring pipeline.
    
    Args:
        base_resume: Base resume dictionary
        job_url: Job posting URL to scrape
        output_pdf: Output path for tailored resume PDF
        diff_md_out: Optional output path for markdown diff
        diff_patch_out: Optional output path for unified diff patch
        score_out: Optional output path for ATS score JSON
        ollama_client: Optional OllamaClient instance (creates default if None)
    
    Returns:
        Dictionary with tailored_resume, diff_md, and diff_patch
    """
    if ollama_client is None:
        ollama_client = OllamaClient()
    
    print("Scraping job description...")
    jd = scrape_job_description(job_url)

    print("Aligning resume...")
    tailored = align_resume(base_resume, jd, client=ollama_client)

    print("Scoring ATS match (LLM)...")
    ats = compute_ats_score_llm(
        job_description=jd,
        tailored_resume=tailored,
        client=ollama_client,
    )

    if score_out:
        with open(score_out, "w", encoding="utf-8") as f:
            json.dump(ats, f, indent=2)

    print(f"ATS score: {ats.get('ats_score')}/100 (confidence={ats.get('confidence')})")

    print("Generating diffs...")
    diff_md = make_diff_markdown(base_resume, tailored)
    diff_patch = make_unified_diff(base_resume, tailored)

    if diff_md_out:
        with open(diff_md_out, "w", encoding="utf-8") as f:
            f.write(diff_md)

    if diff_patch_out:
        with open(diff_patch_out, "w", encoding="utf-8") as f:
            f.write(diff_patch)

    print("Generating PDF...")
    generate_pdf(tailored, output_pdf)
    print(f"Done → {output_pdf}")

    return {
        "tailored_resume": tailored,
        "diff_md": diff_md,
        "diff_patch": diff_patch,
        "ats_score": ats,
    }
