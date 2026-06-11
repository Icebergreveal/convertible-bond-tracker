def batch_parse_pdfs(*args, **kwargs):
    from .mineru_batch_parse import batch_parse_pdfs as _batch_parse_pdfs
    return _batch_parse_pdfs(*args, **kwargs)

def check_parse_quality(*args, **kwargs):
    from .parse_check import check_parse_quality as _check_parse_quality
    return _check_parse_quality(*args, **kwargs)

__all__ = ["batch_parse_pdfs", "check_parse_quality"]
