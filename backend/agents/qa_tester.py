# VirtuAI Office - TestBot QA Agent
# Senior QA Engineer specializing in test planning, automation, and quality assurance

import asyncio
import re
from typing import Dict, List, Any
from datetime import datetime
from .base_agent import BaseAgent, AgentType


class TestBotQAAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="TestBot QA",
            agent_type=AgentType.QA_TESTER,
            description="Senior QA Engineer with 6+ years of experience in software quality assurance and test automation",
            expertise=[
                "test planning", "test automation", "manual testing", "pytest", "jest",
                "selenium", "api testing", "performance testing", "bug reporting",
                "quality assurance", "test case design", "regression testing",
                "load testing", "security testing", "test data management",
                "continuous integration", "test documentation"
            ]
        )
    
    def get_system_prompt(self) -> str:
        return """You are TestBot QA, a Senior QA Engineer with 6+ years of experience in software quality assurance.

Your expertise includes:
- Test planning and strategy development
- Test case design and execution (manual and automated)
- Automated testing frameworks (pytest, Jest, Selenium, Cypress)
- API testing and validation (Postman, automated REST testing)
- Performance testing and load testing (JMeter, Artillery)
- Security testing fundamentals
- Bug reporting and defect tracking
- Test data management and environment setup
- Continuous integration testing (CI/CD pipelines)
- Quality metrics and reporting

When creating test plans and procedures:
- Cover positive, negative, and edge cases comprehensively
- Include functional, integration, and regression tests
- Consider performance, security, and accessibility aspects
- Provide clear, reproducible test steps with expected results
- Include pass/fail criteria and acceptance thresholds
- Consider different environments (dev, staging, production)
- Think about test data requirements and setup procedures
- Include automation recommendations where appropriate
- Focus on risk-based testing prioritization

Your testing philosophy:
- Quality is everyone's responsibility, but QA ensures it's measured
- Prevention is better than detection
- Test early, test often, test everything that matters
- Automate repetitive tasks, focus human effort on exploration
- Clear communication of quality status to all stakeholders

Always provide practical, actionable testing solutions that improve software quality and reliability."""

    async def process_task(self, task) -> str:
        """Generate comprehensive testing strategies and procedures"""
        
        # Analyze task for testing requirements
        task_analysis = self._analyze_testing_requirements(task.description, task.title)
        
        # Build comprehensive testing prompt
        prompt = f"""{self.get_system_prompt()}

Task: {task.title}
Description: {task.description}
Priority: {task.priority}

Testing Analysis:
- Type: {task_analysis['type']}
- Complexity: {task_analysis['complexity']}
- Risk Level: {task_analysis['risk_level']}
- Testing Scope: {', '.join(task_analysis['scope'])}

Please provide a comprehensive testing solution including:

1. **Test Strategy Overview**
   - Testing approach and methodology
   - Scope and objectives
   - Risk assessment and mitigation
   - Resource requirements

2. **Test Plan**
   - Test scenarios and objectives
   - Entry and exit criteria
   - Test environment requirements
   - Test data requirements

3. **Manual Test Cases**
   - Detailed step-by-step test cases
   - Expected results and pass/fail criteria
   - Priority and risk classification
   - Traceability to requirements

4. **Automated Test Code**
   - Test automation framework recommendations
   - Sample automated test scripts (pytest/Jest)
   - Page objects or test utilities (if applicable)
   - CI/CD integration suggestions

5. **API Testing** (if applicable)
   - API endpoint testing scenarios
   - Request/response validation
   - Error handling verification
   - Performance and load testing

6. **Performance Testing** (if applicable)
   - Load testing scenarios and metrics
   - Performance acceptance criteria
   - Bottleneck identification strategies
   - Monitoring and alerting recommendations

7. **Security Testing** (if applicable)
   - Security test cases and scenarios
   - Vulnerability assessment approach
   - Authentication and authorization testing
   - Data protection verification

8. **Bug Report Template**
   - Standardized bug reporting format
   - Severity and priority classification
   - Reproduction steps template
   - Documentation requirements

9. **Quality Metrics**
   - Test coverage metrics
   - Defect density tracking
   - Test execution metrics
   - Quality gates and thresholds

10. **Regression Testing Strategy**
    - Regression test suite design
    - Automated regression execution
    - Risk-based regression selection
    - Continuous quality monitoring

Format your response with clear headings, actionable steps, and specific examples.
Include code blocks for test scripts with proper syntax highlighting.
Provide realistic timelines and resource estimates where appropriate."""

        return await self._call_ollama(prompt)

    def _analyze_testing_requirements(self, description: str, title: str) -> Dict[str, Any]:
        """Analyze task to determine testing requirements and approach"""
        
        description_lower = description.lower()
        title_lower = title.lower()
        combined_text = f"{title_lower} {description_lower}"
        
        # Determine testing type
        testing_type = self._determine_testing_type(combined_text)
        
        # Assess complexity
        complexity = self._assess_testing_complexity(combined_text)
        
        # Determine risk level
        risk_level = self._assess_risk_level(combined_text)
        
        # Identify testing scope
        scope = self._identify_testing_scope(combined_text)
        
        return {
            'type': testing_type,
            'complexity': complexity,
            'risk_level': risk_level,
            'scope': scope
        }
    
    def _determine_testing_type(self, text: str) -> str:
        """Determine the primary type of testing needed"""
        
        type_indicators = {
            'api': ['api', 'endpoint', 'rest', 'graphql', 'service', 'backend'],
            'ui': ['ui', 'interface', 'frontend', 'component', 'page', 'form'],
            'integration': ['integration', 'workflow', 'end-to-end', 'e2e', 'system'],
            'performance': ['performance', 'load', 'stress', 'scalability', 'speed'],
            'security': ['security', 'authentication', 'authorization', 'encryption'],
            'mobile': ['mobile', 'app', 'ios', 'android', 'responsive'],
            'database': ['database', 'sql', 'query', 'data', 'migration']
        }
        
        scores = {}
        for test_type, keywords in type_indicators.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[test_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'functional'
    
    def _assess_testing_complexity(self, text: str) -> str:
        """Assess the complexity level of testing required"""
        
        complexity_indicators = {
            'high': [
                'complex', 'advanced', 'enterprise', 'scalable', 'distributed',
                'microservices', 'integration', 'workflow', 'multi-step'
            ],
            'medium': [
                'moderate', 'standard', 'typical', 'normal', 'regular',
                'component', 'feature', 'functionality'
            ],
            'low': [
                'simple', 'basic', 'quick', 'minor', 'small', 'straightforward'
            ]
        }
        
        word_count = len(text.split())
        
        # Check for complexity keywords
        for level, keywords in complexity_indicators.items():
            if any(keyword in text for keyword in keywords):
                if level == 'high':
                    return 'high'
                elif level == 'low':
                    return 'low'
        
        # Fallback based on description length and content
        if word_count > 100 or 'system' in text or 'integration' in text:
            return 'high'
        elif word_count < 30:
            return 'low'
        else:
            return 'medium'
    
    def _assess_risk_level(self, text: str) -> str:
        """Assess the risk level associated with the feature/change"""
        
        high_risk_indicators = [
            'security', 'authentication', 'payment', 'financial', 'critical',
            'production', 'data', 'migration', 'database', 'user data'
        ]
        
        medium_risk_indicators = [
            'integration', 'api', 'workflow', 'business logic', 'validation'
        ]
        
        low_risk_indicators = [
            'ui', 'styling', 'display', 'cosmetic', 'minor', 'small'
        ]
        
        if any(indicator in text for indicator in high_risk_indicators):
            return 'high'
        elif any(indicator in text for indicator in medium_risk_indicators):
            return 'medium'
        elif any(indicator in text for indicator in low_risk_indicators):
            return 'low'
        else:
            return 'medium'  # Default to medium risk
    
    def _identify_testing_scope(self, text: str) -> List[str]:
        """Identify the scope of testing required"""
        
        scope_areas = {
            'functional': ['functionality', 'feature', 'business logic', 'requirements'],
            'ui': ['interface', 'ui', 'user interface', 'frontend', 'display'],
            'api': ['api', 'endpoint', 'service', 'backend', 'rest'],
            'integration': ['integration', 'workflow', 'end-to-end', 'system'],
            'performance': ['performance', 'load', 'speed', 'scalability', 'response time'],
            'security': ['security', 'authentication', 'authorization', 'encryption'],
            'usability': ['usability', 'user experience', 'ux', 'accessibility'],
            'compatibility': ['browser', 'device', 'mobile', 'responsive', 'cross-platform'],
            'data': ['data', 'database', 'validation', 'integrity', 'migration']
        }
        
        identified_scope = []
        
        for scope_area, keywords in scope_areas.items():
            if any(keyword in text for keyword in keywords):
                identified_scope.append(scope_area)
        
        # Always include functional testing
        if 'functional' not in identified_scope:
            identified_scope.append('functional')
        
        return identified_scope
    
    def can_handle_task(self, task_description: str) -> float:
        """Determine confidence level for handling this task"""
        
        description_lower = task_description.lower()
        
        # High confidence keywords
        high_confidence_keywords = [
            'test', 'testing', 'qa', 'quality', 'bug', 'defect', 'validation',
            'verification', 'automation', 'selenium', 'pytest', 'jest'
        ]
        
        # Medium confidence keywords
        medium_confidence_keywords = [
            'api', 'endpoint', 'component', 'feature', 'functionality',
            'integration', 'workflow', 'performance', 'security'
        ]
        
        # Testing-specific patterns
        testing_patterns = [
            r'test\s+(plan|case|suite|strategy)',
            r'(create|write|develop)\s+test',
            r'(automation|automated)\s+test',
            r'quality\s+assurance',
            r'(bug|defect)\s+(report|tracking)',
            r'(load|performance|stress)\s+test'
        ]
        
        confidence = 0.0
        
        # Check for high confidence keywords
        high_matches = sum(1 for keyword in high_confidence_keywords if keyword in description_lower)
        confidence += min(high_matches * 0.3, 0.6)
        
        # Check for medium confidence keywords
        medium_matches = sum(1 for keyword in medium_confidence_keywords if keyword in description_lower)
        confidence += min(medium_matches * 0.15, 0.3)
        
        # Check for testing-specific patterns
        pattern_matches = sum(1 for pattern in testing_patterns if re.search(pattern, description_lower))
        confidence += min(pattern_matches * 0.2, 0.4)
        
        # Bonus for explicit testing requests
        if any(phrase in description_lower for phrase in ['test plan', 'test case', 'qa', 'quality assurance']):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def get_specialization_tags(self) -> List[str]:
        """Return tags that identify this agent's specializations"""
        return [
            'testing', 'qa', 'quality-assurance', 'test-automation',
            'pytest', 'jest', 'selenium', 'api-testing', 'performance-testing',
            'security-testing', 'bug-reporting', 'test-planning'
        ]
    
    def get_collaboration_strength(self) -> Dict[str, float]:
        """Return collaboration effectiveness with other agent types"""
        return {
            'product_manager': 0.9,  # Work closely on acceptance criteria and requirements
            'frontend_developer': 0.8,  # Test UI components and user workflows
            'backend_developer': 0.8,  # Test APIs and backend functionality
            'ui_ux_designer': 0.7,  # Validate design implementation and usability
            'qa_tester': 1.0  # Perfect collaboration with other QA
        }
    
    def estimate_effort_hours(self, task_description: str, task_complexity: str = None) -> float:
        """Estimate effort required for testing tasks"""
        
        base_hours = {
            'low': 4,      # Simple test case writing
            'medium': 8,   # Comprehensive test plan
            'high': 16     # Full test strategy with automation
        }
        
        if task_complexity:
            effort = base_hours.get(task_complexity, 8)
        else:
            # Estimate based on task description
            description_lower = task_description.lower()
            
            if any(keyword in description_lower for keyword in ['automation', 'framework', 'strategy']):
                effort = 16
            elif any(keyword in description_lower for keyword in ['plan', 'comprehensive', 'full']):
                effort = 12
            elif any(keyword in description_lower for keyword in ['case', 'scenario', 'simple']):
                effort = 6
            else:
                effort = 8
        
        # Adjust based on scope
        scope_multipliers = {
            'api': 1.2,
            'integration': 1.5,
            'performance': 1.8,
            'security': 1.6,
            'automation': 2.0
        }
        
        description_lower = task_description.lower()
        for scope, multiplier in scope_multipliers.items():
            if scope in description_lower:
                effort *= multiplier
                break
        
        return min(effort, 40)  # Cap at 40 hours for single task
