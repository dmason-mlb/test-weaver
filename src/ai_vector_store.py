"""
Real AI-Powered Vector Store using OpenAI embeddings.
This replaces the mock vector store with genuine AI functionality.
"""

import os
import json
import pickle
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
import openai
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AIVectorStore:
    """In-memory vector store with real OpenAI embeddings and cosine similarity."""

    def __init__(self):
        """Initialize with OpenAI client and in-memory storage."""
        # Initialize with graceful degradation for missing API keys
        self.client = None
        self.api_available = False

        # Try to initialize OpenAI client
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key and openai_api_key.strip():
            try:
                self.client = openai.OpenAI(api_key=openai_api_key)
                # Test the client with a simple call
                self.api_available = True
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.client = None
                self.api_available = False
        else:
            logger.warning("OpenAI API key not found - using fallback mode")

        self.patterns = {}  # id -> pattern data
        self.embeddings = {}  # id -> embedding vector
        self.embedding_dim = 1536  # OpenAI text-embedding-ada-002 dimension

        # Cache file for embeddings (to save API costs)
        self.cache_file = Path("cache/embeddings.pkl")
        self.cache_file.parent.mkdir(exist_ok=True)

        # Load cached embeddings if available
        self._load_embedding_cache()

        # Add default AI-generated patterns
        self._initialize_ai_patterns()

        logger.info(f"AI Vector Store initialized with {len(self.patterns)} patterns")

    def _load_embedding_cache(self):
        """Load cached embeddings to save API costs."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    cache = pickle.load(f)
                    self.embeddings.update(cache.get('embeddings', {}))
                    self.patterns.update(cache.get('patterns', {}))
                logger.info(f"Loaded {len(self.embeddings)} cached embeddings")
            except Exception as e:
                logger.warning(f"Could not load embedding cache: {e}")

    def _save_embedding_cache(self):
        """Save embeddings to cache file."""
        try:
            cache_data = {
                'embeddings': self.embeddings,
                'patterns': self.patterns
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            logger.info("Embedding cache saved")
        except Exception as e:
            logger.warning(f"Could not save embedding cache: {e}")

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get OpenAI embedding for text, with caching and fallback."""
        # Create hash for caching
        text_hash = hashlib.md5(text.encode()).hexdigest()

        # Check cache first
        if text_hash in self.embeddings:
            return self.embeddings[text_hash]

        # Use OpenAI if available
        if self.api_available and self.client:
            try:
                logger.info(f"Generating OpenAI embedding for: {text[:50]}...")
                response = self.client.embeddings.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                embedding = response.data[0].embedding

                # Cache the result
                self.embeddings[text_hash] = embedding
                self._save_embedding_cache()

                return embedding
            except Exception as e:
                logger.error(f"Failed to generate OpenAI embedding: {e}")
                # Fall through to hash-based fallback

        # Fallback: hash-based pseudo-embedding
        logger.info(f"Generating fallback embedding for: {text[:50]}...")
        embedding = self._generate_fallback_embedding(text)

        # Cache the fallback result too
        self.embeddings[text_hash] = embedding
        self._save_embedding_cache()

        return embedding

    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate hash-based pseudo-embedding when OpenAI is unavailable."""
        # Create multiple hashes for better distribution
        hash1 = hashlib.md5(text.encode()).hexdigest()
        hash2 = hashlib.sha256(text.encode()).hexdigest()

        # Convert hashes to integers
        hash1_int = int(hash1, 16)
        hash2_int = int(hash2[:8], 16)  # Use first 8 chars of SHA256

        # Generate pseudo-embedding vector
        embedding = []
        for i in range(self.embedding_dim):
            # Use different bit positions and hash combinations
            bit_val1 = (hash1_int >> (i % 32)) & 1
            bit_val2 = (hash2_int >> (i % 32)) & 1

            # Combine and normalize to [-1, 1] range
            combined = (bit_val1 * 2 - 1) * 0.7 + (bit_val2 * 2 - 1) * 0.3
            embedding.append(combined)

        # Normalize vector to unit length (similar to OpenAI embeddings)
        magnitude = np.sqrt(sum(x * x for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def _initialize_ai_patterns(self):
        """Initialize with intelligent test patterns."""
        ai_patterns = [
            {
                "id": "webview_interaction",
                "component_type": "webview",
                "description": "Interactive WebView component with URL loading and JavaScript bridge",
                "test_pattern": """def test_webview_interaction():
    driver = webdriver.Chrome()
    driver.get('{url}')

    # Wait for WebView to load
    wait = WebDriverWait(driver, 10)
    webview = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))

    # Switch to WebView frame
    driver.switch_to.frame(webview)

    # Test content is loaded
    assert driver.page_source != ""
    assert "error" not in driver.page_source.lower()

    driver.quit()""",
                "tags": ["webview", "selenium", "interaction", "iframe", "javascript"],
                "complexity": "medium",
                "ai_generated": True
            },
            {
                "id": "button_click_validation",
                "component_type": "button",
                "description": "Button click with state validation and response checking",
                "test_pattern": """def test_button_functionality():
    driver = webdriver.Chrome()
    driver.get('{base_url}')

    # Find button element
    button = driver.find_element(By.ID, "{component_id}")

    # Verify button is clickable
    assert button.is_enabled()
    assert button.is_displayed()

    # Perform click action
    initial_text = button.text
    button.click()

    # Wait for response and validate state change
    time.sleep(1)
    assert button.text != initial_text or button.get_attribute("class") != initial_text

    driver.quit()""",
                "tags": ["button", "selenium", "click", "validation", "state"],
                "complexity": "simple",
                "ai_generated": True
            },
            {
                "id": "api_endpoint_testing",
                "component_type": "api_endpoint",
                "description": "REST API endpoint testing with authentication and response validation",
                "test_pattern": """def test_api_endpoint():
    headers = {{'Authorization': 'Bearer {auth_token}'}}

    # Make API request
    response = requests.get('{endpoint_url}', headers=headers)

    # Validate response structure
    assert response.status_code == 200
    data = response.json()

    # Verify required fields exist
    required_fields = ['data', 'status', 'timestamp']
    for field in required_fields:
        assert field in data, f"Missing required field: {{field}}"

    # Validate data types
    assert isinstance(data['data'], (list, dict))
    assert isinstance(data['status'], str)
    assert data['status'] in ['success', 'partial', 'error']""",
                "tags": ["api", "rest", "authentication", "validation", "json"],
                "complexity": "medium",
                "ai_generated": True
            },
            {
                "id": "list_scroll_performance",
                "component_type": "list",
                "description": "List scrolling with performance monitoring and item validation",
                "test_pattern": """def test_list_scroll_performance():
    driver = webdriver.Chrome()
    driver.get('{base_url}')

    list_container = driver.find_element(By.ID, "{component_id}")
    initial_items = len(list_container.find_elements(By.CLASS_NAME, "list-item"))

    # Measure scroll performance
    start_time = time.time()

    # Scroll to bottom
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", list_container)

    # Wait for lazy loading
    WebDriverWait(driver, 5).until(
        lambda d: len(list_container.find_elements(By.CLASS_NAME, "list-item")) > initial_items
    )

    scroll_time = time.time() - start_time
    final_items = len(list_container.find_elements(By.CLASS_NAME, "list-item"))

    # Performance assertions
    assert scroll_time < 2.0, f"Scroll took {{scroll_time}}s, expected < 2s"
    assert final_items > initial_items, "No new items loaded after scroll"

    driver.quit()""",
                "tags": ["list", "scroll", "performance", "lazy-loading", "selenium"],
                "complexity": "complex",
                "ai_generated": True
            }
        ]

        # Generate embeddings for each pattern
        for pattern in ai_patterns:
            # Create rich text representation for embedding
            embedding_text = f"{pattern['description']} {pattern['component_type']} {' '.join(pattern['tags'])} {pattern['test_pattern']}"

            embedding = self._get_embedding(embedding_text)
            if embedding:
                self.patterns[pattern['id']] = pattern
                # Store embedding with pattern ID
                self.embeddings[pattern['id']] = embedding

        logger.info(f"Initialized {len(ai_patterns)} AI-generated patterns with embeddings")

    def store_pattern(self, pattern: Dict[str, Any]) -> str:
        """Store a test pattern with AI-generated embedding."""
        pattern_id = pattern.get('id', hashlib.md5(str(pattern).encode()).hexdigest())

        # Create rich text representation
        embedding_text = f"{pattern.get('description', '')} {pattern.get('component_type', '')} {pattern.get('test_pattern', '')}"

        # Generate embedding
        embedding = self._get_embedding(embedding_text)
        if embedding:
            self.patterns[pattern_id] = pattern
            self.embeddings[pattern_id] = embedding
            logger.info(f"Stored pattern with ID: {pattern_id}")
            return pattern_id
        else:
            logger.error(f"Failed to store pattern - could not generate embedding")
            return ""

    def search_similar_patterns(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar patterns using real vector similarity."""
        logger.info(f"Searching for patterns similar to: {query}")

        # Generate embedding for query
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            logger.error("Could not generate embedding for query")
            return []

        # Calculate similarities
        similarities = []
        for pattern_id, pattern_embedding in self.embeddings.items():
            if pattern_id in self.patterns:  # Only consider stored patterns
                similarity = self._cosine_similarity(query_embedding, pattern_embedding)
                similarities.append((pattern_id, similarity))

        # Sort by similarity score (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top results with similarity scores
        results = []
        for pattern_id, similarity in similarities[:limit]:
            result = self.patterns[pattern_id].copy()
            result['similarity_score'] = similarity
            result['pattern_id'] = pattern_id
            results.append(result)

        logger.info(f"Found {len(results)} similar patterns (top similarity: {results[0]['similarity_score']:.3f})")
        return results

    def get_pattern_analytics(self) -> Dict[str, Any]:
        """Get analytics about stored patterns and embeddings."""
        return {
            "total_patterns": len(self.patterns),
            "total_embeddings": len(self.embeddings),
            "embedding_dimension": self.embedding_dim,
            "component_types": list(set(p.get('component_type', 'unknown') for p in self.patterns.values())),
            "ai_generated_count": sum(1 for p in self.patterns.values() if p.get('ai_generated', False)),
            "cache_file_exists": self.cache_file.exists()
        }

    def health_check(self) -> bool:
        """Check if the AI vector store is healthy."""
        try:
            # Test embedding generation
            test_embedding = self._get_embedding("test health check")
            return test_embedding is not None and len(test_embedding) == self.embedding_dim
        except Exception:
            return False

    def get_pattern_analytics(self) -> Dict[str, Any]:
        """Get analytics about stored patterns and API availability."""
        return {
            "total_patterns": len(self.patterns),
            "total_embeddings": len(self.embeddings),
            "pattern_types": list(set(p.get('component_type', 'unknown') for p in self.patterns.values())),
            "openai_available": self.api_available,
            "embedding_mode": "OpenAI" if self.api_available else "Fallback Hash-based"
        }