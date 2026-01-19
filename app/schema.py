from typing import List, Dict
from pydantic import BaseModel


class Experience(BaseModel):
    role: str
    company: str
    location: str
    dates: str
    bullets: List[str]
    tech_stack: str


class Resume(BaseModel):
    summary: List[str]
    experience: List[Experience]
    skills: Dict[str, str]

