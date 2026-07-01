"""
Generates interview questions dynamically using a locally-running LLM via
Ollama, instead of relying solely on a fixed, pre-written question database.

Why this exists:
    A hardcoded questions_db only ever covers the handful of skills someone
    thought to write questions for ahead of time. As the skill database
    grows (see seed_data.py), maintaining matching hand-written questions
    for every skill doesn't scale. This module asks a local LLM to generate
    a few questions on demand for whatever skill is missing, with results
    cached in the database so the same skill is never regenerated twice.

Requires Ollama running locally (https://ollama.com) with a model pulled:
    ollama pull llama3.2:1b

If Ollama isn't running or generation fails for any reason, this falls back
to the existing curated InterviewQuestionDB seed data — the app should never
break just because the local model isn't available.
"""
import json
import re
import requests
from typing import List, Dict, Optional

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"
# First request after Ollama starts cold-loads the model into memory,
# which can take 30-60s on CPU. Subsequent requests are much faster.
# 60s covers the cold-start case without hanging indefinitely.
OLLAMA_TIMEOUT_SECONDS = 60


def _build_prompt(skill: str) -> str:
    return (
        f"Generate exactly 3 technical interview questions for a candidate "
        f"claiming the skill \"{skill}\". Questions should range from easy "
        f"to hard. Respond with ONLY a JSON array, no other text, in this "
        f"exact format:\n"
        f'[{{"question": "...", "difficulty": "easy|medium|hard"}}, ...]'
    )


def _extract_json_array(raw_text: str) -> Optional[list]:
    """
    LLMs frequently wrap JSON in markdown fences or add stray commentary
    even when explicitly told not to. This pulls out the first valid JSON
    array found in the response rather than assuming raw_text is clean JSON.
    """
    match = re.search(r"\[.*\]", raw_text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def generate_questions_for_skill(skill: str, topic: Optional[str] = None) -> Optional[List[Dict]]:
    """
    Calls the local Ollama model to generate questions for a single skill.
    Returns None (not an empty list) on any failure, so callers can
    distinguish "model returned zero questions" from "model is unavailable"
    and fall back to the curated database accordingly.
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": _build_prompt(skill),
                "stream": False,
                "options": {"temperature": 0.7},
            },
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print(f"[question_generator] Timeout generating questions for '{skill}' — model cold-starting?")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[question_generator] Ollama unreachable for '{skill}': {e}")
        return None

    raw_text = response.json().get("response", "")
    parsed = _extract_json_array(raw_text)
    if not parsed:
        print(f"[question_generator] Could not parse JSON from model output for '{skill}': {raw_text[:200]}")
        return None

    print(f"[question_generator] Generated {len(parsed)} questions for '{skill}'")

    questions = []
    for item in parsed:
        if not isinstance(item, dict) or "question" not in item:
            continue
        questions.append({
            "question": item["question"],
            "difficulty": item.get("difficulty", "medium"),
            "topic": topic or skill,
            "skill": skill,
            "source": "generated",  # lets the frontend/debugging distinguish AI-generated from curated
        })

    return questions if questions else None