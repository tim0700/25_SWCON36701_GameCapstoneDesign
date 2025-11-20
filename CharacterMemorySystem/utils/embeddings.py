"""
Embedding Service - Singleton for generating text embeddings.

This service manages a sentence-transformer model for generating
384-dimensional embeddings. Uses singleton pattern to ensure
only one model instance is loaded in memory.
"""
import logging
import threading
from typing import Union, List
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Singleton service for generating text embeddings using sentence-transformers.

    The model is loaded once and shared across all requests. Thread-safe
    for concurrent access.
    """

    _instance = None
    _lock = threading.Lock()
    _model = None
    _model_lock = threading.Lock()
    _model_name = None
    _device = None

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern: ensure only one instance exists.

        Args and kwargs are ignored here but accepted for compatibility with __init__.

        Returns:
            Single EmbeddingService instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    logger.debug("Created new EmbeddingService instance")
        return cls._instance

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "auto"):
        """
        Initialize the embedding service (called every time, but model loaded only once).

        Args:
            model_name: Hugging Face model identifier
            device: Device for inference ('auto', 'cpu', 'cuda', 'mps')
        """
        # Only set these if not already set (first initialization)
        if EmbeddingService._model_name is None:
            EmbeddingService._model_name = model_name
            EmbeddingService._device = device
            logger.info(
                f"EmbeddingService configured: model={model_name}, device={device}"
            )

    def _load_model(self) -> None:
        """
        Load the sentence-transformer model (thread-safe).

        This is called lazily on first use or explicitly via warmup().
        """
        if self._model is not None:
            return  # Already loaded

        with self._model_lock:
            # Double-check after acquiring lock
            if self._model is not None:
                return

            try:
                logger.info(f"Loading embedding model: {self._model_name}")
                logger.info("This may take 5-10 seconds on first run...")

                # Import here to avoid loading torch if not needed
                from sentence_transformers import SentenceTransformer

                # Determine device
                device = self._resolve_device(self._device)
                logger.info(f"Using device: {device}")

                # Load model
                EmbeddingService._model = SentenceTransformer(
                    self._model_name,
                    device=device
                )

                logger.info(
                    f"✓ Embedding model loaded successfully "
                    f"(~{self._get_model_size_mb()}MB RAM)"
                )

            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise RuntimeError(f"Could not load embedding model: {e}")

    def _resolve_device(self, device_config: str) -> str:
        """
        Resolve device configuration to actual device.

        Args:
            device_config: 'auto', 'cpu', 'cuda', or 'mps'

        Returns:
            Actual device string for sentence-transformers
        """
        if device_config in ['cpu', 'cuda', 'mps']:
            return device_config

        if device_config == 'auto':
            try:
                import torch
                if torch.cuda.is_available():
                    return 'cuda'
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    return 'mps'
                else:
                    return 'cpu'
            except ImportError:
                logger.warning("PyTorch not available, defaulting to CPU")
                return 'cpu'

        # Unknown config, default to CPU
        logger.warning(f"Unknown device config '{device_config}', defaulting to CPU")
        return 'cpu'

    def _get_model_size_mb(self) -> int:
        """
        Estimate model size in memory (approximate).

        Returns:
            Estimated size in MB
        """
        # all-MiniLM-L6-v2 is approximately 80-90MB
        # This is a rough estimate
        return 90

    def embed(self, texts: Union[str, List[str]], show_progress: bool = False) -> np.ndarray:
        """
        Generate embeddings for text(s).

        Args:
            texts: Single string or list of strings to embed
            show_progress: Show progress bar for batch processing

        Returns:
            numpy array of embeddings
            - Single text: shape (384,)
            - Multiple texts: shape (n, 384)

        Raises:
            RuntimeError: If model fails to load
        """
        # Ensure model is loaded
        self._load_model()

        # Convert single string to list for consistent processing
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]

        try:
            # Generate embeddings
            embeddings = self._model.encode(
                texts,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalize for cosine similarity
            )

            # Return single embedding if input was single string
            if is_single:
                return embeddings[0]

            return embeddings

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}")

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for large batches with memory efficiency.

        Args:
            texts: List of strings to embed
            batch_size: Process in batches to manage memory

        Returns:
            numpy array of embeddings, shape (n, 384)
        """
        if len(texts) <= batch_size:
            return self.embed(texts)

        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.embed(batch)
            all_embeddings.append(batch_embeddings)

        return np.vstack(all_embeddings)

    def warmup(self) -> None:
        """
        Preload the model (useful at application startup).

        This triggers model loading and performs a test inference
        to ensure everything works.
        """
        logger.info("Warming up embedding service...")
        self._load_model()

        # Test inference
        try:
            test_embedding = self.embed("test")
            assert test_embedding.shape == (384,), "Unexpected embedding shape"
            logger.info("✓ Embedding service warmed up and ready")
        except Exception as e:
            logger.error(f"Warmup failed: {e}")
            raise

    def is_loaded(self) -> bool:
        """
        Check if model is currently loaded in memory.

        Returns:
            True if model is loaded, False otherwise
        """
        return self._model is not None

    def unload(self) -> None:
        """
        Unload the model from memory (admin operation).

        This frees ~90MB of RAM. Model will be reloaded on next embed() call.
        """
        with self._model_lock:
            if self._model is not None:
                logger.info("Unloading embedding model from memory")
                del EmbeddingService._model
                EmbeddingService._model = None

                # Force garbage collection
                import gc
                gc.collect()

                logger.info("✓ Model unloaded, ~90MB RAM freed")
            else:
                logger.warning("Model not loaded, nothing to unload")

    def get_info(self) -> dict:
        """
        Get information about the embedding service.

        Returns:
            Dict with model info
        """
        return {
            "model_name": self._model_name,
            "device": self._device,
            "is_loaded": self.is_loaded(),
            "embedding_dimensions": 384,
            "estimated_ram_mb": 90 if self.is_loaded() else 0
        }
