import time
import json
import re


def review_resume(text: str, client, model: str) -> dict:
    """
    Sends resume text to Gemini and returns structured feedback as a dict.
    """
    prompt = f"""
You are an expert resume reviewer and ATS specialist. Analyze the resume below and respond ONLY with valid JSON, no markdown, no backticks, no extra text.

Return exactly this structure:
{{
  "overall_score": <integer 1-10>,
  "overall_summary": "<2-3 sentence overall assessment>",
  "ats_score": <integer 1-10>,
  "ats_issues": ["<issue 1>", "<issue 2>"],
  "sections": {{
    "summary": {{"score": <1-10>, "feedback": "<feedback>", "present": <true/false>}},
    "education": {{"score": <1-10>, "feedback": "<feedback>", "present": <true/false>}},
    "experience": {{"score": <1-10>, "feedback": "<feedback>", "present": <true/false>}},
    "skills": {{"score": <1-10>, "feedback": "<feedback>", "present": <true/false>}},
    "projects": {{"score": <1-10>, "feedback": "<feedback>", "present": <true/false>}}
  }},
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "improvements": ["<improvement 1>", "<improvement 2>", "<improvement 3>"]
}}

Resume:
{text[:5000]}
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            raw = response.text.strip()
            # Strip markdown fences if Gemini adds them
            raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
            return json.loads(raw)
        except Exception as e:
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            return {"error": str(e)}