import json
from openai import OpenAI

# Use Ollama running locally
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Ollama doesn't require a real API key
)


def align_resume(resume: dict, job_description: str) -> dict:
    with open("prompts/resume_align.txt") as f:
        prompt = f.read()

    prompt = prompt.replace("{{ resume }}", json.dumps(resume, indent=2))
    prompt = prompt.replace("{{ job_description }}", job_description)

    response = client.chat.completions.create(
        model="kimi-k2-thinking:cloud",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    print(response)

    return json.loads(response.choices[0].message.content)
