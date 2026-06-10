"""Project configuration — paths and chunking parameters."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Folder holding the cleaned .txt source documents.
DOCS_PATH = os.path.join(BASE_DIR, "documents")

# Chunking parameters (see planning.md > Chunking Strategy).
CHUNK_SIZE = 600        # characters per chunk (~150 tokens)
CHUNK_OVERLAP = 50      # characters duplicated at each boundary
MIN_CHUNK_LENGTH = 50   # drop fragments shorter than this
