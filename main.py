import yaml
import argparse
from app.pipeline import run_pipeline
from app.ollama_client import OllamaClient

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Tailor a resume to a job posting and generate a styled PDF"
    )
    ap.add_argument("--resume", required=True, help="Path to base resume YAML file")
    ap.add_argument("--job-url", required=True, help="URL of job posting to tailor to")
    ap.add_argument("--out", default="tailored_resume.pdf", help="Output PDF path")
    ap.add_argument("--diff-md", default="diff.md", help="Markdown diff output path")
    ap.add_argument("--diff-patch", default="diff.patch", help="Unified diff output path")
    ap.add_argument("--score-json", default="score.json", help="ATS score JSON output path")
    ap.add_argument(
        "--ollama-url",
        help="Ollama base URL (default: env OLLAMA_BASE_URL or http://localhost:11434)",
    )
    ap.add_argument(
        "--ollama-model",
        help="Ollama model name (default: env OLLAMA_MODEL or kimi-k2-thinking:cloud)",
    )
    args = ap.parse_args()

    with open(args.resume, "r", encoding="utf-8") as f:
        resume = yaml.safe_load(f)

    # Create Ollama client with CLI or env config
    ollama_client = OllamaClient(
        base_url=args.ollama_url,
        model=args.ollama_model,
    )

    run_pipeline(
        base_resume=resume,
        job_url=args.job_url,
        output_pdf=args.out,
        diff_md_out=args.diff_md,
        diff_patch_out=args.diff_patch,
        score_out=args.score_json,
        ollama_client=ollama_client,
    )
