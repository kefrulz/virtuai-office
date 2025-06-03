# VirtuAI Office - Intelligent Task Assignment System
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
import math

from sqlalchemy.orm import Session
from ..core.logging import get_logger, log_error_with_context
from ..models.database import Task, Agent, TaskStatus, TaskPriority, AgentType

logger = get_logger('virtuai.task_assignment')

# Task Analysis Data Classes
@dataclass
class TaskComplexity:
    level: str  # simple, medium, complex, epic
    score: float  # 0.0 to 1.0
    factors: Dict[str, float] = field(default_factory=dict)

@dataclass
class SkillRequirement:
    skill: str
    importance: float  # 0.0 to 1.0
    proficiency_needed: float  # 0.0 to 1.0

@dataclass
class TaskAnalysis:
    task_id: str
    complexity: TaskComplexity
    required_skills: List[SkillRequirement]
    keywords: List[str]
    domain: str  # web, mobile, data, documentation, general
    estimated_effort: float  # hours
    collaboration_needed: bool
    priority_weight: float
    urgency_factor: float
    confidence: float  # 0.0 to 1.0

@dataclass
class AgentCapability:
    agent_id: str
    agent_type: AgentType
    skills: Dict[str, float]  # skill -> proficiency (0.0 to 1.0)
    current_workload: float  # hours
    performance_score: float  # 0.0 to 2.0
    availability: float  # 0.0 to 1.0
    specialization_bonus: float  # 0.0 to 1.0

@dataclass
class AssignmentScore:
    agent_id: str
    total_score: float
    skill_match: float
    workload_factor: float
    performance_factor: float
    availability_factor: float
    specialization_bonus: float
    confidence: float
    reasoning: str

class TaskDomain(str, Enum):
    WEB_DEVELOPMENT = "web_development"
    MOBILE_DEVELOPMENT = "mobile_development"
    DATA_ANALYSIS = "data_analysis"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DESIGN = "design"
    ARCHITECTURE = "architecture"
    GENERAL = "general"

class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EPIC = "epic"

