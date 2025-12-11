from typing import Optional, Tuple


def infer_provider_from_model(model_id: str) -> Optional[str]:
    """Infer provider from a model id heuristic."""
    mid = model_id.lower()
    if mid.startswith(("seedream", "volcengine")) or "doubao" in mid or "seedream" in mid:
        return "volcengine"
    if mid.startswith("deepseek"):
        return "deepseek"
    if mid.startswith(("keling", "kling")):
        return "keling"
    if mid.startswith("jimeng"):
        return "jimeng"
    if mid.startswith(("dall-e", "dalle", "gpt-image-1")):
        return "openai"
    if mid.startswith("gemini"):
        return "google"
    return None


def parse_model_and_provider(model: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Split provider:model strings and infer provider when absent.

    Returns (clean_model_id, provider_hint).
    """
    if not model:
        return None, None
    raw = model.strip()
    if not raw:
        return None, None

    provider_hint: Optional[str] = None
    clean_model = raw

    if ":" in raw:
        provider_hint, clean_model = raw.split(":", 1)
        provider_hint = provider_hint or None
        clean_model = clean_model or None

    if clean_model:
        inferred = infer_provider_from_model(clean_model)
        provider_hint = provider_hint or inferred

    return clean_model, provider_hint


def normalize_openai_image_style(style: Optional[str]) -> str:
    """
    Normalize style for OpenAI image endpoints: supported only 'vivid' or 'natural'.
    Defaults to 'natural' when unspecified or invalid.
    """
    if not style:
        return "natural"
    s = style.lower()
    if s in {"vivid", "natural"}:
        return s
    # map common synonyms
    if s in {"realistic", "realism", "photo", "photorealistic"}:
        return "natural"
    return "natural"
