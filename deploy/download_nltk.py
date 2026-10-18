"""Download required data during the build; never depend on startup egress."""
import os
from pathlib import Path

import nltk

destination = Path(os.environ.get("NLTK_DATA", "/opt/nltk_data"))
for name in ("punkt", "punkt_tab", "stopwords", "averaged_perceptron_tagger"):
    if not nltk.download(name, download_dir=str(destination), raise_on_error=True):
        raise RuntimeError(f"Could not download NLTK resource: {name}")

# resume_analyzer also checks this top-level path.
alias = destination / "stopwords"
if not alias.exists():
    alias.symlink_to("corpora/stopwords", target_is_directory=True)
