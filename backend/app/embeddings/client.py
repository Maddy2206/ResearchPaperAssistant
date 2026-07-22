from sentence_transformers import SentenceTransformer

from app.config import get_settings

_model_singleton: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model_singleton
    if _model_singleton is None:
        settings = get_settings()
        _model_singleton = SentenceTransformer(settings.embedding_model)
    return _model_singleton


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
