# photobrain/__init__.py

"""
PhotoBrain - Autonomous image ingestion and indexing for ImageStack.

This package is responsible for:
- Watching user-defined directories for new/changed images
- Deduplicating via file path + mtime + hash
- Sending images to ImageStack's ImageRAG ingestion endpoint
"""

__all__ = ["settings", "index_store", "ingestor"]

