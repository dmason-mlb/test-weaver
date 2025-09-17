from typing import Dict, List, Any, Optional
import logging
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
try:
    from .agents import UIValidatorAgent, APIAnalyzerAgent, PatternDiscoveryAgent
    from .external_enrichment import ExternalTestEnrichment
except ImportError:
    # Fallback for direct execution
    try:
        from agents import UIValidatorAgent, APIAnalyzerAgent, PatternDiscoveryAgent
        from external_enrichment import ExternalTestEnrichment
    except ImportError:
        # Create stub classes for testing
        class UIValidatorAgent:
            def __init__(self, *args, **kwargs): pass
        class APIAnalyzerAgent:
            def __init__(self, *args, **kwargs): pass
        class PatternDiscoveryAgent:
            def __init__(self, *args, **kwargs): pass
        class ExternalTestEnrichment:
            def __init__(self, *args, **kwargs): pass

logger = logging.getLogger(__name__)

class TestGenerationCrew:
    """Multi-agent crew for intelligent test generation using CrewAI framework.

    Orchestrates multiple specialized agents to collaboratively generate
    comprehensive test suites for MLB's server-driven UI components.
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize the test generation crew.

        Args:
            config: Optional configuration for agents and crew behavior
        """
        self.config = config or {}
        self.agents = {}
        self.tasks = []
        self.crew = None
        self.results_history = []

        # Initialize specialized agents
        self._initialize_agents()

        # Initialize external enrichment service
        self._initialize_external_enrichment()

        # Create CrewAI crew
        self._create_crew()

    def _initialize_agents(self):
        """Initialize all specialized agents for the crew."""
        try:
            # UI Validation Agent
            self.agents['ui_validator'] = UIValidatorAgent(
                design_system_rules=self.config.get('design_rules')
            )

            # API Analysis Agent
            self.agents['api_analyzer'] = APIAnalyzerAgent(
                base_url=self.config.get('api_base_url'),
                auth_config=self.config.get('auth_config')
            )

            # Pattern Discovery Agent
            self.agents['pattern_discovery'] = PatternDiscoveryAgent(
                pattern_storage=self.config.get('pattern_storage'),
                similarity_threshold=self.config.get('similarity_threshold', 0.8)
            )

            # Test Coordinator Agent (CrewAI agent for orchestration)
            self.agents['coordinator'] = Agent(
                role="Test Generation Coordinator",
                goal="Coordinate test generation activities across multiple agents and ensure comprehensive coverage",
                backstory="Experienced test architect with expertise in coordinating complex testing workflows and ensuring quality deliverables.",
                verbose=self.config.get('verbose', False),
                allow_delegation=True,
                max_iter=3
            )

            # Test Synthesizer Agent (CrewAI agent for final assembly)
            self.agents['synthesizer'] = Agent(
                role="Test Suite Synthesizer",
                goal="Synthesize inputs from all agents into cohesive, executable test suites",
                backstory="Expert in test automation frameworks with deep knowledge of creating maintainable and comprehensive test suites.",
                verbose=self.config.get('verbose', False),
                allow_delegation=False,
                max_iter=2
            )

            # External Enrichment Agent (CrewAI agent for external patterns)
            self.agents['external_enricher'] = Agent(
                role="External Pattern Enrichment Specialist",
                goal="Enrich test generation with external best practices and industry-standard patterns",
                backstory="Expert in discovering and integrating external test patterns from industry sources to enhance test coverage and quality.",
                verbose=self.config.get('verbose', False),
                allow_delegation=False,
                max_iter=2
            )

            logger.info("Initialized all crew agents successfully")

        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise

    def _initialize_external_enrichment(self):
        """Initialize external enrichment service."""
        try:
            self.external_enrichment = ExternalTestEnrichment(
                timeout=self.config.get('external_timeout', 30),
                max_patterns_per_search=self.config.get('max_external_patterns', 20),
                quality_threshold=self.config.get('external_quality_threshold', 0.6)
            )
            logger.info("External enrichment service initialized successfully")

        except Exception as e:
            logger.warning(f"External enrichment service not available: {e}")
            self.external_enrichment = None

    def _create_crew(self):
        """Create the CrewAI crew with agents and process configuration."""
        try:
            # Get CrewAI agents only (exclude our custom agent classes)
            crew_agents = [
                self.agents['coordinator'],
                self.agents['external_enricher'],
                self.agents['synthesizer']
            ]

            self.crew = Crew(
                agents=crew_agents,
                tasks=[],  # Tasks will be added dynamically
                process=Process.sequential,
                verbose=self.config.get('verbose', False),
                memory=self.config.get('enable_memory', True),
                max_rpm=self.config.get('max_requests_per_minute', 10)
            )

            logger.info("Created CrewAI crew successfully")

        except Exception as e:
            logger.error(f"Error creating crew: {e}")
            raise

    def generate_tests(self, ui_schema: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate comprehensive tests for UI schema using multi-agent collaboration.

        Args:
            ui_schema: UI component schema definition
            context: Optional context (screen type, user flow, etc.)

        Returns:
            Comprehensive test generation results from all agents
        """
        if not ui_schema:
            raise ValueError("UI schema cannot be None or empty")

        generation_result = {
            'ui_schema': ui_schema,
            'context': context or {},
            'timestamp': self._get_timestamp(),
            'agent_results': {},
            'synthesized_tests': {},
            'collaboration_insights': {},
            'execution_summary': {}
        }

        try:
            # Phase 1: Individual agent analysis
            logger.info("Starting Phase 1: Individual agent analysis")
            generation_result['agent_results'] = self._execute_individual_analyses(ui_schema, context)

            # Phase 2: Agent collaboration and synthesis
            logger.info("Starting Phase 2: Agent collaboration and synthesis")
            generation_result['synthesized_tests'] = self._execute_collaborative_synthesis(
                ui_schema, context, generation_result['agent_results']
            )

            # Phase 3: Generate insights and recommendations
            logger.info("Starting Phase 3: Generate insights and recommendations")
            generation_result['collaboration_insights'] = self._generate_collaboration_insights(
                generation_result['agent_results']
            )

            # Phase 4: Execution summary
            generation_result['execution_summary'] = self._create_execution_summary(generation_result)

            # Store results for learning
            self.results_history.append(generation_result)

            logger.info(f"Test generation completed successfully for {len(ui_schema.get('components', []))} components")

        except Exception as e:
            generation_result['error'] = str(e)
            logger.error(f"Error during test generation: {e}")

        return generation_result

    def _execute_individual_analyses(self, ui_schema: Dict, context: Optional[Dict]) -> Dict[str, Any]:
        """Execute individual analysis by each specialized agent."""
        agent_results = {}

        try:
            components = ui_schema.get('components', [])

            # UI Validation Analysis
            logger.info("Running UI validation analysis")
            ui_results = []
            for component in components:
                try:
                    result = self.agents['ui_validator'].validate_component(component, context)
                    ui_results.append(result)
                except Exception as e:
                    logger.error(f"UI validation error for component {component.get('id', 'unknown')}: {e}")
                    ui_results.append({'error': str(e), 'component_id': component.get('id', 'unknown')})

            agent_results['ui_validation'] = {
                'component_results': ui_results,
                'summary': self._summarize_ui_results(ui_results)
            }

            # API Analysis
            logger.info("Running API analysis")
            api_results = []
            for component in components:
                if 'endpoint' in component or 'api_url' in component:
                    try:
                        endpoint = component.get('endpoint') or component.get('api_url')
                        result = self.agents['api_analyzer'].analyze_endpoint(endpoint, context)
                        api_results.append(result)
                    except Exception as e:
                        logger.error(f"API analysis error for component {component.get('id', 'unknown')}: {e}")
                        api_results.append({'error': str(e), 'component_id': component.get('id', 'unknown')})

            agent_results['api_analysis'] = {
                'endpoint_results': api_results,
                'summary': self._summarize_api_results(api_results)
            }

            # Pattern Discovery
            logger.info("Running pattern discovery")
            pattern_results = []
            for component in components:
                try:
                    patterns = self.agents['pattern_discovery'].discover_patterns(component, context)
                    pattern_results.append({
                        'component_id': component.get('id', 'unknown'),
                        'patterns': patterns
                    })
                except Exception as e:
                    logger.error(f"Pattern discovery error for component {component.get('id', 'unknown')}: {e}")
                    pattern_results.append({'error': str(e), 'component_id': component.get('id', 'unknown')})

            agent_results['pattern_discovery'] = {
                'component_patterns': pattern_results,
                'summary': self._summarize_pattern_results(pattern_results)
            }

            # External Pattern Enrichment
            logger.info("Running external pattern enrichment")
            external_results = []
            if self.external_enrichment:
                try:
                    # Batch discover external patterns for all components
                    external_patterns_batch = self.external_enrichment.batch_discover_patterns(
                        components=components,
                        max_workers=3
                    )

                    for component_id, patterns in external_patterns_batch.items():
                        external_results.append({
                            'component_id': component_id,
                            'external_patterns': patterns,
                            'pattern_count': len(patterns)
                        })

                except Exception as e:
                    logger.error(f"External enrichment error: {e}")
                    external_results.append({'error': str(e)})
            else:
                logger.info("External enrichment service not available")

            agent_results['external_enrichment'] = {
                'component_enrichments': external_results,
                'summary': self._summarize_external_results(external_results)
            }

        except Exception as e:
            logger.error(f"Error in individual analyses: {e}")
            agent_results['error'] = str(e)

        return agent_results

    def _execute_collaborative_synthesis(self, ui_schema: Dict, context: Optional[Dict], agent_results: Dict) -> Dict[str, Any]:
        """Execute collaborative synthesis using CrewAI framework."""
        synthesis_result = {}

        try:
            # Create synthesis tasks
            tasks = self._create_synthesis_tasks(ui_schema, context, agent_results)

            # Update crew with tasks
            self.crew.tasks = tasks

            # Execute crew collaboration
            logger.info("Executing CrewAI crew collaboration")
            crew_output = self.crew.kickoff()

            # Process crew output
            synthesis_result = self._process_crew_output(crew_output, agent_results)

        except Exception as e:
            logger.error(f"Error in collaborative synthesis: {e}")
            synthesis_result = self._fallback_synthesis(agent_results)

        return synthesis_result

    def _create_synthesis_tasks(self, ui_schema: Dict, context: Optional[Dict], agent_results: Dict) -> List[Task]:
        """Create CrewAI tasks for collaborative synthesis."""
        tasks = []

        try:
            # Task 1: Coordinate test generation strategy
            coordination_task = Task(
                description=f"""
                Coordinate test generation for UI schema with {len(ui_schema.get('components', []))} components.

                Analyze results from specialized agents:
                - UI Validation: {len(agent_results.get('ui_validation', {}).get('component_results', []))} components analyzed
                - API Analysis: {len(agent_results.get('api_analysis', {}).get('endpoint_results', []))} endpoints analyzed
                - Pattern Discovery: {len(agent_results.get('pattern_discovery', {}).get('component_patterns', []))} pattern sets discovered
                - External Enrichment: {len(agent_results.get('external_enrichment', {}).get('component_enrichments', []))} components enriched

                Create a comprehensive test strategy that leverages insights from all agents.
                Focus on MLB-specific requirements and cross-platform consistency.
                """,
                agent=self.agents['coordinator'],
                expected_output="Comprehensive test generation strategy with prioritized test areas and agent collaboration plan"
            )
            tasks.append(coordination_task)

            # Task 2: External Pattern Integration
            external_task = None
            if self.external_enrichment:
                external_task = Task(
                    description=f"""
                    Integrate external test patterns and best practices discovered from industry sources.

                    External enrichment results available:
                    - {len(agent_results.get('external_enrichment', {}).get('component_enrichments', []))} components have external patterns
                    - Quality threshold: {self.external_enrichment.quality_threshold}
                    - Supported contexts: mobile, web, api, performance, accessibility

                    Analyze external patterns for:
                    1. Industry best practices that can enhance test coverage
                    2. Advanced testing techniques not covered by internal patterns
                    3. Performance and accessibility patterns from external sources
                    4. Integration opportunities with internal test strategies

                    Prioritize high-quality external patterns that align with MLB testing requirements.
                    """,
                    agent=self.agents['external_enricher'],
                    expected_output="External pattern integration recommendations with quality scores and integration strategies",
                    context=[coordination_task]
                )
                tasks.append(external_task)

            # Task 3: Synthesize comprehensive test suite
            synthesis_task = Task(
                description=f"""
                Synthesize inputs from all agents into executable test suites.

                Agent inputs available:
                - UI validation results with accessibility and design compliance scores
                - API analysis with test patterns and security considerations
                - Pattern discovery with similarity matching and reusable test strategies
                - External enrichment with industry best practices and advanced testing patterns

                Generate:
                1. Happy path tests for all components
                2. Error handling and edge case tests
                3. Performance and accessibility tests
                4. MLB-specific domain tests
                5. Cross-platform consistency tests
                6. External pattern-enhanced tests for advanced coverage

                Ensure all tests are executable and follow MLB testing standards.
                Integrate external patterns where they enhance test quality and coverage.
                """,
                agent=self.agents['synthesizer'],
                expected_output="Complete test suite with executable test code, organized by test type and component, enhanced with external patterns",
                context=[coordination_task] + ([external_task] if external_task else [])
            )
            tasks.append(synthesis_task)

        except Exception as e:
            logger.error(f"Error creating synthesis tasks: {e}")

        return tasks

    def _process_crew_output(self, crew_output: Any, agent_results: Dict) -> Dict[str, Any]:
        """Process output from CrewAI crew execution."""
        synthesis_result = {
            'test_suites': {},
            'test_strategies': {},
            'collaboration_effectiveness': {},
            'recommendations': []
        }

        try:
            # Extract coordination strategy
            if hasattr(crew_output, 'tasks_output') and len(crew_output.tasks_output) > 0:
                coordination_output = crew_output.tasks_output[0]
                synthesis_result['test_strategies']['coordination'] = str(coordination_output)

            # Extract synthesis results
            if hasattr(crew_output, 'tasks_output') and len(crew_output.tasks_output) > 1:
                synthesis_output = crew_output.tasks_output[1]
                synthesis_result['test_suites']['synthesized'] = str(synthesis_output)

            # Evaluate collaboration effectiveness
            synthesis_result['collaboration_effectiveness'] = self._evaluate_collaboration(
                agent_results, synthesis_result
            )

        except Exception as e:
            logger.error(f"Error processing crew output: {e}")
            synthesis_result = self._fallback_synthesis(agent_results)

        return synthesis_result

    def _fallback_synthesis(self, agent_results: Dict) -> Dict[str, Any]:
        """Fallback synthesis when CrewAI execution fails."""
        logger.warning("Using fallback synthesis due to CrewAI execution failure")

        fallback_result = {
            'test_suites': {
                'ui_tests': self._extract_ui_tests(agent_results.get('ui_validation', {})),
                'api_tests': self._extract_api_tests(agent_results.get('api_analysis', {})),
                'pattern_tests': self._extract_pattern_tests(agent_results.get('pattern_discovery', {}))
            },
            'test_strategies': {
                'fallback_strategy': 'Individual agent results combined without CrewAI collaboration'
            },
            'recommendations': [
                'CrewAI collaboration failed - using individual agent outputs',
                'Consider checking CrewAI configuration and dependencies',
                'Results may be less comprehensive than full collaboration'
            ]
        }

        return fallback_result

    def _extract_ui_tests(self, ui_results: Dict) -> List[Dict]:
        """Extract test patterns from UI validation results."""
        tests = []

        component_results = ui_results.get('component_results', [])
        for result in component_results:
            if result.get('is_valid', True):  # Only valid components
                test = {
                    'test_type': 'ui_validation',
                    'component_id': result.get('component_id', 'unknown'),
                    'test_strategy': 'validate_ui_compliance',
                    'accessibility_score': result.get('accessibility_score', 0),
                    'design_score': result.get('design_compliance_score', 0)
                }
                tests.append(test)

        return tests

    def _extract_api_tests(self, api_results: Dict) -> List[Dict]:
        """Extract test patterns from API analysis results."""
        tests = []

        endpoint_results = api_results.get('endpoint_results', [])
        for result in endpoint_results:
            if result.get('analysis_status') == 'success':
                for pattern in result.get('test_patterns', []):
                    test = {
                        'test_type': 'api_validation',
                        'endpoint_url': result.get('endpoint_url', ''),
                        'test_name': pattern.get('name', ''),
                        'test_code': pattern.get('test_code', ''),
                        'pattern_type': pattern.get('type', 'unknown')
                    }
                    tests.append(test)

        return tests

    def _extract_pattern_tests(self, pattern_results: Dict) -> List[Dict]:
        """Extract test patterns from pattern discovery results."""
        tests = []

        component_patterns = pattern_results.get('component_patterns', [])
        for component_result in component_patterns:
            patterns = component_result.get('patterns', [])
            for pattern in patterns:
                test = {
                    'test_type': 'pattern_based',
                    'component_id': component_result.get('component_id', 'unknown'),
                    'pattern_type': pattern.get('pattern_type', 'unknown'),
                    'test_strategy': pattern.get('test_strategy', ''),
                    'similarity_score': pattern.get('similarity_score', 0)
                }
                tests.append(test)

        return tests

    def _summarize_ui_results(self, ui_results: List[Dict]) -> Dict:
        """Summarize UI validation results."""
        total = len(ui_results)
        valid = sum(1 for r in ui_results if r.get('is_valid', False))

        return {
            'total_components': total,
            'valid_components': valid,
            'validation_rate': valid / total if total > 0 else 0,
            'avg_accessibility_score': sum(r.get('accessibility_score', 0) for r in ui_results) / total if total > 0 else 0
        }

    def _summarize_api_results(self, api_results: List[Dict]) -> Dict:
        """Summarize API analysis results."""
        total = len(api_results)
        successful = sum(1 for r in api_results if r.get('analysis_status') == 'success')

        return {
            'total_endpoints': total,
            'successful_analyses': successful,
            'success_rate': successful / total if total > 0 else 0,
            'total_test_patterns': sum(len(r.get('test_patterns', [])) for r in api_results)
        }

    def _summarize_pattern_results(self, pattern_results: List[Dict]) -> Dict:
        """Summarize pattern discovery results."""
        total_patterns = sum(len(r.get('patterns', [])) for r in pattern_results)

        return {
            'components_analyzed': len(pattern_results),
            'total_patterns_discovered': total_patterns,
            'avg_patterns_per_component': total_patterns / len(pattern_results) if pattern_results else 0
        }

    def _generate_collaboration_insights(self, agent_results: Dict) -> Dict[str, Any]:
        """Generate insights from multi-agent collaboration."""
        insights = {
            'coverage_analysis': {},
            'quality_metrics': {},
            'improvement_opportunities': [],
            'agent_effectiveness': {}
        }

        try:
            # Coverage analysis
            ui_summary = agent_results.get('ui_validation', {}).get('summary', {})
            api_summary = agent_results.get('api_analysis', {}).get('summary', {})
            pattern_summary = agent_results.get('pattern_discovery', {}).get('summary', {})

            insights['coverage_analysis'] = {
                'ui_coverage': ui_summary.get('validation_rate', 0),
                'api_coverage': api_summary.get('success_rate', 0),
                'pattern_coverage': pattern_summary.get('avg_patterns_per_component', 0)
            }

            # Quality metrics
            insights['quality_metrics'] = {
                'avg_accessibility_score': ui_summary.get('avg_accessibility_score', 0),
                'total_test_patterns': api_summary.get('total_test_patterns', 0),
                'pattern_discovery_rate': pattern_summary.get('total_patterns_discovered', 0)
            }

            # Improvement opportunities
            if insights['coverage_analysis']['ui_coverage'] < 0.8:
                insights['improvement_opportunities'].append("UI validation coverage below 80% - review component definitions")

            if insights['coverage_analysis']['api_coverage'] < 0.9:
                insights['improvement_opportunities'].append("API analysis coverage below 90% - check endpoint configurations")

            if insights['quality_metrics']['avg_accessibility_score'] < 80:
                insights['improvement_opportunities'].append("Average accessibility score below 80 - improve component accessibility")

        except Exception as e:
            logger.error(f"Error generating collaboration insights: {e}")
            insights['error'] = str(e)

        return insights

    def _evaluate_collaboration(self, agent_results: Dict, synthesis_result: Dict) -> Dict[str, Any]:
        """Evaluate effectiveness of agent collaboration."""
        effectiveness = {
            'collaboration_score': 0.0,
            'synergy_indicators': [],
            'bottlenecks': [],
            'recommendations': []
        }

        try:
            # Calculate collaboration score based on multiple factors
            score = 0.0

            # Factor 1: All agents produced results
            agents_with_results = sum(1 for agent in ['ui_validation', 'api_analysis', 'pattern_discovery']
                                    if agent in agent_results and agent_results[agent])
            score += (agents_with_results / 3.0) * 30  # 30 points for agent participation

            # Factor 2: Synthesis success
            if 'test_suites' in synthesis_result and synthesis_result['test_suites']:
                score += 40  # 40 points for successful synthesis

            # Factor 3: Quality of insights
            if len(synthesis_result.get('recommendations', [])) > 0:
                score += 20  # 20 points for recommendations

            # Factor 4: Error handling
            error_count = sum(1 for result in agent_results.values() if 'error' in result)
            score += max(0, 10 - error_count * 2)  # Deduct points for errors

            effectiveness['collaboration_score'] = score

            # Identify synergy indicators
            if score > 80:
                effectiveness['synergy_indicators'].append("High agent collaboration effectiveness")
            if agents_with_results == 3:
                effectiveness['synergy_indicators'].append("All agents contributed successfully")

            # Identify bottlenecks
            if score < 60:
                effectiveness['bottlenecks'].append("Low overall collaboration score - check agent integration")
            if error_count > 1:
                effectiveness['bottlenecks'].append(f"Multiple agent errors detected ({error_count})")

        except Exception as e:
            logger.error(f"Error evaluating collaboration: {e}")
            effectiveness['error'] = str(e)

        return effectiveness

    def _create_execution_summary(self, generation_result: Dict) -> Dict[str, Any]:
        """Create execution summary for the test generation process."""
        summary = {
            'execution_time': self._get_timestamp(),
            'components_processed': 0,
            'tests_generated': 0,
            'agents_used': 0,
            'success_rate': 0.0,
            'key_achievements': [],
            'areas_for_improvement': []
        }

        try:
            # Count components processed
            ui_schema = generation_result.get('ui_schema', {})
            summary['components_processed'] = len(ui_schema.get('components', []))

            # Count tests generated
            synthesized_tests = generation_result.get('synthesized_tests', {})
            test_suites = synthesized_tests.get('test_suites', {})
            summary['tests_generated'] = sum(
                len(suite) if isinstance(suite, list) else 1
                for suite in test_suites.values()
            )

            # Count agents used
            agent_results = generation_result.get('agent_results', {})
            summary['agents_used'] = len([k for k in agent_results.keys() if not k.endswith('_error')])

            # Calculate success rate
            collaboration_insights = generation_result.get('collaboration_insights', {})
            if 'coverage_analysis' in collaboration_insights:
                coverage = collaboration_insights['coverage_analysis']
                avg_coverage = sum(coverage.values()) / len(coverage) if coverage else 0
                summary['success_rate'] = avg_coverage

            # Key achievements
            if summary['tests_generated'] > 0:
                summary['key_achievements'].append(f"Generated {summary['tests_generated']} test cases")
            if summary['agents_used'] == 3:
                summary['key_achievements'].append("All specialized agents contributed")
            if summary['success_rate'] > 0.8:
                summary['key_achievements'].append("High success rate achieved")

            # Areas for improvement
            if summary['success_rate'] < 0.7:
                summary['areas_for_improvement'].append("Success rate below 70% - review agent configurations")
            if summary['tests_generated'] < summary['components_processed']:
                summary['areas_for_improvement'].append("Some components did not generate tests")

        except Exception as e:
            logger.error(f"Error creating execution summary: {e}")
            summary['error'] = str(e)

        return summary

    def _get_timestamp(self) -> str:
        """Get current timestamp for logging."""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_crew_status(self) -> Dict[str, Any]:
        """Get current status of the crew and all agents.

        Returns:
            Status information for debugging and monitoring
        """
        status = {
            'crew_initialized': self.crew is not None,
            'agents_count': len(self.agents),
            'agents_status': {},
            'recent_results': len(self.results_history),
            'configuration': self.config
        }

        # Check individual agent status
        for agent_name, agent in self.agents.items():
            try:
                if hasattr(agent, 'agent'):  # CrewAI agents
                    status['agents_status'][agent_name] = {
                        'type': 'crewai_agent',
                        'role': getattr(agent.agent, 'role', 'unknown'),
                        'status': 'active'
                    }
                else:  # Custom agents
                    status['agents_status'][agent_name] = {
                        'type': 'custom_agent',
                        'class': agent.__class__.__name__,
                        'status': 'active'
                    }
            except Exception as e:
                status['agents_status'][agent_name] = {
                    'status': 'error',
                    'error': str(e)
                }

        return status

    def _summarize_external_results(self, external_results: List[Dict]) -> Dict[str, Any]:
        """Summarize external enrichment results."""
        total_external_patterns = 0
        successful_enrichments = 0

        for result in external_results:
            if 'external_patterns' in result:
                total_external_patterns += len(result['external_patterns'])
                successful_enrichments += 1

        return {
            'total_external_patterns': total_external_patterns,
            'components_enriched': successful_enrichments,
            'average_external_patterns_per_component': total_external_patterns / max(successful_enrichments, 1),
            'enrichment_service_available': self.external_enrichment is not None
        }

    def kickoff(self, ui_schema: Optional[Dict] = None, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Legacy method for compatibility - delegates to generate_tests.

        Args:
            ui_schema: Optional UI schema for test generation
            context: Optional context information

        Returns:
            Test generation results or crew status if no schema provided
        """
        if ui_schema:
            return self.generate_tests(ui_schema, context)
        else:
            # Return crew status for basic kickoff without parameters
            return self.get_crew_status()