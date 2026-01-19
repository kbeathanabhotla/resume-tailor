# resume-tailor

Tailor a resume to a specific job posting link and export a **new PDF** in a consistent resume style.

**What it does**

1. Takes your **base resume content** (YAML/JSON).
2. Scrapes a **job description** from a URL (LinkedIn or other job pages).
3. Aligns / rewrites your resume to the JD (without inventing experience).
4. Generates a **tailored resume PDF**.

---

## Repo layout

```
resume-tailor/
├── app/
│   ├── scrape.py         # Scrape job description from a URL
│   ├── align.py          # Resume ↔ JD alignment (LLM)
│   ├── schema.py         # Pydantic schema for resume structure
│   ├── pdf.py            # PDF rendering wrapper
│   └── pipeline.py       # End-to-end orchestration
├── prompts/
│   └── resume_align.txt  # Alignment instructions/prompt
├── examples/
│   └── base_resume.yaml  # Example resume input
├── make_resume.py        # Styled PDF generator (ReportLab)
├── main.py               # CLI entrypoint
└── requirements.txt
```

---

## Quick start

### 1) Install

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 2) Set up Ollama

This project uses Ollama running locally. Make sure Ollama is installed and running with the model.

```bash
# Install Ollama (if not already installed)
# Visit https://ollama.ai to download

# Pull the model
ollama pull kimi-k2-thinking:cloud

# Ollama should be running on http://localhost:11434
```

### 3) Run the pipeline

```bash
python main.py \
  --resume examples/base_resume.yaml \
  --job-url "https://some-job-site.com/jobs/123" \
  --out tailored_resume.pdf
```

Output:

* `tailored_resume.pdf` (new resume aligned to the job posting)


### 4) Recommended workflow

1. **Convert your existing PDF once** → YAML  
2. Maintain the YAML as your “master resume”  
3. For each job: `YAML + job URL → tailored PDF`

That keeps your source clean and avoids the usual PDF parsing pain.

#### Notes / limitations
- Works best for PDFs with clear ALL-CAPS section headers and the same structure as the generated template.
- PDFs are not a friendly “source format” — text extraction can lose bullets, spacing, and ordering.
- If something parses weirdly, fix the YAML once, then use YAML as your source of truth going forward.


---

## Sample input (resume YAML)

`examples/base_resume.yaml` is a minimal example. Your real resume can be longer; keep the same structure.

```yaml
name: "Sai Krishna Kishore Beathanabhotla"
contact:
  location: "Toronto, Ontario"
  email: "beathanabhotla.kishore@gmail.com"
  linkedin: "https://linkedin.com/in/saikrishnakishore"

sections:
  - title: "Summary"
    type: "bullets"
    items:
      - "Staff Data Scientist with 13+ years of experience..."
      - "Expert in <b>classical ML</b> and <b>Generative AI</b>..."

  - title: "Core Competencies"
    type: "core_competencies"
    blocks:
      - label: "Generative AI & NLP:"
        text: "RAG | Prompting | Fine-tuning | Transformers"

  - title: "Professional Experience"
    type: "experience"
    jobs:
      - role: "Staff Data Scientist"
        company: "SurveyMonkey"
        location: "Toronto, ON"
        dates: "01/2024 - Present"
        bullets:
          - "Built and deployed..."
        tech_stack: "Python, AWS, PyTorch, ..."
```

---

Notes:

* You can use limited HTML inside strings (e.g., `<b>bold</b>`, `<u>underline</u>`, `<br/>`) because ReportLab’s `Paragraph` supports a small HTML subset.
* Keep content truthful. The aligner will rewrite/re-rank but should not invent.

---

## How it works

### Step 1: Scrape job description

`app/scrape.py` fetches the URL and extracts the most likely JD block using generic heuristics.

### Step 2: Align resume to the job

`app/align.py` calls the LLM with:

* Your resume (structured JSON/YAML)
* The scraped job description text
* A prompt in `prompts/resume_align.txt` enforcing constraints like:

  * **No fabricated experience**
  * Use JD language where applicable
  * Reorder bullets by relevance
  * Keep bullet count sane per role

### Step 3: Generate PDF

`make_resume.py` renders a clean, consistent PDF style using ReportLab.

---

## LinkedIn URLs (important)

LinkedIn often blocks scraping from non-authenticated clients or rate-limits aggressively.

If a LinkedIn link fails:

* Try using the “job description text” from the page (copy/paste) in a future enhancement, or
* Add a Playwright-based scraper (headless browser), or
* Use a public JD link from the company’s site (usually easiest)

This repo is structured so you can swap the scraping layer without touching alignment or PDF rendering.

---

## Configuration

### Model

The LLM model is currently set in `app/align.py`. You can swap it for:

* another OpenAI model
* Azure OpenAI
* Bedrock / Claude (via a different client)
* local LLM (as long as you return valid JSON in the same schema)

### Prompt

Edit `prompts/resume_align.txt` to change tone, strictness, output size, etc.

---

## PDF -> YAML (import an existing resume)

If you already have a resume PDF in the same style/template, you can convert it into the structured YAML format used by this repo.

```bash
python tools/pdf_to_yaml.py --pdf path/to/resume.pdf --out resume.yaml
```

---

## Roadmap ideas

* Match scoring (resume ↔ JD) and “why” explanations
* Diff view: what changed vs base resume
* Multi-target batch mode: one resume → N tailored PDFs
* Cover letter generator using the same JD
* Playwright scraper adapter for LinkedIn
* FastAPI web app wrapper

---

## Disclaimer

This tool helps you *rephrase and prioritize* what you already did. It is not meant to fabricate experience or credentials. Always review the final PDF before using it.

---

## License
MIT