class IntelligentTaskAssignment:
    """Advanced task assignment system with ML-inspired algorithms"""
    
    def __init__(self):
        self.skill_keywords = self._load_skill_keywords()
        self.domain_keywords = self._load_domain_keywords()
        self.complexity_indicators = self._load_complexity_indicators()
        self.agent_profiles = {}
        self.performance_history = {}
        
    def _load_skill_keywords(self) -> Dict[str, List[str]]:
        """Load skill-related keywords for task analysis"""
        return {
            'react': ['react', 'jsx', 'component', 'hook', 'state', 'props', 'frontend', 'ui'],
            'python': ['python', 'django', 'flask', 'fastapi', 'backend', 'api', 'server'],
            'javascript': ['javascript', 'js', 'typescript', 'ts', 'node', 'npm', 'webpack'],
            'css': ['css', 'sass', 'scss', 'styling', 'responsive', 'layout', 'flexbox', 'grid'],
            'html': ['html', 'markup', 'semantic', 'accessibility', 'seo'],
            'database': ['database', 'sql', 'postgresql', 'mysql', 'mongodb', 'orm', 'query'],
            'testing': ['test', 'testing', 'unit', 'integration', 'e2e', 'jest', 'pytest', 'qa'],
            'design': ['design', 'ui', 'ux', 'wireframe', 'mockup', 'figma', 'prototype'],
            'documentation': ['documentation', 'docs', 'readme', 'guide', 'manual', 'wiki'],
            'api': ['api', 'rest', 'graphql', 'endpoint', 'json', 'http', 'request'],
            'authentication': ['auth', 'login', 'user', 'jwt', 'oauth', 'security', 'session'],
            'deployment': ['deploy', 'docker', 'kubernetes', 'aws', 'cloud', 'ci/cd'],
            'performance': ['performance', 'optimization', 'speed', 'cache', 'benchmark'],
            'mobile': ['mobile', 'ios', 'android', 'react-native', 'flutter', 'app'],
            'data': ['data', 'analytics', 'visualization', 'chart', 'graph', 'metrics'],
        }
    
    def _load_domain_keywords(self) -> Dict[TaskDomain, List[str]]:
        """Load domain-specific keywords"""
        return {
            TaskDomain.WEB_DEVELOPMENT: [
                'website', 'web', 'browser', 'http', 'html', 'css', 'javascript',
                'responsive', 'frontend', 'backend', 'fullstack'
            ],
            TaskDomain.MOBILE_DEVELOPMENT: [
                'mobile', 'app', 'ios', 'android', 'react-native', 'flutter',
                'smartphone', 'tablet', 'touch', 'gesture'
            ],
            TaskDomain.DATA_ANALYSIS: [
                'data', 'analytics', 'visualization', 'chart', 'graph', 'dashboard',
                'metrics', 'kpi', 'reporting', 'insights'
            ],
            TaskDomain.DOCUMENTATION: [
                'documentation', 'docs', 'guide', 'manual', 'readme', 'wiki',
                'tutorial', 'help', 'reference'
            ],
            TaskDomain.TESTING: [
                'test', 'testing', 'qa', 'quality', 'bug', 'validation',
                'verification', 'automation'
            ],
            TaskDomain.DESIGN: [
                'design', 'ui', 'ux', 'interface', 'wireframe', 'mockup',
                'prototype', 'visual', 'layout'
            ],
            TaskDomain.ARCHITECTURE: [
                'architecture', 'system', 'design', 'structure', 'scalability',
                'performance', 'infrastructure'
            ]
        }
    
    def _load_complexity_indicators(self) -> Dict[str, float]:
        """Load complexity indicators and their weights"""
        return {
            # High complexity indicators
            'system': 0.8, 'architecture': 0.9, 'complex': 0.9, 'advanced': 0.8,
            'integration': 0.7, 'scalable': 0.7, 'optimization': 0.6, 'performance': 0.6,
            'security': 0.7, 'enterprise': 0.8, 'microservices': 0.9, 'distributed': 0.9,
            
            # Medium complexity indicators
            'component': 0.4, 'feature': 0.5, 'functionality': 0.5, 'workflow': 0.6,
            'dashboard': 0.5, 'form': 0.3, 'page': 0.3, 'api': 0.4,
            
            # Low complexity indicators
            'simple': -0.5, 'basic': -0.4, 'quick': -0.3, 'small': -0.3,
            'minor': -0.4, 'fix': -0.2, 'update': -0.2, 'modify': -0.1,
            
            # Effort indicators
            'comprehensive': 0.6, 'detailed': 0.4, 'complete': 0.5, 'full': 0.4,
            'multiple': 0.3, 'several': 0.2, 'various': 0.2, 'all': 0.3,
        }
    
    async def analyze_task(self, task: Task) -> TaskAnalysis:
        """Comprehensive task analysis using NLP-inspired techniques"""
        try:
            # Combine title and description for analysis
            text = f"{task.title} {task.description}".lower()
            words = re.findall(r'\b\w+\b', text)
            
            # Analyze complexity
            complexity = self._analyze_complexity(text, words, len(task.description))
            
            # Extract required skills
            required_skills = self._extract_required_skills(text, words)
            
            # Determine domain
            domain = self._determine_domain(text, words)
            
            # Extract keywords
            keywords = self._extract_keywords(words)
            
            # Estimate effort
            estimated_effort = self._estimate_effort(complexity, required_skills, len(task.description))
            
            # Determine if collaboration is needed
            collaboration_needed = self._needs_collaboration(complexity, required_skills, domain)
            
            # Calculate priority and urgency factors
            priority_weight = self._get_priority_weight(task.priority)
            urgency_factor = self._calculate_urgency_factor(task.created_at, task.priority)
            
            # Calculate confidence in analysis
            confidence = self._calculate_analysis_confidence(text, required_skills, complexity)
            
            analysis = TaskAnalysis(
                task_id=task.id,
                complexity=complexity,
                required_skills=required_skills,
                keywords=keywords,
                domain=domain.value,
                estimated_effort=estimated_effort,
                collaboration_needed=collaboration_needed,
                priority_weight=priority_weight,
                urgency_factor=urgency_factor,
                confidence=confidence
            )
            
            logger.info(f"Task analysis completed for {task.id}: {complexity.level} complexity, {len(required_skills)} skills required")
            return analysis
            
        except Exception as e:
            log_error_with_context('virtuai.task_assignment', e, {'task_id': task.id})
            # Return basic analysis as fallback
            return self._create_fallback_analysis(task)
    
    def _analyze_complexity(self, text: str, words: List[str], description_length: int) -> TaskComplexity:
        """Analyze task complexity using multiple factors"""
        factors = {}
        
        # Length factor (longer descriptions tend to be more complex)
        length_score = min(description_length / 500, 1.0)  # Normalize to 0-1
        factors['length'] = length_score * 0.2
        
        # Keyword complexity scoring
        keyword_score = 0.0
        keyword_count = 0
        
        for word in words:
            if word in self.complexity_indicators:
                keyword_score += self.complexity_indicators[word]
                keyword_count += 1
        
        # Normalize keyword score
        if keyword_count > 0:
            keyword_score = keyword_score / keyword_count
            factors['keywords'] = max(-0.5, min(0.5, keyword_score)) + 0.5  # Normalize to 0-1
        else:
            factors['keywords'] = 0.5  # Default medium complexity
        
        # Technical term density
        technical_terms = [
            'api', 'database', 'authentication', 'optimization', 'architecture',
            'integration', 'scalability', 'performance', 'security', 'framework',
            'algorithm', 'data structure', 'concurrent', 'async', 'real-time'
        ]
        
        tech_term_count = sum(1 for word in words if word in technical_terms)
        tech_density = min(tech_term_count / len(words) * 20, 1.0)  # Scale up for better sensitivity
        factors['technical_density'] = tech_density
        
        # Multiple domain complexity (tasks spanning multiple areas)
        domain_matches = 0
        for domain_keywords in self.domain_keywords.values():
            if any(keyword in words for keyword in domain_keywords):
                domain_matches += 1
        
        multi_domain_factor = min(domain_matches / 3, 1.0)  # 3+ domains = high complexity
        factors['multi_domain'] = multi_domain_factor * 0.3
        
        # Calculate overall complexity score
        total_score = sum(factors.values()) / len(factors)
        
        # Determine complexity level
        if total_score < 0.3:
            level = ComplexityLevel.SIMPLE
        elif total_score < 0.6:
            level = ComplexityLevel.MEDIUM
        elif total_score < 0.8:
            level = ComplexityLevel.COMPLEX
        else:
            level = ComplexityLevel.EPIC
        
        return TaskComplexity(level=level.value, score=total_score, factors=factors)
    
    def _extract_required_skills(self, text: str, words: List[str]) -> List[SkillRequirement]:
        """Extract required skills from task description"""
        skill_scores = {}
        
        # Score each skill based on keyword matches
        for skill, keywords in self.skill_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches > 0:
                # Calculate importance based on frequency and position
                importance = min(matches / len(keywords), 1.0)
                
                # Boost importance for exact skill mentions
                if skill in text:
                    importance = min(importance * 1.5, 1.0)
                
                skill_scores[skill] = importance
        
        # Convert to SkillRequirement objects
        requirements = []
        for skill, importance in skill_scores.items():
            if importance > 0.1:  # Filter out very low scores
                # Estimate proficiency needed based on complexity indicators
                proficiency_needed = 0.5  # Default medium proficiency
                
                if any(word in text for word in ['advanced', 'expert', 'complex', 'sophisticated']):
                    proficiency_needed = 0.8
                elif any(word in text for word in ['basic', 'simple', 'beginner', 'intro']):
                    proficiency_needed = 0.3
                
                requirements.append(SkillRequirement(
                    skill=skill,
                    importance=importance,
                    proficiency_needed=proficiency_needed
                ))
        
        # Sort by importance
        requirements.sort(key=lambda x: x.importance, reverse=True)
        
        return requirements[:10]  # Limit to top 10 skills
    
    def _determine_domain(self, text: str, words: List[str]) -> TaskDomain:
        """Determine the primary domain of the task"""
        domain_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in words)
            if matches > 0:
                domain_scores[domain] = matches / len(keywords)
        
        if not domain_scores:
            return TaskDomain.GENERAL
        
        # Return domain with highest score
        best_domain = max(domain_scores.items(), key=lambda x: x[1])
        return best_domain[0]
    
    def _extract_keywords(self, words: List[str]) -> List[str]:
        """Extract relevant keywords from the task"""
        # Filter out common words and focus on technical terms
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        
        # Get all skill-related keywords
        all_skill_keywords = set()
        for keywords in self.skill_keywords.values():
            all_skill_keywords.update(keywords)
        
        relevant_words = []
        for word in words:
            if (word not in stop_words and
                len(word) > 2 and
                (word in all_skill_keywords or word in self.complexity_indicators)):
                relevant_words.append(word)
        
        # Remove duplicates and return top keywords
        unique_keywords = list(set(relevant_words))
        return unique_keywords[:15]
    
    def _estimate_effort(self, complexity: TaskComplexity, required_skills: List[SkillRequirement], description_length: int) -> float:
        """Estimate effort in hours based on various factors"""
        base_effort = {
            ComplexityLevel.SIMPLE.value: 1.0,
            ComplexityLevel.MEDIUM.value: 3.0,
            ComplexityLevel.COMPLEX.value: 8.0,
            ComplexityLevel.EPIC.value: 20.0
        }
        
        effort = base_effort.get(complexity.level, 3.0)
        
        # Adjust based on number of required skills
        skill_multiplier = 1.0 + (len(required_skills) * 0.1)
        effort *= skill_multiplier
        
        # Adjust based on description length (more detail = more work)
        length_multiplier = 1.0 + (description_length / 1000) * 0.5
        effort *= length_multiplier
        
        # Ensure reasonable bounds
        return max(0.5, min(effort, 40.0))
    
    def _needs_collaboration(self, complexity: TaskComplexity, required_skills: List[SkillRequirement], domain: TaskDomain) -> bool:
        """Determine if task needs multi-agent collaboration"""
        # High complexity tasks often need collaboration
        if complexity.score > 0.8:
            return True
        
        # Tasks requiring many diverse skills
        if len(required_skills) > 5:
            return True
        
        # Tasks spanning multiple skill domains
        skill_domains = set()
        domain_mapping = {
            'react': 'frontend', 'javascript': 'frontend', 'css': 'frontend', 'html': 'frontend',
            'python': 'backend', 'database': 'backend', 'api': 'backend',
            'design': 'design', 'testing': 'qa', 'documentation': 'pm'
        }
        
        for skill_req in required_skills:
            if skill_req.skill in domain_mapping:
                skill_domains.add(domain_mapping[skill_req.skill])
        
        return len(skill_domains) > 2
    
    def _get_priority_weight(self, priority: TaskPriority) -> float:
        """Convert priority to numerical weight"""
        weights = {
            TaskPriority.LOW: 0.5,
            TaskPriority.MEDIUM: 1.0,
            TaskPriority.HIGH: 1.5,
            TaskPriority.URGENT: 2.0
        }
        return weights.get(priority, 1.0)
    
    def _calculate_urgency_factor(self, created_at: datetime, priority: TaskPriority) -> float:
        """Calculate urgency factor based on age and priority"""
        age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600
        
        # Base urgency increases with age
        urgency = min(age_hours / 24, 1.0)  # Max urgency after 24 hours
        
        # Priority multiplier
        priority_multiplier = {
            TaskPriority.LOW: 0.5,
            TaskPriority.MEDIUM: 1.0,
            TaskPriority.HIGH: 1.5,
            TaskPriority.URGENT: 2.0
        }
        
        return urgency * priority_multiplier.get(priority, 1.0)
    
    def _calculate_analysis_confidence(self, text: str, required_skills: List[SkillRequirement], complexity: TaskComplexity) -> float:
        """Calculate confidence in the task analysis"""
        confidence_factors = []
        
        # Text length factor (more text = more confidence)
        length_confidence = min(len(text) / 200, 1.0)
        confidence_factors.append(length_confidence)
        
        # Skill clarity factor (clear skill requirements = higher confidence)
        if required_skills:
            avg_skill_importance = sum(skill.importance for skill in required_skills) / len(required_skills)
            confidence_factors.append(avg_skill_importance)
        else:
            confidence_factors.append(0.3)  # Low confidence if no clear skills
        
        # Complexity factors confidence
        complexity_factor_confidence = len(complexity.factors) / 5  # Normalize based on number of factors
        confidence_factors.append(min(complexity_factor_confidence, 1.0))
        
        return sum(confidence_factors) / len(confidence_factors)
    
    def _create_fallback_analysis(self, task: Task) -> TaskAnalysis:
        """Create basic analysis when detailed analysis fails"""
        return TaskAnalysis(
            task_id=task.id,
            complexity=TaskComplexity(level=ComplexityLevel.MEDIUM.value, score=0.5),
            required_skills=[SkillRequirement(skill="general", importance=0.5, proficiency_needed=0.5)],
            keywords=[],
            domain=TaskDomain.GENERAL.value,
            estimated_effort=3.0,
            collaboration_needed=False,
            priority_weight=self._get_priority_weight(task.priority),
            urgency_factor=self._calculate_urgency_factor(task.created_at, task.priority),
            confidence=0.3
        )
    
    async def get_agent_capabilities(self, agents: List[Agent], db: Session) -> List[AgentCapability]:
        """Analyze capabilities of available agents"""
        capabilities = []
        
        for agent in agents:
            if not agent.is_active:
                continue
            
            # Parse agent expertise
            try:
                expertise = json.loads(agent.expertise) if agent.expertise else []
            except:
                expertise = []
            
            # Convert expertise to skill proficiency mapping
            skills = {}
            for skill in expertise:
                # Map expertise to skill categories
                skill_lower = skill.lower()
                for category, keywords in self.skill_keywords.items():
                    if skill_lower in keywords or any(keyword in skill_lower for keyword in keywords):
                        skills[category] = skills.get(category, 0.0) + 0.8
            
            # Add agent type specific skills
            type_skills = self._get_agent_type_skills(agent.type)
            for skill, proficiency in type_skills.items():
                skills[skill] = max(skills.get(skill, 0.0), proficiency)
            
            # Calculate current workload
            current_workload = await self._calculate_agent_workload(agent.id, db)
            
            # Get performance score
            performance_score = self.performance_history.get(agent.id, 1.0)
            
            # Calculate availability (inverse of workload)
            max_workload = 40.0  # hours per week
            availability = max(0.0, 1.0 - (current_workload / max_workload))
            
            # Calculate specialization bonus
            specialization_bonus = self._calculate_specialization_bonus(agent.type, skills)
            
            capabilities.append(AgentCapability(
                agent_id=agent.id,
                agent_type=agent.type,
                skills=skills,
                current_workload=current_workload,
                performance_score=performance_score,
                availability=availability,
                specialization_bonus=specialization_bonus
            ))
        
        return capabilities
    
    def _get_agent_type_skills(self, agent_type: AgentType) -> Dict[str, float]:
        """Get default skills for each agent type"""
        type_skills = {
            AgentType.PRODUCT_MANAGER: {
                'documentation': 0.9,
                'api': 0.6,
                'testing': 0.7
            },
            AgentType.FRONTEND_DEVELOPER: {
                'react': 0.9,
                'javascript': 0.9,
                'css': 0.8,
                'html': 0.8,
                'design': 0.6
            },
            AgentType.BACKEND_DEVELOPER: {
                'python': 0.9,
                'database': 0.8,
                'api': 0.9,
                'authentication': 0.7,
                'deployment': 0.6
            },
            AgentType.UI_UX_DESIGNER: {
                'design': 0.9,
                'css': 0.7,
                'html': 0.6,
                'react': 0.5
            },
            AgentType.QA_TESTER: {
                'testing': 0.9,
                'python': 0.6,
                'javascript': 0.6,
                'api': 0.7
            }
        }
        
        return type_skills.get(agent_type, {})
    
    async def _calculate_agent_workload(self, agent_id: str, db: Session) -> float:
        """Calculate current workload for an agent"""
        active_tasks = db.query(Task).filter(
            Task.agent_id == agent_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        ).all()
        
        total_effort = sum(task.estimated_effort or 3.0 for task in active_tasks)
        return total_effort
    
    def _calculate_specialization_bonus(self, agent_type: AgentType, skills: Dict[str, float]) -> float:
        """Calculate bonus for agent specialization"""
        # Agents get bonus for having high proficiency in their primary skills
        primary_skills = {
            AgentType.PRODUCT_MANAGER: ['documentation'],
            AgentType.FRONTEND_DEVELOPER: ['react', 'javascript', 'css'],
            AgentType.BACKEND_DEVELOPER: ['python', 'database', 'api'],
            AgentType.UI_UX_DESIGNER: ['design'],
            AgentType.QA_TESTER: ['testing']
        }
        
        agent_primary_skills = primary_skills.get(agent_type, [])
        if not agent_primary_skills:
            return 0.0
        
        # Calculate average proficiency in primary skills
        primary_skill_scores = [skills.get(skill, 0.0) for skill in agent_primary_skills]
        if primary_skill_scores:
            avg_primary_proficiency = sum(primary_skill_scores) / len(primary_skill_scores)
            return min(avg_primary_proficiency * 0.3, 0.3)  # Max 30% bonus
        
        return 0.0
    
    async def score_agent_for_task(self, agent_capability: AgentCapability, task_analysis: TaskAnalysis) -> AssignmentScore:
        """Score how well an agent matches a task"""
        scores = {}
        
        # 1. Skill Match Score (40% weight)
        skill_match_score = self._calculate_skill_match(agent_capability.skills, task_analysis.required_skills)
        scores['skill_match'] = skill_match_score * 0.4
        
        # 2. Workload Factor (25% weight)
        workload_score = agent_capability.availability
        scores['workload_factor'] = workload_score * 0.25
        
        # 3. Performance Factor (20% weight)
        performance_score = min(agent_capability.performance_score / 2.0, 1.0)  # Normalize to 0-1
        scores['performance_factor'] = performance_score * 0.2
        
        # 4. Availability Factor (10% weight)
        availability_score = agent_capability.availability
        scores['availability_factor'] = availability_score * 0.1
        
        # 5. Specialization Bonus (5% weight)
        specialization_score = agent_capability.specialization_bonus
        scores['specialization_bonus'] = specialization_score * 0.05
        
        # Calculate total score
        total_score = sum(scores.values())
        
        # Apply urgency multiplier
        if task_analysis.urgency_factor > 1.0:
            total_score *= (1.0 + (task_analysis.urgency_factor - 1.0) * 0.1)
        
        # Apply priority multiplier
        total_score *= task_analysis.priority_weight
        
        # Generate reasoning
        reasoning = self._generate_assignment_reasoning(agent_capability, task_analysis, scores)
        
        return AssignmentScore(
            agent_id=agent_capability.agent_id,
            total_score=total_score,
            skill_match=scores['skill_match'],
            workload_factor=scores['workload_factor'],
            performance_factor=scores['performance_factor'],
            availability_factor=scores['availability_factor'],
            specialization_bonus=scores['specialization_bonus'],
            confidence=task_analysis.confidence,
            reasoning=reasoning
        )
    
    def _calculate_skill_match(self, agent_skills: Dict[str, float], required_skills: List[SkillRequirement]) -> float:
        """Calculate how well agent skills match task requirements"""
        if not required_skills:
            return 0.5  # Neutral score for tasks with no specific requirements
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for skill_req in required_skills:
            agent_proficiency = agent_skills.get(skill_req.skill, 0.0)
            
            # Calculate match score based on proficiency vs requirement
            if agent_proficiency >= skill_req.proficiency_needed:
                # Agent exceeds requirement - excellent match
                match_score = 1.0
            elif agent_proficiency > 0:
                # Agent has some proficiency - partial match
                match_score = agent_proficiency / skill_req.proficiency_needed
            else:
                # Agent has no proficiency - poor match
                match_score = 0.0
            
            # Weight by importance of the skill
            weighted_score = match_score * skill_req.importance
            total_weighted_score += weighted_score
            total_weight += skill_req.importance
        
        if total_weight == 0:
            return 0.5
        
        return total_weighted_score / total_weight
    
    def _generate_assignment_reasoning(self, agent_capability: AgentCapability, task_analysis: TaskAnalysis, scores: Dict[str, float]) -> str:
        """Generate human-readable reasoning for the assignment"""
        reasons = []
        
        # Skill match reasoning
        skill_score = scores['skill_match'] / 0.4  # Denormalize
        if skill_score > 0.8:
            reasons.append("Excellent skill match")
        elif skill_score > 0.6:
            reasons.append("Good skill match")
        elif skill_score > 0.4:
            reasons.append("Partial skill match")
        else:
            reasons.append("Limited skill match")
        
        # Workload reasoning
        if agent_capability.availability > 0.8:
            reasons.append("Low current workload")
        elif agent_capability.availability > 0.5:
            reasons.append("Moderate workload")
        else:
            reasons.append("High current workload")
        
        # Performance reasoning
        if agent_capability.performance_score > 1.5:
            reasons.append("Excellent performance history")
        elif agent_capability.performance_score > 1.
