# backend/agents/ui_designer.py
# Luna Design - UI/UX Designer Agent

import asyncio
import json
import re
from typing import Dict, List, Optional
import logging

from .base_agent import BaseAgent
from ..models.database import Task

logger = logging.getLogger(__name__)

class LunaDesignAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Luna Design",
            agent_type="ui_ux_designer",
            description="Senior UI/UX Designer with expertise in user-centered design, wireframing, and design systems",
            expertise=[
                "ui design", "ux design", "wireframing", "prototyping",
                "design systems", "accessibility", "user research", "figma",
                "responsive design", "user journey mapping", "information architecture",
                "color theory", "typography", "interaction design"
            ]
        )
        self.design_principles = [
            "user-centered design",
            "accessibility first",
            "mobile-first approach",
            "consistency and patterns",
            "clear visual hierarchy",
            "intuitive navigation"
        ]
    
    def get_system_prompt(self) -> str:
        return """You are Luna Design, a Senior UI/UX Designer with 5+ years of experience creating user-centered digital experiences.

Your expertise includes:
- User experience (UX) research and design
- User interface (UI) design and visual design
- Wireframing and prototyping
- Design systems and component libraries
- Accessibility and inclusive design (WCAG 2.1)
- Responsive and mobile-first design
- User journey mapping
- Information architecture
- Design handoff and specifications

Design Philosophy:
- Always prioritize user needs and accessibility
- Create inclusive designs that work for everyone
- Follow established design principles and patterns
- Ensure consistency across all design elements
- Design for multiple devices and screen sizes
- Consider performance and technical constraints

When creating designs:
- Always consider user needs and accessibility
- Follow design principles (contrast, hierarchy, consistency)
- Create scalable design systems
- Provide detailed specifications for developers
- Consider multiple device sizes and contexts
- Include interaction design details
- Think about edge cases and error states
- Ensure WCAG 2.1 compliance

Focus on creating designs that are both beautiful and functional, with clear specifications that developers can implement effectively."""

    async def process_task(self, task: Task) -> str:
        """Generate comprehensive design specifications and guidelines"""
        prompt = f"""{self.get_system_prompt()}

Task: {task.title}
Description: {task.description}
Priority: {task.priority.value if hasattr(task.priority, 'value') else task.priority}

Please provide a comprehensive design solution including:

1. **Design Brief & Analysis**
   - User needs assessment
   - Design goals and objectives
   - Success criteria
   - Design constraints and considerations

2. **Wireframes & Layout**
   - Detailed wireframe descriptions
   - Layout structure and grid system
   - Content organization and hierarchy
   - Navigation patterns and user flow

3. **Visual Design System**
   - Color palette with hex codes and usage guidelines
   - Typography scale and font specifications
   - Spacing and sizing specifications
   - Component design patterns

4. **Responsive Design Strategy**
   - Breakpoint specifications (mobile, tablet, desktop)
   - Responsive behavior descriptions
   - Mobile-first design considerations
   - Touch interaction guidelines

5. **Component Specifications**
   - Detailed component descriptions
   - State variations (default, hover, active, disabled)
   - Interactive behaviors and micro-interactions
   - Animation and transition specifications

6. **Accessibility Guidelines**
   - WCAG 2.1 compliance requirements
   - Color contrast specifications
   - Keyboard navigation requirements
   - Screen reader considerations
   - Focus management guidelines

7. **User Experience Considerations**
   - User journey mapping
   - Information architecture
   - Error handling and edge cases
   - Loading states and feedback

8. **Developer Handoff Specifications**
   - CSS specifications and measurements
   - Asset requirements and formats
   - Implementation guidelines
   - Browser compatibility notes

Use clear, descriptive language since you're providing text-based design specifications.
Include specific measurements, colors (hex codes), and technical details that developers need.
Be comprehensive but organized, using clear headings and bullet points for easy reference."""

        try:
            response = await self._call_ollama(prompt)
            
            # Enhance the response with additional design context
            enhanced_response = self._enhance_design_output(response, task)
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Luna Design task processing failed: {e}")
            return f"Design specification generation failed: {str(e)}"
    
    def _enhance_design_output(self, response: str, task: Task) -> str:
        """Enhance design output with additional context and formatting"""
        
        # Add design metadata
        metadata = f"""
# 🎨 Design Specification by Luna Design

**Project:** {task.title}
**Designer:** Luna Design
**Date:** {task.created_at.strftime('%Y-%m-%d') if task.created_at else 'N/A'}
**Priority:** {task.priority.value if hasattr(task.priority, 'value') else task.priority}

---

"""
        
        # Add design system quick reference
        design_system_ref = """

---

## 🎯 Quick Reference - Design System

### Color Palette
```css
/* Primary Colors */
--primary-blue: #2563eb;
--primary-blue-dark: #1d4ed8;
--primary-blue-light: #3b82f6;

/* Secondary Colors */
--secondary-purple: #7c3aed;
--secondary-green: #10b981;
--secondary-orange: #f59e0b;

/* Neutral Colors */
--gray-50: #f9fafb;
--gray-100: #f3f4f6;
--gray-200: #e5e7eb;
--gray-300: #d1d5db;
--gray-400: #9ca3af;
--gray-500: #6b7280;
--gray-600: #4b5563;
--gray-700: #374151;
--gray-800: #1f2937;
--gray-900: #111827;

/* Status Colors */
--success: #10b981;
--warning: #f59e0b;
--error: #ef4444;
--info: #3b82f6;
```

### Typography Scale
```css
/* Font Sizes */
--text-xs: 0.75rem;     /* 12px */
--text-sm: 0.875rem;    /* 14px */
--text-base: 1rem;      /* 16px */
--text-lg: 1.125rem;    /* 18px */
--text-xl: 1.25rem;     /* 20px */
--text-2xl: 1.5rem;     /* 24px */
--text-3xl: 1.875rem;   /* 30px */
--text-4xl: 2.25rem;    /* 36px */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Spacing System
```css
/* Spacing Scale (based on 0.25rem = 4px) */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

### Breakpoints
```css
/* Responsive Breakpoints */
--breakpoint-sm: 640px;   /* Small devices */
--breakpoint-md: 768px;   /* Medium devices */
--breakpoint-lg: 1024px;  /* Large devices */
--breakpoint-xl: 1280px;  /* Extra large devices */
--breakpoint-2xl: 1536px; /* 2X large devices */
```

### Component Patterns
- **Buttons:** Minimum 44px touch target, 8px padding, rounded corners
- **Form Elements:** Consistent spacing, clear labels, validation states
- **Cards:** Subtle shadows, consistent padding, rounded corners
- **Navigation:** Clear hierarchy, active states, breadcrumbs where needed

---

## 🔧 Implementation Guidelines

### CSS Framework Recommendations
- **Tailwind CSS** - Utility-first approach (recommended)
- **CSS Modules** - Component-scoped styles
- **Styled Components** - CSS-in-JS solution

### Asset Formats
- **Icons:** SVG format for scalability
- **Images:** WebP with JPEG fallback
- **Fonts:** WOFF2 with WOFF fallback

### Performance Considerations
- Optimize images for different screen densities
- Use CSS Grid and Flexbox for layouts
- Implement lazy loading for images
- Minimize CSS and JavaScript bundles

### Browser Support
- Modern browsers (Chrome, Firefox, Safari, Edge)
- iOS Safari 12+
- Chrome Mobile 80+
- Progressive enhancement for older browsers

---

## 📱 Responsive Design Checklist

### Mobile First (320px+)
- [ ] Touch-friendly interface (44px+ touch targets)
- [ ] Readable text without zooming
- [ ] Fast loading and smooth scrolling
- [ ] Thumb-friendly navigation

### Tablet (768px+)
- [ ] Optimal use of increased screen space
- [ ] Landscape and portrait orientations
- [ ] Touch and keyboard input support

### Desktop (1024px+)
- [ ] Mouse and keyboard interactions
- [ ] Hover states and tooltips
- [ ] Efficient use of screen real estate
- [ ] Keyboard navigation support

---

## ♿ Accessibility Requirements

### WCAG 2.1 Level AA Compliance
- [ ] Color contrast ratio 4.5:1 for normal text
- [ ] Color contrast ratio 3:1 for large text
- [ ] Focus indicators for all interactive elements
- [ ] Keyboard navigation for all functionality
- [ ] Screen reader compatibility
- [ ] Alternative text for images
- [ ] Proper heading hierarchy
- [ ] Form labels and error messages

### Testing Checklist
- [ ] Screen reader testing (NVDA, JAWS, VoiceOver)
- [ ] Keyboard-only navigation
- [ ] Color contrast validation
- [ ] Focus management verification
- [ ] Mobile accessibility testing

"""
        
        # Combine all parts
        full_response = metadata + response + design_system_ref
        
        return full_response
    
    def can_handle_task(self, task_description: str) -> float:
        """Return confidence score for handling design tasks"""
        description_lower = task_description.lower()
        
        # High confidence keywords
        high_confidence_keywords = [
            "design", "ui", "ux", "wireframe", "mockup", "prototype",
            "interface", "user experience", "user interface", "visual",
            "layout", "component", "style guide", "design system"
        ]
        
        # Medium confidence keywords
        medium_confidence_keywords = [
            "page", "screen", "view", "dashboard", "form", "button",
            "navigation", "menu", "modal", "responsive", "mobile"
        ]
        
        # Low confidence keywords (but still relevant)
        low_confidence_keywords = [
            "frontend", "react", "css", "html", "styling", "theme",
            "color", "font", "typography", "accessibility"
        ]
        
        score = 0.0
        word_count = len(description_lower.split())
        
        # Calculate confidence based on keyword matches
        for keyword in high_confidence_keywords:
            if keyword in description_lower:
                score += 0.3
        
        for keyword in medium_confidence_keywords:
            if keyword in description_lower:
                score += 0.2
        
        for keyword in low_confidence_keywords:
            if keyword in description_lower:
                score += 0.1
        
        # Boost score for design-specific requests
        if any(phrase in description_lower for phrase in [
            "create design", "design a", "ui for", "ux for",
            "wireframe for", "mockup of", "style guide", "design system"
        ]):
            score += 0.4
        
        # Reduce score if it's clearly code-focused
        if any(phrase in description_lower for phrase in [
            "implement", "code", "function", "api", "database",
            "backend", "server", "algorithm", "test"
        ]):
            score *= 0.7
        
        # Normalize score based on task complexity
        if word_count > 50:
            score += 0.1  # Complex tasks often benefit from design thinking
        
        return min(score, 1.0)
    
    async def collaborate_with_frontend(self, design_specs: str, frontend_requirements: str) -> str:
        """Collaborate with frontend developer on design implementation"""
        
        collaboration_prompt = f"""{self.get_system_prompt()}

You are collaborating with Marcus Dev (Frontend Developer) on implementing your design.

Your Original Design Specifications:
{design_specs}

Frontend Developer's Requirements/Questions:
{frontend_requirements}

Please provide:
1. **Design Clarifications** - Answer any questions about the design
2. **Implementation Guidelines** - Specific guidance for frontend development
3. **Component Specifications** - Detailed specs for React components
4. **Responsive Behavior** - How components should adapt across devices
5. **Interaction Details** - Hover states, animations, transitions
6. **Asset Requirements** - Icons, images, or other assets needed

Be specific about measurements, colors, spacing, and behavior to ensure accurate implementation."""

        try:
            response = await self._call_ollama(collaboration_prompt)
            return f"## 🤝 Design Collaboration Response\n\n{response}"
        except Exception as e:
            logger.error(f"Design collaboration failed: {e}")
            return f"Collaboration response failed: {str(e)}"
    
    def validate_design_implementation(self, implementation_description: str) -> Dict[str, any]:
        """Validate if implementation matches design specifications"""
        
        validation_results = {
            "overall_score": 0.0,
            "accessibility_score": 0.0,
            "responsive_score": 0.0,
            "design_consistency_score": 0.0,
            "recommendations": [],
            "accessibility_issues": [],
            "responsive_issues": []
        }
        
        description_lower = implementation_description.lower()
        
        # Check for accessibility considerations
        accessibility_indicators = [
            "aria", "alt text", "keyboard", "screen reader", "contrast",
            "focus", "accessibility", "wcag", "semantic"
        ]
        
        accessibility_count = sum(1 for indicator in accessibility_indicators
                                if indicator in description_lower)
        validation_results["accessibility_score"] = min(accessibility_count / 5, 1.0)
        
        # Check for responsive design
        responsive_indicators = [
            "responsive", "mobile", "tablet", "desktop", "breakpoint",
            "media query", "flexible", "adaptive"
        ]
        
        responsive_count = sum(1 for indicator in responsive_indicators
                             if indicator in description_lower)
        validation_results["responsive_score"] = min(responsive_count / 4, 1.0)
        
        # Check for design consistency
        design_indicators = [
            "consistent", "style guide", "design system", "component",
            "pattern", "color", "typography", "spacing"
        ]
        
        design_count = sum(1 for indicator in design_indicators
                         if indicator in description_lower)
        validation_results["design_consistency_score"] = min(design_count / 5, 1.0)
        
        # Calculate overall score
        validation_results["overall_score"] = (
            validation_results["accessibility_score"] * 0.4 +
            validation_results["responsive_score"] * 0.3 +
            validation_results["design_consistency_score"] * 0.3
        )
        
        # Generate recommendations
        if validation_results["accessibility_score"] < 0.7:
            validation_results["accessibility_issues"].append(
                "Consider adding more accessibility features (ARIA labels, keyboard navigation, screen reader support)"
            )
        
        if validation_results["responsive_score"] < 0.7:
            validation_results["responsive_issues"].append(
                "Ensure the design works well across all device sizes and orientations"
            )
        
        if validation_results["design_consistency_score"] < 0.7:
            validation_results["recommendations"].append(
                "Follow the established design system and maintain visual consistency"
            )
        
        return validation_results
    
    async def create_design_system(self, project_context: str) -> str:
        """Create a comprehensive design system for a project"""
        
        design_system_prompt = f"""{self.get_system_prompt()}

Project Context: {project_context}

Create a comprehensive design system that includes:

1. **Brand Guidelines**
   - Color palette (primary, secondary, neutral, status colors)
   - Typography system (font families, sizes, weights, line heights)
   - Logo usage and brand elements

2. **Component Library**
   - Buttons (primary, secondary, outline, sizes, states)
   - Form elements (inputs, textareas, selects, checkboxes, radios)
   - Navigation components (headers, sidebars, breadcrumbs, tabs)
   - Cards and containers
   - Modals and overlays
   - Alerts and notifications

3. **Layout System**
   - Grid system specifications
   - Spacing scale and rhythm
   - Container sizes and breakpoints
   - Layout patterns and templates

4. **Interaction Patterns**
   - Hover and focus states
   - Animation and transition guidelines
   - Loading states and feedback
   - Error handling patterns

5. **Accessibility Standards**
   - Color contrast requirements
   - Keyboard navigation patterns
   - Screen reader compatibility
   - Focus management guidelines

6. **Implementation Guidelines**
   - CSS custom properties (variables)
   - Naming conventions
   - File organization
   - Documentation standards

Provide specific values, measurements, and code examples where appropriate."""

        try:
            response = await self._call_ollama(design_system_prompt)
            return f"## 🎨 Design System Specification\n\n{response}"
        except Exception as e:
            logger.error(f"Design system creation failed: {e}")
            return f"Design system creation failed: {str(e)}"
