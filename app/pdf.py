from make_resume import build_resume


def generate_pdf(aligned_resume: dict, output_path: str):
    build_resume(aligned_resume, output_path)
