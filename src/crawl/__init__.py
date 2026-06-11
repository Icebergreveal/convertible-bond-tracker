def load_config(*args, **kwargs):
    from .load_config import load_config as _load_config
    return _load_config(*args, **kwargs)

def search_announcements(*args, **kwargs):
    from .search_announcements import search_announcements as _search_announcements
    return _search_announcements(*args, **kwargs)

def download_pdfs(*args, **kwargs):
    from .download_pdfs import download_pdfs as _download_pdfs
    return _download_pdfs(*args, **kwargs)

def check_dataset(*args, **kwargs):
    from .check_dataset import check_dataset as _check_dataset
    return _check_dataset(*args, **kwargs)

__all__ = ["load_config", "search_announcements", "download_pdfs", "check_dataset"]
