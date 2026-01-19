import yaml
import argparse
from app.pipeline import run_pipeline

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", required=True)
    ap.add_argument("--job-url", required=True)
    ap.add_argument("--out", default="tailored_resume.pdf")
    ap.add_argument("--diff-md", default="diff.md")
    ap.add_argument("--diff-patch", default="diff.patch")
    ap.add_argument("--score-json", default="score.json")
    args = ap.parse_args()

    with open(args.resume, "r", encoding="utf-8") as f:
        resume = yaml.safe_load(f)

    run_pipeline(
        base_resume=resume,
        job_url=args.job_url,
        output_pdf=args.out,
        diff_md_out=args.diff_md,
        diff_patch_out=args.diff_patch,
        score_out=args.score_json,
    )
