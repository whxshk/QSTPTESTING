"""
RAG (Retrieval-Augmented Generation) module for document processing and semantic search.
Handles document parsing, chunking, embedding, and FAISS-based retrieval.
"""

import docx2txt
import io
import logging
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state for embeddings model and index
_model = None
_index = None
_chunks = []
_metadata = []


def get_model():
    """Lazy load the sentence transformer model."""
    global _model
    if _model is None:
        logger.info("Loading sentence transformer model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Model loaded successfully")
    return _model


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from DOCX or PDF files.

    Args:
        file_bytes: Raw file content as bytes
        filename: Original filename with extension

    Returns:
        Extracted text content
    """
    filename_lower = filename.lower()

    try:
        if filename_lower.endswith(".pdf"):
            logger.info(f"Parsing PDF: {filename}")
            reader = PdfReader(io.BytesIO(file_bytes))
            text = "\n".join(
                page.extract_text() or "" for page in reader.pages
            )

        elif filename_lower.endswith(".docx"):
            logger.info(f"Parsing DOCX: {filename}")
            text = docx2txt.process(io.BytesIO(file_bytes))

        else:
            logger.warning(f"Unsupported file format: {filename}")
            return ""

        # Clean up excessive whitespace
        text = " ".join(text.split())

        if not text or len(text.strip()) < 50:
            logger.warning(f"Minimal text extracted from {filename} - may be image-based")

        return text

    except Exception as e:
        logger.error(f"Error extracting text from {filename}: {str(e)}")
        return ""


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    """
    Split text into overlapping chunks for better context preservation.

    Args:
        text: Input text to chunk
        chunk_size: Number of words per chunk
        overlap: Number of words to overlap between chunks

    Returns:
        List of text chunks
    """
    words = text.split()
    chunks = []
    i = 0

    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)
        i += chunk_size - overlap

        # Prevent infinite loop
        if i <= 0:
            i = chunk_size

    logger.info(f"Created {len(chunks)} chunks from {len(words)} words")
    return chunks


def build_index(files: List[Tuple[bytes, str]]) -> dict:
    """
    Build FAISS index from uploaded files.

    Args:
        files: List of (file_bytes, filename) tuples

    Returns:
        Dictionary with indexing statistics

    Raises:
        ValueError: If no valid text could be extracted
    """
    global _index, _chunks, _metadata

    _chunks = []
    _metadata = []

    logger.info(f"Building index from {len(files)} files")

    # Extract and chunk all files
    for file_bytes, filename in files:
        text = extract_text(file_bytes, filename)

        if text:
            file_chunks = chunk_text(text)
            _chunks.extend(file_chunks)
            _metadata.extend([{"filename": filename, "chunk_id": i}
                            for i in range(len(file_chunks))])
        else:
            logger.warning(f"No text extracted from {filename}")

    if not _chunks:
        raise ValueError(
            "No text could be extracted from the uploaded files. "
            "Please ensure files contain readable text (not just images)."
        )

    # Generate embeddings
    logger.info(f"Generating embeddings for {len(_chunks)} chunks...")
    model = get_model()
    embeddings = model.encode(
        _chunks,
        convert_to_numpy=True,
        show_progress_bar=False,
        batch_size=32
    )

    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)

    # Build FAISS index
    dimension = embeddings.shape[1]
    _index = faiss.IndexFlatIP(dimension)  # Inner product = cosine after normalization
    _index.add(embeddings)

    logger.info(f"Index built successfully with {_index.ntotal} vectors")

    return {
        "chunks_indexed": len(_chunks),
        "files_processed": len(files),
        "embedding_dimension": dimension
    }


def search(query: str, k: int = 8) -> List[Tuple[float, str, dict]]:
    """
    Perform semantic search over indexed documents.

    Args:
        query: Search query text
        k: Number of top results to return

    Returns:
        List of (score, chunk_text, metadata) tuples

    Raises:
        ValueError: If index hasn't been built yet
    """
    if _index is None or not _chunks:
        raise ValueError("No documents have been indexed yet. Please upload files first.")

    # Encode query
    model = get_model()
    query_embedding = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_embedding)

    # Search
    k = min(k, len(_chunks))  # Don't request more results than chunks
    distances, indices = _index.search(query_embedding, k)

    # Prepare results
    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(_chunks):  # Safety check
            results.append((
                float(distances[0][i]),
                _chunks[idx],
                _metadata[idx]
            ))

    logger.info(f"Retrieved {len(results)} chunks for query")
    return results


def get_index_stats() -> dict:
    """Get statistics about the current index."""
    return {
        "indexed": _index is not None,
        "total_chunks": len(_chunks),
        "index_size": _index.ntotal if _index else 0
    }


def clear_index():
    """Clear the current index and free memory."""
    global _index, _chunks, _metadata
    _index = None
    _chunks = []
    _metadata = []
    logger.info("Index cleared")
