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
_documents = []  # Store full document texts with metadata


def get_model():
    """Lazy load the sentence transformer model with retry logic."""
    global _model
    if _model is None:
        logger.info("Loading sentence transformer model...")
        try:
            _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            logger.info("Model loaded successfully")
        except PermissionError as e:
            logger.error(f"Permission error loading model: {e}")
            logger.info("Attempting to load model with cache disabled...")
            # Try loading without cache as fallback
            import os
            os.environ['TRANSFORMERS_OFFLINE'] = '0'
            _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", cache_folder=None)
            logger.info("Model loaded successfully (no cache)")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(
                "Failed to load sentence transformer model. "
                "This may be due to cache directory permissions. "
                "Please check the logs and rebuild the container."
            ) from e
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


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[Tuple[str, int, int]]:
    """
    Split text into overlapping chunks for better context preservation.

    Args:
        text: Input text to chunk
        chunk_size: Number of words per chunk
        overlap: Number of words to overlap between chunks

    Returns:
        List of (chunk_text, start_char, end_char) tuples
    """
    words = text.split()
    chunks = []
    i = 0
    char_position = 0

    while i < len(words):
        # Get chunk words
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)

        if chunk_text:  # Only add non-empty chunks
            # Find approximate character position in original text
            start_char = text.find(chunk_words[0], char_position)
            if start_char == -1:
                start_char = char_position

            end_char = start_char + len(chunk_text)
            chunks.append((chunk_text, start_char, end_char))
            char_position = end_char

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
    global _index, _chunks, _metadata, _documents

    _chunks = []
    _metadata = []
    _documents = []

    logger.info(f"Building index from {len(files)} files")

    # Extract and chunk all files
    for doc_idx, (file_bytes, filename) in enumerate(files):
        text = extract_text(file_bytes, filename)

        if text:
            # Store full document
            _documents.append({
                "id": doc_idx,
                "filename": filename,
                "full_text": text,
                "length": len(text)
            })

            # Create chunks with positions
            file_chunks_with_positions = chunk_text(text)

            for chunk_id, (chunk_text, start_char, end_char) in enumerate(file_chunks_with_positions):
                _chunks.append(chunk_text)
                _metadata.append({
                    "filename": filename,
                    "doc_id": doc_idx,
                    "chunk_id": chunk_id,
                    "start_char": start_char,
                    "end_char": end_char
                })
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
        "documents_stored": len(_documents),
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
        "total_documents": len(_documents),
        "index_size": _index.ntotal if _index else 0
    }


def get_documents() -> List[dict]:
    """Get all stored documents with their full text."""
    return _documents


def clear_index():
    """Clear the current index and free memory."""
    global _index, _chunks, _metadata, _documents
    _index = None
    _chunks = []
    _metadata = []
    _documents = []
    logger.info("Index cleared")
