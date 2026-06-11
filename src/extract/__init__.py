from .validate_results import validate_results

def extract_fields(*args, **kwargs):
    from .llm_extract import extract_fields as _extract_fields
    return _extract_fields(*args, **kwargs)

__all__ = ["extract_fields", "validate_results"]
