import json
import re
from google import genai


def generate_quiz(topic: str, num_questions: int, client, model: str) -> list:
    prompt = f"""
    You are a quiz generator. Create exactly {num_questions} multiple choice questions about "{topic}".

    Rules:
    - Each question must have exactly 4 options labeled A, B, C, D.
    - The answer field must be just the letter: A, B, C, or D.
    - The explanation must be 1 to 2 sentences explaining why the answer is correct.
    - Return ONLY a valid JSON array. No extra text, no markdown, no explanation outside the JSON.

    Use this exact format:
    [
      {{
        "question": "Your question here?",
        "options": ["A. Option one", "B. Option two", "C. Option three", "D. Option four"],
        "answer": "A",
        "explanation": "Explanation of why A is correct."
      }}
    ]
    """

    try:
        response = client.models.generate_content(model=model, contents=prompt)
        text = response.text.strip()
        text = re.sub(r"```json|```", "", text).strip()
        questions = json.loads(text)
        return questions
    except json.JSONDecodeError:
        return []
    except Exception as e:
        return []


def check_answers(questions: list, user_answers: dict) -> dict:
    score = 0
    results = []

    for i, q in enumerate(questions):
        user_choice = user_answers.get(i, None)
        correct_letter = q["answer"].strip().upper()

        is_correct = False
        if user_choice:
            chosen_letter = user_choice[0].upper()
            is_correct = chosen_letter == correct_letter

        if is_correct:
            score += 1

        results.append({
            "question": q["question"],
            "user_answer": user_choice,
            "correct_answer": next((o for o in q["options"] if o.startswith(correct_letter)), correct_letter),
            "is_correct": is_correct,
            "explanation": q["explanation"]
        })

    return {"score": score, "total": len(questions), "results": results}