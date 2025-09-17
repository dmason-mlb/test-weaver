from typing import Dict, List, Any, Optional, Tuple
import logging
import json
import hashlib
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class PatternDiscoveryAgent:
    """Agent responsible for discovering and evolving test patterns for MLB's server-driven UI.

    Capabilities:
    - Learn from successful test patterns
    - Identify similar UI components and reuse patterns
    - Evolve patterns based on test results and feedback
    - Create pattern similarity scoring
    - Build pattern knowledge base over time
    """

    def __init__(self, pattern_storage=None, similarity_threshold: float = 0.8, external_enrichment=None):
        """Initialize the Pattern Discovery Agent.

        Args:
            pattern_storage: Optional storage backend for patterns
            similarity_threshold: Threshold for pattern similarity matching
            external_enrichment: Optional external enrichment service for pattern discovery
        """
        self.pattern_storage = pattern_storage or self._initialize_storage()
        self.similarity_threshold = similarity_threshold
        self.pattern_cache = {}
        self.usage_stats = defaultdict(int)
        self.success_rates = defaultdict(list)
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)

        # External enrichment integration
        self.external_enrichment = external_enrichment
        self._initialize_external_enrichment()

        # Initialize CrewAI agent
        self.agent = Agent(
            role="Test Pattern Discovery Specialist",
            goal="Discover, evolve, and optimize test patterns for maximum coverage and effectiveness, enhanced with external industry best practices",
            backstory="Expert in machine learning and pattern recognition with deep understanding of test automation patterns, MLB's UI component ecosystem, and access to industry-wide testing knowledge.",
            verbose=True,
            allow_delegation=False
        )

    def _initialize_external_enrichment(self):
        """Initialize external enrichment service if not provided."""
        if self.external_enrichment is None:
            try:
                from ..external_enrichment import ExternalTestEnrichment
                self.external_enrichment = ExternalTestEnrichment()
                logger.info("External enrichment service initialized for PatternDiscoveryAgent")
            except Exception as e:
                logger.warning(f"External enrichment not available: {e}")
                self.external_enrichment = None

    def discover_patterns(self, component: Dict[str, Any], context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Discover relevant test patterns for a UI component.

        Args:
            component: UI component definition
            context: Optional context (screen type, user flow, etc.)

        Returns:
            List of discovered patterns with similarity scores
        """
        if not component or 'type' not in component:
            return []

        discovered_patterns = []

        try:
            # Extract component features for pattern matching
            component_features = self._extract_component_features(component, context)

            # Find similar patterns in knowledge base
            similar_patterns = self._find_similar_patterns(component_features)

            # Score and rank patterns
            scored_patterns = self._score_patterns(component_features, similar_patterns)

            # Filter by similarity threshold
            discovered_patterns = [
                pattern for pattern in scored_patterns
                if pattern.get('similarity_score', 0) >= self.similarity_threshold
            ]

            # Generate new patterns if no good matches found
            if len(discovered_patterns) < 2:
                generated_patterns = self._generate_new_patterns(component_features)
                discovered_patterns.extend(generated_patterns)

            # Enrich with external patterns if available
            if self.external_enrichment:
                try:
                    external_patterns = self._discover_external_patterns(component, context)
                    if external_patterns:
                        # Merge and deduplicate external patterns
                        enriched_patterns = self._merge_external_patterns(discovered_patterns, external_patterns)
                        discovered_patterns = enriched_patterns
                        logger.info(f"Enriched with {len(external_patterns)} external patterns")
                except Exception as e:
                    logger.warning(f"External pattern enrichment failed: {e}")

            # Update usage statistics
            self._update_usage_stats(component_features, discovered_patterns)

            logger.info(f"Discovered {len(discovered_patterns)} patterns (including external) for component {component.get('id', 'unknown')}")

        except Exception as e:
            logger.error(f"Error discovering patterns for component {component.get('id', 'unknown')}: {e}")

        return discovered_patterns

    def learn_from_test_results(self, component: Dict, patterns_used: List[Dict], test_results: Dict) -> None:
        """Learn from test execution results to improve pattern discovery.

        Args:
            component: Component that was tested
            patterns_used: Patterns that were used for testing
            test_results: Results from test execution
        """
        try:
            component_features = self._extract_component_features(component)
            success_rate = self._calculate_success_rate(test_results)

            # Update success rates for each pattern
            for pattern in patterns_used:
                pattern_id = pattern.get('pattern_id', self._generate_pattern_id(pattern))
                self.success_rates[pattern_id].append(success_rate)

                # Update pattern in storage with new success data
                self._update_pattern_success_rate(pattern_id, success_rate)

            # Learn new patterns from successful tests
            if success_rate > 0.8:  # High success rate
                self._extract_successful_patterns(component_features, patterns_used, test_results)

            # Mark failing patterns for review
            if success_rate < 0.5:  # Low success rate
                self._flag_failing_patterns(component_features, patterns_used, test_results)

            logger.info(f"Learned from test results for component {component.get('id', 'unknown')}: success_rate={success_rate:.2f}")

        except Exception as e:
            logger.error(f"Error learning from test results: {e}")

    def evolve_patterns(self, time_window_days: int = 30) -> Dict[str, Any]:
        """Evolve patterns based on recent usage and success data.

        Args:
            time_window_days: Number of days to look back for evolution analysis

        Returns:
            Evolution report with statistics and changes made
        """
        evolution_report = {
            'patterns_analyzed': 0,
            'patterns_evolved': 0,
            'patterns_deprecated': 0,
            'new_patterns_created': 0,
            'evolution_summary': {}
        }

        try:
            # Get patterns from recent time window
            cutoff_date = datetime.now() - timedelta(days=time_window_days)
            recent_patterns = self._get_patterns_since(cutoff_date)

            evolution_report['patterns_analyzed'] = len(recent_patterns)

            # Analyze usage patterns
            usage_analysis = self._analyze_usage_patterns(recent_patterns)

            # Evolve high-performing patterns
            evolved_patterns = self._evolve_high_performers(usage_analysis)
            evolution_report['patterns_evolved'] = len(evolved_patterns)

            # Deprecate low-performing patterns
            deprecated_patterns = self._deprecate_low_performers(usage_analysis)
            evolution_report['patterns_deprecated'] = len(deprecated_patterns)

            # Create new patterns from successful combinations
            new_patterns = self._create_composite_patterns(usage_analysis)
            evolution_report['new_patterns_created'] = len(new_patterns)

            # Update pattern storage
            self._persist_evolution_changes(evolved_patterns, deprecated_patterns, new_patterns)

            evolution_report['evolution_summary'] = {
                'top_performing_patterns': self._get_top_patterns(5),
                'trending_patterns': self._get_trending_patterns(5),
                'deprecated_reasons': self._get_deprecation_reasons(deprecated_patterns)
            }

            logger.info(f"Pattern evolution completed: {evolution_report['patterns_evolved']} evolved, {evolution_report['new_patterns_created']} created")

        except Exception as e:
            logger.error(f"Error during pattern evolution: {e}")
            evolution_report['error'] = str(e)

        return evolution_report

    def _extract_component_features(self, component: Dict, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Extract features from a component for pattern matching."""
        features = {
            'type': component.get('type', 'unknown'),
            'complexity_score': self._calculate_complexity_score(component),
            'interaction_types': self._extract_interaction_types(component),
            'has_auth': component.get('requires_auth', False),
            'has_api_calls': 'endpoint' in component or 'api_url' in component,
            'context_type': context.get('screen_type', 'unknown') if context else 'unknown',
            'feature_vector': self._create_feature_vector(component, context)
        }

        # Add MLB-specific features
        mlb_features = self._extract_mlb_features(component, context)
        features.update(mlb_features)

        return features

    def _calculate_complexity_score(self, component: Dict) -> float:
        """Calculate complexity score for a component."""
        score = 0.0

        # Base complexity by type
        type_complexity = {
            'button': 1.0, 'list': 3.0, 'form': 4.0, 'modal': 2.5,
            'webview': 3.5, 'api_endpoint': 2.0, 'card': 2.0,
            'navigation': 2.5, 'chart': 4.0, 'video': 3.0
        }
        score += type_complexity.get(component.get('type', 'unknown'), 2.0)

        # Additional complexity factors
        if component.get('requires_auth', False):
            score += 1.0

        if 'validation' in component:
            score += 0.5

        if 'nested_components' in component:
            score += len(component['nested_components']) * 0.3

        if 'interactions' in component:
            score += len(component['interactions']) * 0.2

        return min(score, 10.0)  # Cap at 10.0

    def _extract_interaction_types(self, component: Dict) -> List[str]:
        """Extract types of interactions supported by the component."""
        interactions = []

        # Direct interaction specification
        if 'interactions' in component:
            interactions.extend(component['interactions'])

        # Infer from component type
        component_type = component.get('type', '')
        type_interactions = {
            'button': ['click', 'tap'],
            'list': ['scroll', 'select', 'swipe'],
            'form': ['input', 'submit', 'validate'],
            'modal': ['dismiss', 'close'],
            'webview': ['load', 'navigate', 'scroll'],
            'navigation': ['navigate', 'select']
        }

        if component_type in type_interactions:
            interactions.extend(type_interactions[component_type])

        return list(set(interactions))  # Remove duplicates

    def _extract_mlb_features(self, component: Dict, context: Optional[Dict]) -> Dict[str, Any]:
        """Extract MLB-specific features from component."""
        mlb_features = {
            'is_team_related': False,
            'is_game_related': False,
            'is_stats_related': False,
            'requires_real_time': False,
            'mlb_entity_type': 'unknown'
        }

        # Check component properties for MLB entities
        component_text = json.dumps(component).lower()

        if any(term in component_text for term in ['team', 'roster', 'player']):
            mlb_features['is_team_related'] = True
            mlb_features['mlb_entity_type'] = 'team'

        if any(term in component_text for term in ['game', 'score', 'inning', 'pitch']):
            mlb_features['is_game_related'] = True
            mlb_features['requires_real_time'] = True
            mlb_features['mlb_entity_type'] = 'game'

        if any(term in component_text for term in ['stats', 'batting', 'era', 'average']):
            mlb_features['is_stats_related'] = True
            mlb_features['mlb_entity_type'] = 'stats'

        # Context-based features
        if context:
            screen_type = context.get('screen_type', '').lower()
            if screen_type in ['gameday', 'live_game']:
                mlb_features['requires_real_time'] = True

        return mlb_features

    def _create_feature_vector(self, component: Dict, context: Optional[Dict]) -> List[float]:
        """Create numerical feature vector for similarity calculations."""
        vector = []

        # Component type one-hot encoding
        component_types = ['button', 'list', 'form', 'modal', 'webview', 'api_endpoint', 'card', 'navigation', 'chart', 'video']
        component_type = component.get('type', 'unknown')
        type_vector = [1.0 if t == component_type else 0.0 for t in component_types]
        vector.extend(type_vector)

        # Numerical features
        vector.extend([
            float(component.get('requires_auth', False)),
            float('endpoint' in component),
            float('validation' in component),
            len(component.get('interactions', [])) / 10.0,  # Normalize
            self._calculate_complexity_score(component) / 10.0,  # Normalize
        ])

        # Context features
        if context:
            screen_types = ['gameday', 'team_page', 'browse_menu', 'scoreboard', 'unknown']
            screen_type = context.get('screen_type', 'unknown')
            screen_vector = [1.0 if s == screen_type else 0.0 for s in screen_types]
            vector.extend(screen_vector)
        else:
            vector.extend([0.0] * 5)  # Default context vector

        return vector

    def _find_similar_patterns(self, component_features: Dict) -> List[Dict]:
        """Find patterns similar to the given component features using Qdrant vector search."""
        similar_patterns = []

        try:
            if self.pattern_storage.get('type') == 'qdrant' and hasattr(self, 'vector_store'):
                # Use Qdrant vector search for efficient similarity matching
                similar_patterns = self._qdrant_similarity_search(component_features)
            else:
                # Fallback to in-memory similarity calculation
                similar_patterns = self._fallback_similarity_search(component_features)

        except Exception as e:
            logger.error(f"Error finding similar patterns: {e}")
            # Try fallback method
            try:
                similar_patterns = self._fallback_similarity_search(component_features)
            except Exception as fallback_error:
                logger.error(f"Fallback similarity search also failed: {fallback_error}")

        return similar_patterns

    def _qdrant_similarity_search(self, component_features: Dict) -> List[Dict]:
        """Use Qdrant for efficient vector similarity search."""
        similar_patterns = []

        try:
            # Create text representation for embedding
            feature_text = self._features_to_text(component_features)

            # Use vector store's similarity search
            search_results = self.vector_store.search_similar_patterns(
                feature_text,
                limit=20,  # Get top 20 similar patterns
                threshold=self.similarity_threshold
            )

            for result in search_results:
                pattern = result.get('pattern', {})
                pattern['similarity_score'] = result.get('similarity', 0.0)
                pattern['pattern_id'] = result.get('id', '')

                if pattern['similarity_score'] >= self.similarity_threshold:
                    similar_patterns.append(pattern)

            logger.info(f"Found {len(similar_patterns)} similar patterns using Qdrant")

        except Exception as e:
            logger.error(f"Error in Qdrant similarity search: {e}")
            raise

        return similar_patterns

    def _fallback_similarity_search(self, component_features: Dict) -> List[Dict]:
        """Fallback similarity search using in-memory calculations."""
        similar_patterns = []

        try:
            # Get all patterns from storage
            all_patterns = self._get_all_patterns()

            if not all_patterns:
                return []

            # Calculate similarities using feature vectors
            target_vector = np.array(component_features['feature_vector']).reshape(1, -1)

            for pattern in all_patterns:
                if 'feature_vector' in pattern:
                    pattern_vector = np.array(pattern['feature_vector']).reshape(1, -1)
                    similarity = cosine_similarity(target_vector, pattern_vector)[0][0]

                    if similarity >= self.similarity_threshold:
                        pattern_copy = pattern.copy()
                        pattern_copy['similarity_score'] = similarity
                        similar_patterns.append(pattern_copy)

            # Sort by similarity score
            similar_patterns.sort(key=lambda p: p.get('similarity_score', 0), reverse=True)

            logger.info(f"Found {len(similar_patterns)} similar patterns using fallback method")

        except Exception as e:
            logger.error(f"Error in fallback similarity search: {e}")
            raise

        return similar_patterns

    def _features_to_text(self, component_features: Dict) -> str:
        """Convert component features to text representation for embedding."""
        text_parts = []

        # Add component type
        text_parts.append(f"type:{component_features.get('type', 'unknown')}")

        # Add complexity
        complexity = component_features.get('complexity_score', 0)
        text_parts.append(f"complexity:{complexity:.1f}")

        # Add interactions
        interactions = component_features.get('interaction_types', [])
        if interactions:
            text_parts.append(f"interactions:{','.join(interactions)}")

        # Add auth requirement
        if component_features.get('has_auth', False):
            text_parts.append("requires_auth")

        # Add API calls
        if component_features.get('has_api_calls', False):
            text_parts.append("has_api")

        # Add context
        context_type = component_features.get('context_type', 'unknown')
        if context_type != 'unknown':
            text_parts.append(f"context:{context_type}")

        # Add MLB features
        mlb_entity = component_features.get('mlb_entity_type', 'unknown')
        if mlb_entity != 'unknown':
            text_parts.append(f"mlb_entity:{mlb_entity}")

        if component_features.get('requires_real_time', False):
            text_parts.append("real_time")

        return " ".join(text_parts)

    def _score_patterns(self, component_features: Dict, patterns: List[Dict]) -> List[Dict]:
        """Score patterns based on multiple criteria."""
        scored_patterns = []

        for pattern in patterns:
            try:
                # Base similarity score
                score = pattern.get('similarity_score', 0.0)

                # Boost score based on success rate
                pattern_id = pattern.get('pattern_id', '')
                if pattern_id in self.success_rates:
                    success_history = self.success_rates[pattern_id]
                    avg_success = sum(success_history) / len(success_history)
                    score *= (0.5 + 0.5 * avg_success)  # Boost successful patterns

                # Boost score based on usage frequency
                usage_count = self.usage_stats.get(pattern_id, 0)
                usage_boost = min(usage_count / 100.0, 0.3)  # Max 30% boost
                score += usage_boost

                # MLB-specific scoring
                mlb_score_boost = self._calculate_mlb_score_boost(component_features, pattern)
                score += mlb_score_boost

                pattern['final_score'] = score
                scored_patterns.append(pattern)

            except Exception as e:
                logger.error(f"Error scoring pattern {pattern.get('pattern_id', 'unknown')}: {e}")

        # Sort by final score
        scored_patterns.sort(key=lambda p: p.get('final_score', 0), reverse=True)

        return scored_patterns

    def _calculate_mlb_score_boost(self, component_features: Dict, pattern: Dict) -> float:
        """Calculate MLB-specific score boost for pattern matching."""
        boost = 0.0

        # Match MLB entity types
        if (component_features.get('mlb_entity_type') == pattern.get('mlb_entity_type', 'unknown')
            and component_features.get('mlb_entity_type') != 'unknown'):
            boost += 0.2

        # Real-time requirement matching
        if (component_features.get('requires_real_time', False) ==
            pattern.get('requires_real_time', False)):
            boost += 0.1

        # Auth requirement matching
        if (component_features.get('has_auth', False) ==
            pattern.get('has_auth', False)):
            boost += 0.1

        return boost

    def _generate_new_patterns(self, component_features: Dict) -> List[Dict]:
        """Generate new patterns when no good matches are found."""
        new_patterns = []

        try:
            # Create basic pattern based on component type
            base_pattern = self._create_base_pattern(component_features)
            new_patterns.append(base_pattern)

            # Create MLB-specific patterns if applicable
            if component_features.get('mlb_entity_type') != 'unknown':
                mlb_pattern = self._create_mlb_specific_pattern(component_features)
                new_patterns.append(mlb_pattern)

            # Create interaction-specific patterns
            for interaction in component_features.get('interaction_types', []):
                interaction_pattern = self._create_interaction_pattern(component_features, interaction)
                new_patterns.append(interaction_pattern)

            # Store new patterns for future use
            for pattern in new_patterns:
                self._store_pattern(pattern)

        except Exception as e:
            logger.error(f"Error generating new patterns: {e}")

        return new_patterns

    def _create_base_pattern(self, component_features: Dict) -> Dict:
        """Create a base test pattern for the component."""
        component_type = component_features.get('type', 'unknown')

        pattern = {
            'pattern_id': self._generate_pattern_id({'type': component_type, 'base': True}),
            'pattern_type': 'base',
            'component_type': component_type,
            'test_strategy': f'{component_type}_basic_testing',
            'test_steps': self._get_basic_test_steps(component_type),
            'expected_assertions': self._get_basic_assertions(component_type),
            'feature_vector': component_features.get('feature_vector', []),
            'created_date': datetime.now().isoformat(),
            'usage_count': 0,
            'success_rate': 0.0,
            'similarity_score': 1.0  # Perfect match for newly created pattern
        }

        return pattern

    def _create_mlb_specific_pattern(self, component_features: Dict) -> Dict:
        """Create MLB-specific test pattern."""
        entity_type = component_features.get('mlb_entity_type', 'unknown')

        pattern = {
            'pattern_id': self._generate_pattern_id({'mlb_entity': entity_type}),
            'pattern_type': 'mlb_specific',
            'mlb_entity_type': entity_type,
            'component_type': component_features.get('type', 'unknown'),
            'test_strategy': f'mlb_{entity_type}_validation',
            'test_steps': self._get_mlb_test_steps(entity_type),
            'expected_assertions': self._get_mlb_assertions(entity_type),
            'feature_vector': component_features.get('feature_vector', []),
            'requires_real_time': component_features.get('requires_real_time', False),
            'created_date': datetime.now().isoformat(),
            'usage_count': 0,
            'success_rate': 0.0,
            'similarity_score': 0.95
        }

        return pattern

    def _create_interaction_pattern(self, component_features: Dict, interaction: str) -> Dict:
        """Create interaction-specific test pattern."""
        pattern = {
            'pattern_id': self._generate_pattern_id({'interaction': interaction, 'type': component_features.get('type')}),
            'pattern_type': 'interaction',
            'interaction_type': interaction,
            'component_type': component_features.get('type', 'unknown'),
            'test_strategy': f'{interaction}_interaction_testing',
            'test_steps': self._get_interaction_test_steps(interaction),
            'expected_assertions': self._get_interaction_assertions(interaction),
            'feature_vector': component_features.get('feature_vector', []),
            'created_date': datetime.now().isoformat(),
            'usage_count': 0,
            'success_rate': 0.0,
            'similarity_score': 0.9
        }

        return pattern

    def _get_basic_test_steps(self, component_type: str) -> List[str]:
        """Get basic test steps for component type."""
        basic_steps = {
            'button': ['Verify button is visible', 'Click button', 'Verify expected action'],
            'list': ['Verify list loads', 'Check item count', 'Test scrolling', 'Verify item selection'],
            'form': ['Verify form fields', 'Fill valid data', 'Submit form', 'Verify submission'],
            'modal': ['Verify modal opens', 'Check content', 'Test close functionality'],
            'webview': ['Verify webview loads', 'Check URL', 'Test navigation'],
            'api_endpoint': ['Send request', 'Verify response status', 'Validate response data']
        }
        return basic_steps.get(component_type, ['Verify component exists', 'Test basic functionality'])

    def _get_basic_assertions(self, component_type: str) -> List[str]:
        """Get basic assertions for component type."""
        basic_assertions = {
            'button': ['Button is clickable', 'Action is triggered'],
            'list': ['List contains items', 'Items are accessible'],
            'form': ['Form accepts input', 'Validation works'],
            'modal': ['Modal is displayed', 'Modal can be dismissed'],
            'webview': ['Content is loaded', 'Navigation works'],
            'api_endpoint': ['Response is valid', 'Data format is correct']
        }
        return basic_assertions.get(component_type, ['Component is functional'])

    def _get_mlb_test_steps(self, entity_type: str) -> List[str]:
        """Get MLB-specific test steps."""
        mlb_steps = {
            'team': ['Verify team data structure', 'Check team ID format', 'Validate team stats'],
            'game': ['Verify game data structure', 'Check live score updates', 'Validate game status'],
            'stats': ['Verify stats calculation', 'Check historical data', 'Validate stat formats']
        }
        return mlb_steps.get(entity_type, ['Verify MLB data structure'])

    def _get_mlb_assertions(self, entity_type: str) -> List[str]:
        """Get MLB-specific assertions."""
        mlb_assertions = {
            'team': ['Team has valid ID', 'Team name is present', 'Division is correct'],
            'game': ['Game has valid gamePk', 'Teams are present', 'Date is valid'],
            'stats': ['Stats are numerical', 'Stats are within valid ranges']
        }
        return mlb_assertions.get(entity_type, ['MLB data is valid'])

    def _get_interaction_test_steps(self, interaction: str) -> List[str]:
        """Get test steps for specific interactions."""
        interaction_steps = {
            'click': ['Locate clickable element', 'Perform click action', 'Verify response'],
            'scroll': ['Identify scrollable area', 'Perform scroll action', 'Verify content change'],
            'input': ['Locate input field', 'Enter test data', 'Verify input acceptance'],
            'swipe': ['Identify swipe area', 'Perform swipe gesture', 'Verify gesture response']
        }
        return interaction_steps.get(interaction, [f'Test {interaction} interaction'])

    def _get_interaction_assertions(self, interaction: str) -> List[str]:
        """Get assertions for specific interactions."""
        interaction_assertions = {
            'click': ['Click is registered', 'Expected action occurs'],
            'scroll': ['Content scrolls', 'Scroll position changes'],
            'input': ['Input is accepted', 'Input is validated'],
            'swipe': ['Swipe is detected', 'Swipe action occurs']
        }
        return interaction_assertions.get(interaction, [f'{interaction} works correctly'])

    def _generate_pattern_id(self, pattern_data: Dict) -> str:
        """Generate unique ID for a pattern."""
        # Create hash from pattern data
        pattern_str = json.dumps(pattern_data, sort_keys=True)
        return hashlib.md5(pattern_str.encode()).hexdigest()[:12]

    def _calculate_success_rate(self, test_results: Dict) -> float:
        """Calculate success rate from test results."""
        if not test_results:
            return 0.0

        passed = test_results.get('passed', 0)
        failed = test_results.get('failed', 0)
        total = passed + failed

        if total == 0:
            return 0.0

        return passed / total

    def _update_usage_stats(self, component_features: Dict, patterns: List[Dict]) -> None:
        """Update usage statistics for patterns."""
        for pattern in patterns:
            pattern_id = pattern.get('pattern_id', '')
            if pattern_id:
                self.usage_stats[pattern_id] += 1

    def _update_pattern_success_rate(self, pattern_id: str, success_rate: float) -> None:
        """Update success rate for a pattern in storage."""
        # This would update the pattern in persistent storage
        pass

    def _extract_successful_patterns(self, component_features: Dict, patterns: List[Dict], test_results: Dict) -> None:
        """Extract patterns from successful tests for learning."""
        # Analyze what made the test successful and store those patterns
        pass

    def _flag_failing_patterns(self, component_features: Dict, patterns: List[Dict], test_results: Dict) -> None:
        """Flag patterns that led to test failures."""
        # Mark patterns for review or deprecation
        pass

    def _initialize_storage(self):
        """Initialize pattern storage system with Qdrant integration."""
        try:
            # Import vector store
            from ..vector_store import ServerDrivenUIVectorStore

            # Initialize Qdrant vector store for pattern storage
            self.vector_store = ServerDrivenUIVectorStore()

            # Create pattern collection if it doesn't exist
            self._ensure_pattern_collection()

            logger.info("Initialized pattern storage with Qdrant vector store")

            return {
                'type': 'qdrant',
                'vector_store': self.vector_store,
                'patterns': [],  # Cached patterns
                'usage_stats': {},
                'success_rates': {}
            }

        except Exception as e:
            logger.warning(f"Failed to initialize Qdrant storage, using fallback: {e}")
            return {
                'type': 'fallback',
                'patterns': [],
                'usage_stats': {},
                'success_rates': {}
            }

    def _ensure_pattern_collection(self):
        """Ensure pattern collection exists in Qdrant."""
        try:
            if hasattr(self, 'vector_store') and self.vector_store.client:
                # Collection creation is handled by ServerDrivenUIVectorStore
                logger.info("Pattern collection verified in Qdrant")
        except Exception as e:
            logger.error(f"Error ensuring pattern collection: {e}")

    def _get_all_patterns(self) -> List[Dict]:
        """Get all patterns from storage."""
        if self.pattern_storage.get('type') == 'qdrant':
            return self._load_patterns_from_qdrant()
        else:
            return self.pattern_storage.get('patterns', [])

    def _load_patterns_from_qdrant(self) -> List[Dict]:
        """Load patterns from Qdrant vector store."""
        patterns = []
        try:
            if hasattr(self, 'vector_store') and self.vector_store.client:
                # Search for all patterns with a dummy query
                dummy_embedding = [0.0] * self.vector_store.vector_size
                search_results = self.vector_store.client.search(
                    collection_name=self.vector_store.collection_name,
                    query_vector=dummy_embedding,
                    limit=1000,  # Get all patterns
                    with_payload=True
                )

                for result in search_results:
                    pattern = result.payload
                    pattern['pattern_id'] = str(result.id)
                    pattern['similarity_score'] = result.score
                    patterns.append(pattern)

                logger.info(f"Loaded {len(patterns)} patterns from Qdrant")
        except Exception as e:
            logger.error(f"Error loading patterns from Qdrant: {e}")
            # Fallback to cached patterns
            patterns = self.pattern_storage.get('patterns', [])

        return patterns

    def _store_pattern(self, pattern: Dict) -> None:
        """Store a new pattern in Qdrant or fallback storage."""
        try:
            if self.pattern_storage.get('type') == 'qdrant' and hasattr(self, 'vector_store'):
                # Store in Qdrant vector store
                pattern_id = self.vector_store.store_pattern(pattern)
                pattern['pattern_id'] = pattern_id
                logger.info(f"Stored pattern {pattern_id} in Qdrant")
            else:
                # Fallback to in-memory storage
                if 'patterns' not in self.pattern_storage:
                    self.pattern_storage['patterns'] = []
                self.pattern_storage['patterns'].append(pattern)
                logger.info("Stored pattern in fallback storage")

        except Exception as e:
            logger.error(f"Error storing pattern: {e}")
            # Always fallback to in-memory storage
            if 'patterns' not in self.pattern_storage:
                self.pattern_storage['patterns'] = []
            self.pattern_storage['patterns'].append(pattern)

    def _get_patterns_since(self, cutoff_date: datetime) -> List[Dict]:
        """Get patterns created or used since cutoff date."""
        # This would query storage for recent patterns
        return self._get_all_patterns()  # Simplified for now

    def _analyze_usage_patterns(self, patterns: List[Dict]) -> Dict:
        """Analyze usage patterns for evolution."""
        return {
            'high_performers': [],
            'low_performers': [],
            'trending': [],
            'stable': []
        }

    def _evolve_high_performers(self, usage_analysis: Dict) -> List[Dict]:
        """Evolve high-performing patterns."""
        return []

    def _deprecate_low_performers(self, usage_analysis: Dict) -> List[Dict]:
        """Deprecate low-performing patterns."""
        return []

    def _create_composite_patterns(self, usage_analysis: Dict) -> List[Dict]:
        """Create new patterns from successful combinations."""
        return []

    def _persist_evolution_changes(self, evolved: List[Dict], deprecated: List[Dict], new: List[Dict]) -> None:
        """Persist changes from pattern evolution."""
        pass

    def _get_top_patterns(self, count: int) -> List[Dict]:
        """Get top performing patterns."""
        return []

    def _get_trending_patterns(self, count: int) -> List[Dict]:
        """Get trending patterns."""
        return []

    def _get_deprecation_reasons(self, deprecated_patterns: List[Dict]) -> Dict:
        """Get reasons for pattern deprecation."""
        return {}

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pattern statistics.

        Returns:
            Dictionary with pattern usage, success rates, and insights
        """
        stats = {
            'total_patterns': len(self._get_all_patterns()),
            'usage_statistics': dict(self.usage_stats),
            'average_success_rates': {},
            'pattern_breakdown': {},
            'recommendations': []
        }

        # Calculate average success rates
        for pattern_id, success_history in self.success_rates.items():
            if success_history:
                stats['average_success_rates'][pattern_id] = sum(success_history) / len(success_history)

        # Pattern type breakdown
        all_patterns = self._get_all_patterns()
        pattern_types = Counter(p.get('pattern_type', 'unknown') for p in all_patterns)
        stats['pattern_breakdown'] = dict(pattern_types)

        # Generate recommendations
        if stats['total_patterns'] < 10:
            stats['recommendations'].append("Consider building more test patterns for better coverage")

        if len(stats['average_success_rates']) > 0:
            avg_success = sum(stats['average_success_rates'].values()) / len(stats['average_success_rates'])
            if avg_success < 0.7:
                stats['recommendations'].append("Overall pattern success rate is low - review and improve patterns")

        return stats

    def _discover_external_patterns(self, component: Dict[str, Any], context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Discover external patterns for a component using external enrichment service."""
        if not self.external_enrichment:
            return []

        try:
            # Use external enrichment to discover patterns
            external_patterns = self.external_enrichment.discover_patterns_for_component(
                component=component,
                ui_context=context
            )

            # Transform external patterns to internal format
            transformed_patterns = []
            for pattern in external_patterns:
                transformed_pattern = self._transform_external_pattern(pattern, component)
                if transformed_pattern:
                    transformed_patterns.append(transformed_pattern)

            return transformed_patterns

        except Exception as e:
            logger.error(f"Error discovering external patterns: {e}")
            return []

    def _transform_external_pattern(self, external_pattern: Dict[str, Any], component: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform external pattern to internal pattern format."""
        try:
            # Convert external pattern to internal discovery format
            internal_pattern = {
                'pattern_id': f"ext_{external_pattern.get('pattern_id', '')[:8]}",
                'pattern_type': 'external_enriched',
                'source': 'external',
                'title': external_pattern.get('title', ''),
                'description': external_pattern.get('description', ''),
                'confidence_score': external_pattern.get('confidence_score', 0.5),
                'similarity_score': external_pattern.get('confidence_score', 0.5),  # Use confidence as similarity
                'test_strategy': external_pattern.get('test_template', ''),
                'component_type': component.get('type', ''),
                'requirements': [],
                'expected_outcomes': [],
                'metadata': {
                    'external_source': external_pattern.get('source', 'linkup'),
                    'external_pattern_id': external_pattern.get('pattern_id', ''),
                    'framework': external_pattern.get('metadata', {}).get('framework', ''),
                    'language': external_pattern.get('metadata', {}).get('language', 'python'),
                    'tags': external_pattern.get('metadata', {}).get('tags', []),
                    'votes': external_pattern.get('metadata', {}).get('votes', 0),
                    'enrichment_timestamp': datetime.now().isoformat()
                }
            }

            # Add MLB-specific enhancements from external pattern
            if hasattr(external_pattern, 'mlb_enhancements'):
                internal_pattern['mlb_features'] = external_pattern.get('mlb_enhancements', {})

            # Add context-specific features
            if external_pattern.get('mobile_specific'):
                internal_pattern['mobile_testing'] = external_pattern['mobile_specific']

            if external_pattern.get('accessibility_specific'):
                internal_pattern['accessibility_features'] = external_pattern['accessibility_specific']

            if external_pattern.get('performance_specific'):
                internal_pattern['performance_features'] = external_pattern['performance_specific']

            return internal_pattern

        except Exception as e:
            logger.error(f"Error transforming external pattern: {e}")
            return None

    def _merge_external_patterns(self, internal_patterns: List[Dict[str, Any]], external_patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge internal and external patterns, avoiding duplicates and ranking by quality."""
        try:
            all_patterns = internal_patterns.copy()

            # Add external patterns that don't duplicate existing ones
            existing_types = set(p.get('pattern_type', '') for p in internal_patterns)
            existing_titles = set(p.get('title', '').lower() for p in internal_patterns)

            for ext_pattern in external_patterns:
                # Check for duplicates
                ext_title = ext_pattern.get('title', '').lower()
                if ext_title not in existing_titles:
                    # Boost score for high-quality external patterns
                    if ext_pattern.get('confidence_score', 0) > 0.7:
                        ext_pattern['similarity_score'] = min(ext_pattern.get('similarity_score', 0) + 0.1, 1.0)

                    all_patterns.append(ext_pattern)

            # Sort by similarity score (including boosted external patterns)
            all_patterns.sort(key=lambda p: p.get('similarity_score', 0), reverse=True)

            # Limit total patterns to prevent overwhelming
            max_patterns = 15
            if len(all_patterns) > max_patterns:
                all_patterns = all_patterns[:max_patterns]

            return all_patterns

        except Exception as e:
            logger.error(f"Error merging external patterns: {e}")
            return internal_patterns

    def search_external_patterns(self, query: str, context: str = 'general') -> List[Dict[str, Any]]:
        """Search for external patterns using a query string."""
        if not self.external_enrichment:
            return []

        try:
            external_patterns = self.external_enrichment.search_test_patterns(
                query=query,
                context=context
            )

            # Transform patterns for internal use
            transformed_patterns = []
            for pattern in external_patterns:
                # Create a dummy component for transformation
                dummy_component = {'type': context, 'id': 'search_result'}
                transformed_pattern = self._transform_external_pattern(pattern, dummy_component)
                if transformed_pattern:
                    transformed_patterns.append(transformed_pattern)

            return transformed_patterns

        except Exception as e:
            logger.error(f"Error searching external patterns: {e}")
            return []

    def get_trending_external_patterns(self, category: str = 'all') -> List[Dict[str, Any]]:
        """Get trending external patterns."""
        if not self.external_enrichment:
            return []

        try:
            trending_patterns = self.external_enrichment.get_trending_patterns(category=category)

            # Transform for internal use
            transformed_patterns = []
            for pattern in trending_patterns:
                dummy_component = {'type': 'trending', 'id': f'trending_{category}'}
                transformed_pattern = self._transform_external_pattern(pattern, dummy_component)
                if transformed_pattern:
                    transformed_patterns.append(transformed_pattern)

            return transformed_patterns

        except Exception as e:
            logger.error(f"Error getting trending external patterns: {e}")
            return []

    def enhance_pattern_with_external_knowledge(self, internal_pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance an internal pattern with external knowledge."""
        if not self.external_enrichment:
            return internal_pattern

        try:
            # Search for similar external patterns
            query = f"{internal_pattern.get('pattern_type', '')} {internal_pattern.get('title', '')}"
            external_patterns = self.search_external_patterns(query, context='general')

            if external_patterns:
                enhanced_pattern = internal_pattern.copy()

                # Add external insights
                enhanced_pattern['external_insights'] = {
                    'similar_patterns_count': len(external_patterns),
                    'enhancement_timestamp': datetime.now().isoformat(),
                    'top_external_pattern': external_patterns[0] if external_patterns else None
                }

                # Boost confidence if external validation exists
                if external_patterns:
                    external_confidence = external_patterns[0].get('confidence_score', 0)
                    if external_confidence > 0.7:
                        enhanced_pattern['confidence_score'] = min(
                            enhanced_pattern.get('confidence_score', 0.5) + 0.2,
                            1.0
                        )

                return enhanced_pattern

        except Exception as e:
            logger.error(f"Error enhancing pattern with external knowledge: {e}")

        return internal_pattern