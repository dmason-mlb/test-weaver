import pytest

# test_1_vector_store_initialization.py
def test_qdrant_client_not_initialized():
    """Test that QdrantClient raises exception when not properly initialized"""
    from src.vector_store import ServerDrivenUIVectorStore
    
    store = ServerDrivenUIVectorStore()
    with pytest.raises(ConnectionError, match="Qdrant client not initialized"):
        store.health_check()

def test_collection_does_not_exist():
    """Test that accessing non-existent collection raises appropriate error"""
    from src.vector_store import ServerDrivenUIVectorStore
    
    store = ServerDrivenUIVectorStore(host="localhost", port=6333)
    with pytest.raises(ValueError, match="Collection 'ui_patterns' does not exist"):
        store.search_patterns("test query")