from scrape import scrape_job_description
from align import align_resume
from pdf import generate_pdf


def run_pipeline(base_resume: dict, job_url: str, output_pdf: str):
    print("Scraping job description...")
    jd = scrape_job_description(job_url)

    print("Aligning resume...")
    aligned_resume = align_resume(base_resume, jd)

    print("Generating PDF...")
    generate_pdf(aligned_resume, output_pdf)

    print(f"Done → {output_pdf}")
