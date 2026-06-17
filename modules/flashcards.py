import json
import re
from google import genai


def generate_flashcards(topic: str, num_cards: int, client, model: str) -> list:
    prompt = f"""
    You are a flashcard generator. Create exactly {num_cards} flashcards about "{topic}".

    Rules:
    - The front should be a question or a key term.
    - The back should be the answer or a clear definition (1 to 3 sentences max).
    - Cover different aspects of the topic, not just definitions.
    - Return ONLY a valid JSON array. No extra text, no markdown outside the JSON.

    Use this exact format:
    [
      {{
        "front": "What is gradient descent?",
        "back": "Gradient descent is an optimization algorithm that minimizes a function by iteratively moving in the direction of steepest descent."
      }}
    ]
    """

    try:
        response = client.models.generate_content(model=model, contents=prompt)
        text = response.text.strip()
        text = re.sub(r"```json|```", "", text).strip()
        cards = json.loads(text)
        return cards
    except Exception as e:
        return []


def generate_flashcards_from_notes(notes_text: str, num_cards: int, client, model: str) -> list:
    prompt = f"""
    You are a flashcard generator. Read the following study notes and create exactly {num_cards} flashcards from them.

    Rules:
    - The front should be a question or key term from the notes.
    - The back should be the answer or definition, taken from the notes.
    - Return ONLY a valid JSON array. No extra text.

    Format:
    [
      {{
        "front": "Question or term",
        "back": "Answer or definition"
      }}
    ]

    Notes:
    {notes_text[:4000]}
    """

    try:
        response = client.models.generate_content(model=model, contents=prompt)
        text = response.text.strip()
        text = re.sub(r"```json|```", "", text).strip()
        cards = json.loads(text)
        return cards
    except Exception as e:
        return []