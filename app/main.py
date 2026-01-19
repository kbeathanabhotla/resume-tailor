import yaml
import argparse
from pipeline import run_pipeline


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", required=True)
    ap.add_argument("--job-url", required=True)
    ap.add_argument("--out", default="tailored_resume.pdf")
    args = ap.parse_args()

    with open(args.resume) as f:
        resume = yaml.safe_load(f)

    run_pipeline(resume, args.job_url, args.out)
