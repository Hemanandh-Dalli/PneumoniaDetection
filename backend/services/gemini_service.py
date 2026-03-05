from google import genai
import os
from dotenv import load_dotenv
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

DEFAULT_MODEL_CANDIDATES = [
    # Keep this list aligned with models visible from /v1beta/models for this project.
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemma-3-4b-it",
    "gemma-3-1b-it",
]
_CLIENT = None
_CLIENT_KEY = None


def _get_client() -> genai.Client:
    global _CLIENT, _CLIENT_KEY
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing in backend/.env")
    if _CLIENT is None or _CLIENT_KEY != api_key:
        _CLIENT = genai.Client(api_key=api_key)
        _CLIENT_KEY = api_key
    return _CLIENT


def _model_candidates() -> list[str]:
    env_model = (os.getenv("GEMINI_MODEL") or "").strip()
    if env_model.startswith("models/"):
        env_model = env_model.split("models/", 1)[1]
    if env_model:
        return [env_model] + [m for m in DEFAULT_MODEL_CANDIDATES if m != env_model]
    return DEFAULT_MODEL_CANDIDATES.copy()


def _is_quota_or_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "429" in msg
        or "resource_exhausted" in msg
        or "quota exceeded" in msg
        or "rate limit" in msg
    )


def _is_model_not_found_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return ("404" in msg and "not_found" in msg) or "is not found" in msg


def _generate_with_fallback(prompt: str) -> str:
    last_exc = None
    for model_name in _model_candidates():
        try:
            response = _get_client().models.generate_content(
                model=model_name,
                contents=prompt,
            )
            text = (response.text or "").strip()
            if text:
                return text
            last_exc = RuntimeError(f"Empty response from model: {model_name}")
        except Exception as e:
            last_exc = e
            print(f"GEMINI ERROR ({model_name}):", e)
            # Try the next model when this one is unavailable or quota-limited.
            if _is_quota_or_rate_limit_error(e) or _is_model_not_found_error(e):
                continue
            # For other errors, fail fast.
            else:
                break

    raise RuntimeError(last_exc) if last_exc else RuntimeError("Gemini request failed")


def _local_explanation(predicted_class: str, confidence: float, max_lines: int) -> str:
    pct = round(confidence * 100, 1)
    cls = (predicted_class or "").strip().lower()

    if "bacterial" in cls:
        summary = "The scan pattern may match bacterial pneumonia."
    elif "viral" in cls:
        summary = "The scan pattern may match viral pneumonia."
    elif "normal" in cls:
        summary = "The scan does not show a strong pneumonia pattern."
    else:
        summary = "The scan result suggests a possible chest finding."

    lines = [
        f"Model result: {predicted_class} ({pct}% confidence).",
        summary,
        "This is a screening output, not a final diagnosis.",
        "Please consult a qualified doctor for clinical confirmation.",
    ]
    return "\n".join(lines[:max_lines])


def _local_chat_fallback() -> str:
    return (
        "I cannot access AI right now due to API quota limits.\n"
        "If symptoms are worsening (breathlessness, high fever, chest pain), seek urgent care.\n"
        "For routine follow-up, consult a doctor and share your report."
    )


def explain_prediction(predicted_class: str, confidence: float, max_lines: int = 5) -> str:
    prompt = f"""
You are a medical AI assistant.

Explain the chest X-ray result in very simple language.
Limit the explanation to {max_lines} short lines.
Do not use medical jargon.
Do not give treatment advice.

Prediction: {predicted_class}
Confidence: {confidence:.2f}
"""

    try:
        text = _generate_with_fallback(prompt)

        # hard safety cut (just in case Gemini talks too much)
        lines = text.splitlines()
        return "\n".join(lines[:max_lines])

    except Exception as e:
        print("GEMINI ERROR:", e)
        return _local_explanation(predicted_class, confidence, max_lines)


def chat_with_gemini(conversation: str) -> str:
    """Shared chat function used by the chat route."""
    try:
        text = _generate_with_fallback(
            f"""
You are a medical assistant.

Conversation so far:
{conversation}

Rules:
- Simple language
- Max 4 lines
- No diagnosis
- No prescribing medicine
- Give precautions and when to consult doctor
"""
        )

        lines = text.splitlines()
        return "\n".join(lines[:4]).strip()

    except Exception as e:
        print("GEMINI ERROR:", e)
        return _local_chat_fallback()
