from google import genai


def explain_concept(topic: str, level: str, client, model: str) -> str:
    prompt = f"""
    You are a helpful study buddy. Explain the concept of "{topic}" to a student at the "{level}" level.

    Follow these rules:
    - Use simple, clear language suitable for the level.
    - Use a real-world analogy if possible.
    - Break the explanation into 3 to 4 short paragraphs.
    - End with a section called "Key Takeaways" that has exactly 3 bullet points.
    - Do not use overly technical jargon for beginner level.
    """

    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text
    except Exception as e:
        return f"Error generating explanation: {str(e)}"