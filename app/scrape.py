import requests
from bs4 import BeautifulSoup


def scrape_job_description(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # Generic heuristic: works for most JD pages
    candidates = soup.find_all(["section", "div"], recursive=True)

    text_blocks = []
    for c in candidates:
        if c.get_text(strip=True) and len(c.get_text()) > 500:
            text_blocks.append(c.get_text(" ", strip=True))

    if not text_blocks:
        raise RuntimeError("Could not extract job description")

    # Pick the largest block
    return max(text_blocks, key=len)
