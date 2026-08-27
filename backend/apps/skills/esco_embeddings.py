"""
ESCO Skill Extractor with Embedding-Based Matching.

Uses vector similarity against pre-computed ESCO skill embeddings for
much more accurate skill extraction and taxonomy mapping than keyword matching.

Dependencies:
- sentence-transformers (for local embedding generation)
- numpy (for cosine similarity)
- Qdrant (optional, for large-scale vector search)
"""
import logging
from typing import List, Dict, Optional, Tuple
from functools import lru_cache

import numpy as np
from django.core.cache import cache

from .models import Skill

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.65
CACHE_TIMEOUT = 60 * 60 * 24


class ESCOEmbeddingMatcher:
    """
    Matches extracted skill strings to ESCO taxonomy using embeddings.

    Workflow:
    1. Embed the extracted skill text
    2. Compare against pre-computed ESCO skill embeddings
    3. Return best match above threshold
    """

    def __init__(self):
        self._model = None
        self._esco_embeddings = None
        self._esco_skills = None

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(EMBEDDING_MODEL)
            except ImportError:
                logger.warning("sentence-transformers not installed, using fallback matching")
        return self._model

    def _load_esco_embeddings(self):
        """Load all ESCO skill embeddings from DB into memory."""
        if self._esco_embeddings is not None:
            return

        skills_with_embeddings = Skill.objects.filter(
            embedding__isnull=False
        ).values_list('id', 'name', 'esco_uri', 'embedding')

        if not skills_with_embeddings:
            logger.info("No pre-computed ESCO embeddings found, will compute on demand")
            self._esco_embeddings = np.array([])
            self._esco_skills = []
            return

        self._esco_skills = []
        embeddings_list = []

        for skill_id, name, esco_uri, embedding in skills_with_embeddings:
            if embedding and isinstance(embedding, list):
                self._esco_skills.append({
                    'id': skill_id,
                    'name': name,
                    'esco_uri': esco_uri,
                })
                embeddings_list.append(embedding)

        self._esco_embeddings = np.array(embeddings_list) if embeddings_list else np.array([])

    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for a text string."""
        if self.model is None:
            return None
        return self.model.encode(text, normalize_embeddings=True)

    def find_best_match(self, skill_text: str) -> Optional[Dict]:
        """
        Find the best ESCO skill match for a given skill text.

        Returns dict with matched skill info and similarity score, or None.
        """
        cache_key = f"esco_match:{skill_text.lower().strip()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached if cached != "none" else None

        self._load_esco_embeddings()

        if self._esco_embeddings.size == 0:
            result = self._fallback_match(skill_text)
            cache.set(cache_key, result or "none", CACHE_TIMEOUT)
            return result

        query_embedding = self.embed_text(skill_text)
        if query_embedding is None:
            result = self._fallback_match(skill_text)
            cache.set(cache_key, result or "none", CACHE_TIMEOUT)
            return result

        similarities = np.dot(self._esco_embeddings, query_embedding)
        best_idx = np.argmax(similarities)
        best_score = float(similarities[best_idx])

        if best_score >= SIMILARITY_THRESHOLD:
            matched = self._esco_skills[best_idx]
            result = {
                'skill_id': str(matched['id']),
                'name': matched['name'],
                'esco_uri': matched['esco_uri'],
                'similarity': round(best_score, 4),
            }
        else:
            result = self._fallback_match(skill_text)

        cache.set(cache_key, result or "none", CACHE_TIMEOUT)
        return result

    def find_top_matches(self, skill_text: str, top_k: int = 5) -> List[Dict]:
        """Find top-K ESCO skill matches for a given skill text."""
        self._load_esco_embeddings()

        if self._esco_embeddings.size == 0:
            match = self._fallback_match(skill_text)
            return [match] if match else []

        query_embedding = self.embed_text(skill_text)
        if query_embedding is None:
            match = self._fallback_match(skill_text)
            return [match] if match else []

        similarities = np.dot(self._esco_embeddings, query_embedding)
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= SIMILARITY_THRESHOLD * 0.8:
                matched = self._esco_skills[idx]
                results.append({
                    'skill_id': str(matched['id']),
                    'name': matched['name'],
                    'esco_uri': matched['esco_uri'],
                    'similarity': round(score, 4),
                })

        return results

    def _fallback_match(self, skill_text: str) -> Optional[Dict]:
        """Fallback to DB text matching when embeddings aren't available."""
        skill = Skill.objects.filter(name__iexact=skill_text).first()
        if not skill:
            skill = Skill.objects.filter(name__icontains=skill_text).first()
        if skill:
            return {
                'skill_id': str(skill.id),
                'name': skill.name,
                'esco_uri': skill.esco_uri,
                'similarity': 0.9 if skill.name.lower() == skill_text.lower() else 0.7,
            }
        return None

    def batch_match(self, skill_texts: List[str]) -> List[Optional[Dict]]:
        """Match a batch of skill texts to ESCO taxonomy."""
        return [self.find_best_match(text) for text in skill_texts]

    def compute_skill_embedding(self, skill: Skill) -> bool:
        """Compute and store embedding for a single ESCO skill."""
        if self.model is None:
            return False

        text = f"{skill.name}. {skill.description}" if skill.description else skill.name
        embedding = self.model.encode(text, normalize_embeddings=True)
        skill.embedding = embedding.tolist()
        skill.save(update_fields=['embedding'])
        return True

    def compute_all_embeddings(self, batch_size: int = 100) -> int:
        """Compute embeddings for all skills that don't have one yet."""
        if self.model is None:
            logger.error("Cannot compute embeddings: sentence-transformers not installed")
            return 0

        skills_without = Skill.objects.filter(embedding__isnull=True)
        total = skills_without.count()
        computed = 0

        for i in range(0, total, batch_size):
            batch = list(skills_without[i:i + batch_size])
            texts = [
                f"{s.name}. {s.description}" if s.description else s.name
                for s in batch
            ]
            embeddings = self.model.encode(texts, normalize_embeddings=True, batch_size=batch_size)

            for skill, embedding in zip(batch, embeddings):
                skill.embedding = embedding.tolist()

            Skill.objects.bulk_update(batch, ['embedding'], batch_size=batch_size)
            computed += len(batch)
            logger.info(f"Computed embeddings: {computed}/{total}")

        self._esco_embeddings = None
        self._esco_skills = None
        return computed


_matcher: Optional[ESCOEmbeddingMatcher] = None


def get_esco_matcher() -> ESCOEmbeddingMatcher:
    global _matcher
    if _matcher is None:
        _matcher = ESCOEmbeddingMatcher()
    return _matcher
