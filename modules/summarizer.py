import PyPDF2
from docx import Document
from google import genai
import time


def extract_text(uploaded_file) -> str:
    filename = uploaded_file.name
    try:
        if filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(uploaded_file)
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return " ".join(pages)
        elif filename.endswith(".docx"):
            doc = Document(uploaded_file)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return " ".join(paragraphs)
        elif filename.endswith(".txt"):
            return uploaded_file.read().decode("utf-8")
        else:
            return ""
    except Exception as e:
        return f"Error reading file: {str(e)}"


def summarize_notes(text: str, client, model: str) -> str:
    if not text or text.startswith("Error"):
        return "Could not read the file. Please try again with a valid PDF, DOCX, or TXT."

    prompt = f"""
    You are a helpful study buddy. Summarize the following study notes clearly and concisely.

    Structure your response exactly like this:

    ## Summary
    Write 2 to 3 sentences giving an overall summary of what these notes are about.

    ## Key Concepts
    List the 5 most important concepts or ideas from the notes as bullet points.
    Each bullet should be one clear sentence.

    ## Important Definitions or Formulas
    If there are any definitions or formulas in the notes, list them here.
    If there are none, write "None found."

    ## What to Review
    List 3 topics the student should study further based on these notes.

    Notes:
    {text[:4000]}
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            return response.text
        except Exception as e:
            error_str = str(e)
            is_overloaded = "503" in error_str or "UNAVAILABLE" in error_str
            if is_overloaded and attempt < max_retries - 1:
                time.sleep(3 * (attempt + 1))  # wait 3s, then 6s
                continue
            return f"Error generating summary: {error_str}"