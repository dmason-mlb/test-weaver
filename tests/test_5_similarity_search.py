import pytest

# test_5_similarity_search.py
def test_similarity_search_no_embeddings():
    """Test that similarity search fails when no embeddings exist"""
    from src.similarity_engine import TestSimilarityEngine
    
    engine = TestSimilarityEngine()
    with pytest.raises(RuntimeError, match="No embeddings in vector store"):
        engine.find_similar_tests("login flow test")

def test_similarity_threshold_not_met():
    """Test that low similarity scores return empty results"""
    from src.similarity_engine import TestSimilarityEngine
    
    engine = TestSimilarityEngine(similarity_threshold=0.95)
    engine.add_test_embedding("test_1", [0.1, 0.2, 0.3])
    
    results = engine.find_similar_tests("completely unrelated query", min_similarity=0.95)
    assert results == [], "Should return no results when similarity threshold not met"

def test_embedding_dimension_mismatch():
    """Test that mismatched embedding dimensions raise error"""
    from src.similarity_engine import TestSimilarityEngine
    
    engine = TestSimilarityEngine(embedding_dim=384)
    with pytest.raises(ValueError, match="Embedding dimension mismatch: expected 384, got 768"):
        engine.add_test_embedding("test_1", [0.1] * 768)