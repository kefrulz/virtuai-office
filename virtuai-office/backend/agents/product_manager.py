import asyncio
import logging
from typing import List
from ..models.database import Task, AgentType
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class AliceChenAgent(BaseAgent):
    """Alice Chen - Senior Product Manager Agent"""
    
    def __init__(self):
        super().__init__(
            name="Alice Chen",
            agent_type=AgentType.PRODUCT_MANAGER,
            description="Senior Product Manager with expertise in user stories, requirements, and project planning",
            expertise=[
                "user stories", "acceptance criteria", "requirements gathering",
                "product roadmap", "feature specifications", "stakeholder analysis",
                "user personas", "user journey mapping", "product strategy",
                "market research", "competitive analysis", "mvp planning",
                "agile methodology", "scrum", "kanban", "sprint planning",
                "backlog management", "prioritization", "story points",
                "wireframing", "mockups", "user experience", "product metrics",
                "kpi tracking", "a/b testing", "user feedback", "analytics",
                "business requirements", "functional requirements", "epic writing",
                "feature documentation", "project management", "stakeholder communication"
            ]
        )
    
    def get_system_prompt(self) -> str:
        return """You are Alice Chen, a Senior Product Manager with 8+ years of experience in tech companies, specializing in product strategy, user experience, and agile development.

Your expertise includes:
- Writing clear, actionable user stories in proper format with acceptance criteria
- Creating detailed product requirements documents (PRDs) and feature specifications
- Developing product roadmaps and strategic planning
- Stakeholder analysis and communication across technical and business teams
- User research, persona development, and journey mapping
- Agile/Scrum methodology, sprint planning, and backlog management
- Competitive analysis and market research
- Product metrics, KPI tracking, and data-driven decision making
- MVP planning and feature prioritization techniques
- Cross-functional team coordination and project management

When writing user stories, you always use this format:
"As a [user type], I want [goal] so that [benefit]"

Your deliverables always include:
1. **Clear Acceptance Criteria** - Specific, testable conditions for story completion
2. **Story Points Estimation** - Using Fibonacci sequence (1, 2, 3, 5, 8, 13, 21)
3. **Dependencies Analysis** - What needs to be completed first
4. **Success Metrics** - How to measure if the feature achieves its goals
5. **Priority Classification** - Must-have, Should-have, Could-have, Won't-have (MoSCoW)

You write with:
- Business-focused language that both technical and non-technical stakeholders understand
- Clear structure with proper headings and bullet points
- Actionable insights and specific recommendations
- Data-driven rationale for decisions and priorities
- Risk assessment and mitigation strategies
- Timeline estimates and resource considerations

Always consider:
- User needs and pain points
- Business value and ROI
- Technical feasibility and constraints
- Market competition and opportunities
- Scalability and future growth
- Compliance and regulatory requirements"""

    async def process_task(self, task: Task) -> str:
        """Generate product management artifacts based on task requirements"""
        
        prompt = f"""{self.get_system_prompt()}

Task: {task.title}
Description: {task.description}
Priority: {task.priority.value}

Please analyze this request and provide a comprehensive product management response including:

1. **Executive Summary** - Brief overview of the request and recommended approach
2. **User Stories** - Write 3-5 detailed user stories related to this task using proper format
3. **Acceptance Criteria** - Define clear, testable criteria for each user story
4. **Requirements Analysis** - List functional and non-functional requirements
5. **Success Metrics** - Define KPIs and measurable outcomes
6. **Dependencies & Risks** - Identify what needs to be in place first and potential blockers
7. **Timeline Estimation** - Story points and rough time estimates
8. **Priority Recommendation** - MoSCoW prioritization with rationale
9. **Stakeholder Impact** - Who is affected and how to communicate changes
10. **Next Steps** - Actionable recommendations for moving forward

Format your response with clear headings and bullet points.
Use professional product management language.
Focus on user value, business impact, and actionable deliverables.
Consider both immediate needs and long-term product strategy."""

        try:
            response = await self._call_ollama(prompt)
            return self._enhance_pm_response(response, task)
        except Exception as e:
            logger.error(f"Alice Chen task processing failed: {e}")
            return self._generate_fallback_response(task, str(e))
    
    def _enhance_pm_response(self, response: str, task: Task) -> str:
        """Enhance the response with additional product management insights"""
        
        enhancement = f"""
# 👩‍💼 Alice Chen's Product Analysis

## Task Overview
**Title:** {task.title}
**Priority:** {task.priority.value.upper()}
**Complexity:** {self._assess_complexity(task.description)}
**Business Impact:** {self._assess_business_impact(task.description)}

## Analysis & Recommendations
{response}

## 📊 Additional Product Considerations

### User Experience Impact
- Consider user workflow disruption during implementation
- Plan for user onboarding and change management
- Gather user feedback through surveys or interviews
- Monitor user adoption metrics after launch
- Plan for iterative improvements based on usage data

### Business Strategy Alignment
- Evaluate alignment with company OKRs and strategic goals
- Assess competitive advantage and market differentiation
- Consider revenue impact and business model implications
- Analyze customer acquisition and retention effects
- Review compliance and regulatory requirements

### Technical & Operational Considerations
- Coordinate with engineering for technical feasibility assessment
- Plan for infrastructure and scalability requirements
- Consider data privacy and security implications
- Assess integration requirements with existing systems
- Plan for maintenance and operational overhead

### Go-to-Market Strategy
- Develop communication plan for internal stakeholders
- Create user documentation and training materials
- Plan phased rollout or feature flagging approach
- Prepare customer support team for new functionality
- Coordinate with marketing for feature announcement

### Risk Mitigation
- Identify potential user confusion or adoption barriers
- Plan rollback strategy in case of issues
- Monitor key metrics for early warning signs
- Prepare contingency plans for technical difficulties
- Set up feedback channels for rapid issue identification

### Success Measurement Framework
- Define baseline metrics before implementation
- Set up tracking and analytics for key user actions
- Plan regular review cadence for performance assessment
- Establish success criteria and failure thresholds
- Create dashboard for ongoing monitoring

## 🎯 Action Items for Development Team

### Immediate Actions (This Sprint)
- [ ] Review and validate user stories with stakeholders
- [ ] Confirm technical approach with engineering team
- [ ] Set up tracking for success metrics
- [ ] Create detailed wireframes or mockups if needed
- [ ] Validate assumptions with user research if required

### Next Sprint Preparation
- [ ] Break down epics into implementable stories
- [ ] Estimate story points with development team
- [ ] Prioritize backlog items based on user value
- [ ] Prepare acceptance criteria for testing
- [ ] Plan integration and deployment approach

### Ongoing Monitoring
- [ ] Weekly check-ins on progress and blockers
- [ ] User feedback collection and analysis
- [ ] Metric tracking and performance review
- [ ] Stakeholder communication and updates
- [ ] Iterative improvement planning

**Generated by Alice Chen - Senior Product Manager**
*Focused on user value, business impact, and strategic execution*
"""
        
        return enhancement
    
    def _assess_complexity(self, description: str) -> str:
        """Assess the complexity of the product management task"""
        description_lower = description.lower()
        
        # High complexity indicators for PM work
        high_complexity_keywords = [
            "strategic", "roadmap", "multiple stakeholders", "cross-functional",
            "market analysis", "competitive research", "user research",
            "complex workflow", "integration", "enterprise", "compliance"
        ]
        
        # Medium complexity indicators
        medium_complexity_keywords = [
            "feature", "user story", "requirements", "planning", "analysis",
            "stakeholder", "documentation", "process", "workflow", "testing"
        ]
        
        high_score = sum(1 for keyword in high_complexity_keywords if keyword in description_lower)
        medium_score = sum(1 for keyword in medium_complexity_keywords if keyword in description_lower)
        word_count = len(description.split())
        
        if high_score >= 2 or word_count > 100:
            return "High - Strategic initiative requiring extensive stakeholder coordination"
        elif medium_score >= 2 or word_count > 50:
            return "Medium - Feature development with clear user impact"
        else:
            return "Low - Simple feature or documentation task"
    
    def _assess_business_impact(self, description: str) -> str:
        """Assess the potential business impact of the task"""
        description_lower = description.lower()
        
        high_impact_keywords = [
            "revenue", "conversion", "retention", "acquisition", "growth",
            "competitive", "market", "strategic", "customer satisfaction"
        ]
        
        medium_impact_keywords = [
            "efficiency", "user experience", "workflow", "automation",
            "improvement", "optimization", "feature", "functionality"
        ]
        
        high_score = sum(1 for keyword in high_impact_keywords if keyword in description_lower)
        medium_score = sum(1 for keyword in medium_impact_keywords if keyword in description_lower)
        
        if high_score >= 2:
            return "High - Direct impact on key business metrics"
        elif medium_score >= 2 or high_score >= 1:
            return "Medium - Improves user experience and operational efficiency"
        else:
            return "Low - Incremental improvement or maintenance"
    
    def _generate_fallback_response(self, task: Task, error: str) -> str:
        """Generate a fallback response when AI processing fails"""
        return f"""# 👩‍💼 Alice Chen - Product Management Analysis

## Task: {task.title}

I encountered an issue processing this product management task: {error}

## Recommended Approach

Based on the task description: "{task.description}"

### Initial Analysis Framework:

1. **User Story Template**
   ```
   As a [user type],
   I want [specific functionality],
   So that [clear benefit/value].
   
   Acceptance Criteria:
   - [ ] Given [context], when [action], then [expected outcome]
   - [ ] The feature should [specific requirement]
   - [ ] Users should be able to [key functionality]
   ```

2. **Requirements Gathering Questions**
   - Who are the primary users affected by this change?
   - What problem are we trying to solve?
   - How will we measure success?
   - What are the technical constraints?
   - What's the business impact if we don't do this?
   - How does this align with our product strategy?

3. **Priority Assessment Framework**
   - **Must Have**: Critical for basic functionality
   - **Should Have**: Important for user satisfaction
   - **Could Have**: Nice to have if time permits
   - **Won't Have**: Out of scope for current iteration

### Next Steps:
1. Clarify specific user needs and pain points
2. Define success metrics and acceptance criteria
3. Identify stakeholders and communication plan
4. Estimate effort and timeline with development team
5. Create detailed requirements and user stories
6. Plan testing and validation approach

### Stakeholder Questions to Address:
- What's the business justification for this feature?
- How will users discover and adopt this functionality?
- What support or training will be needed?
- How does this fit into our product roadmap?
- What are the risks if we delay this work?

Please provide more specific context about user needs, business goals, or technical constraints to enable a more detailed analysis.

**Alice Chen - Senior Product Manager**
*Focused on translating user needs into actionable development plans*
"""
    
    def can_handle_task(self, task_description: str) -> float:
        """Calculate confidence score for handling this task"""
        description_lower = task_description.lower()
        
        # Product management specific keywords with weights
        pm_indicators = {
            'user story': 1.0, 'user stories': 1.0, 'requirements': 0.9,
            'product': 0.8, 'feature': 0.8, 'epic': 0.9, 'backlog': 0.9,
            'roadmap': 1.0, 'planning': 0.8, 'strategy': 0.9, 'stakeholder': 0.8,
            'business': 0.7, 'analysis': 0.7, 'specification': 0.8, 'scope': 0.8,
            'priority': 0.8, 'prioritize': 0.8, 'mvp': 0.9, 'acceptance criteria': 1.0,
            'user experience': 0.8, 'customer': 0.7, 'market': 0.7, 'competitive': 0.7,
            'personas': 0.9, 'journey': 0.8, 'workflow': 0.7, 'process': 0.6,
            'agile': 0.8, 'scrum': 0.8, 'sprint': 0.8, 'kanban': 0.7,
            'documentation': 0.6, 'wireframe': 0.7, 'mockup': 0.7, 'prototype': 0.7,
            'metrics': 0.8, 'kpi': 0.8, 'analytics': 0.7, 'testing': 0.6,
            'feedback': 0.7, 'research': 0.7, 'interview': 0.8, 'survey': 0.7
        }
        
        # Calculate base confidence
        total_weight = 0
        matched_weight = 0
        
        for keyword, weight in pm_indicators.items():
            total_weight += weight
            if keyword in description_lower:
                matched_weight += weight
        
        base_confidence = matched_weight / total_weight if total_weight > 0 else 0
        
        # Boost for PM-specific task types
        if any(phrase in description_lower for phrase in [
            'write user stories', 'create requirements', 'product planning',
            'feature specification', 'business analysis', 'stakeholder analysis',
            'product roadmap', 'user research', 'competitive analysis'
        ]):
            base_confidence += 0.2
        
        # Reduce confidence for technical implementation tasks
        if any(phrase in description_lower for phrase in [
            'code', 'implement', 'build', 'develop', 'programming',
            'css', 'html', 'javascript', 'python', 'react', 'api'
        ]):
            base_confidence *= 0.3
        
        return min(base_confidence, 1.0)
