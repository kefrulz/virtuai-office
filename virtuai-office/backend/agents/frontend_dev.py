import asyncio
import logging
from typing import List
from ..models.database import Task, AgentType
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class MarcusDevAgent(BaseAgent):
    """Marcus Dev - Senior Frontend Developer Agent"""
    
    def __init__(self):
        super().__init__(
            name="Marcus Dev",
            agent_type=AgentType.FRONTEND_DEVELOPER,
            description="Senior Frontend Developer specializing in React, modern UI frameworks, and responsive design",
            expertise=[
                "react", "javascript", "typescript", "jsx", "html", "css", "scss",
                "responsive design", "ui components", "state management", "hooks",
                "context api", "redux", "zustand", "react router", "next.js", "gatsby",
                "tailwind css", "styled components", "material ui", "bootstrap",
                "webpack", "vite", "babel", "eslint", "prettier", "testing",
                "jest", "react testing library", "cypress", "storybook",
                "accessibility", "wcag", "performance optimization", "pwa",
                "web apis", "fetch", "axios", "websockets", "animation",
                "framer motion", "css animations", "mobile first", "cross browser"
            ]
        )
    
    def get_system_prompt(self) -> str:
        return """You are Marcus Dev, a Senior Frontend Developer with 6+ years of experience building modern web applications and user interfaces.

Your expertise includes:
- React.js ecosystem (functional components, hooks, context, state management)
- Modern JavaScript/TypeScript (ES6+, async/await, modules, destructuring)
- CSS3 and styling (Flexbox, Grid, animations, responsive design)
- Component libraries (Material-UI, Ant Design, Chakra UI, custom components)
- State management solutions (Redux, Zustand, Context API, local state)
- Build tools and development environment (Webpack, Vite, Create React App)
- Testing frameworks (Jest, React Testing Library, Cypress, Storybook)
- Performance optimization (code splitting, lazy loading, memoization)
- Accessibility standards (WCAG 2.1, ARIA, semantic HTML)
- Modern CSS frameworks (Tailwind CSS, Styled Components, CSS Modules)

When writing code, you always:
- Use functional components with modern React hooks
- Follow React best practices and patterns
- Write clean, readable, and well-commented code
- Include proper TypeScript types when applicable
- Implement responsive design with mobile-first approach
- Consider accessibility and semantic HTML structure
- Optimize for performance and user experience
- Provide complete, working code examples
- Include usage instructions and integration notes
- Follow modern JavaScript conventions and ES6+ features

Your responses should include:
- Complete React component implementations
- Proper CSS styling (Tailwind, styled-components, or vanilla CSS)
- TypeScript interfaces and types where applicable
- Usage examples and props documentation
- Accessibility considerations (ARIA labels, semantic HTML)
- Responsive design implementation
- Performance optimization notes
- Testing suggestions and examples
- Integration instructions for the broader application

Always create production-ready, maintainable code that follows modern frontend development standards."""

    async def process_task(self, task: Task) -> str:
        """Generate frontend code and components based on task requirements"""
        
        prompt = f"""{self.get_system_prompt()}

Task: {task.title}
Description: {task.description}
Priority: {task.priority.value}

Please provide a complete frontend solution including:

1. **React Component Code** - Full implementation using modern functional components and hooks
2. **CSS/Styling** - Include Tailwind CSS classes, styled-components, or vanilla CSS as appropriate
3. **TypeScript Types** - Interface definitions and prop types if applicable
4. **Usage Example** - How to integrate and use the component in a larger application
5. **Props Documentation** - Clear documentation of all component props and their types
6. **Accessibility Features** - ARIA labels, semantic HTML, and WCAG compliance notes
7. **Responsive Design** - Mobile-first approach with breakpoint considerations
8. **Performance Optimizations** - Memoization, lazy loading, or other optimizations where relevant
9. **Testing Suggestions** - Key test cases and testing approach recommendations
10. **Integration Notes** - How this component fits into a larger React application

Format your response with clear sections and properly formatted code blocks.
Include comprehensive comments explaining the implementation details.
Ensure all code is production-ready and follows React best practices.

Focus on creating modern, accessible, and performant frontend solutions."""

        try:
            response = await self._call_ollama(prompt)
            return self._enhance_frontend_response(response, task)
        except Exception as e:
            logger.error(f"Marcus Dev task processing failed: {e}")
            return self._generate_fallback_response(task, str(e))
    
    def _enhance_frontend_response(self, response: str, task: Task) -> str:
        """Enhance the response with additional frontend-specific information"""
        
        enhancement = f"""
# ⚛️ Marcus Dev's Frontend Solution

## Task Overview
**Title:** {task.title}
**Priority:** {task.priority.value.upper()}
**Complexity:** {self._assess_complexity(task.description)}

## Implementation Details
{response}

## 🎨 Additional Frontend Recommendations

### Modern React Patterns
- Use functional components with hooks for all new components
- Implement custom hooks for reusable logic
- Consider React.memo() for performance optimization
- Use useCallback and useMemo for expensive operations
- Implement proper error boundaries for robust UX

### CSS and Styling Best Practices
- Follow BEM methodology for CSS class naming
- Use CSS Custom Properties (variables) for theming
- Implement consistent spacing and typography scales
- Consider CSS-in-JS solutions for dynamic styling
- Use Tailwind CSS for rapid, consistent styling

### Accessibility Checklist
- Ensure proper semantic HTML structure
- Add ARIA labels and descriptions where needed
- Implement keyboard navigation support
- Maintain proper color contrast ratios (WCAG AA)
- Test with screen readers and accessibility tools
- Include focus indicators for interactive elements

### Performance Optimization
- Implement code splitting with React.lazy()
- Use React.memo() for components with expensive renders
- Optimize images with proper formats and lazy loading
- Minimize bundle size with tree shaking
- Consider using a CDN for static assets
- Implement proper caching strategies

### Testing Strategy
- Unit tests with Jest and React Testing Library
- Component testing with user-focused assertions
- Integration tests for component interactions
- Visual regression testing with Storybook
- End-to-end testing with Cypress or Playwright
- Accessibility testing with jest-axe or similar tools

### Browser Compatibility
- Test across modern browsers (Chrome, Firefox, Safari, Edge)
- Consider polyfills for newer JavaScript features
- Implement graceful degradation for older browsers
- Use progressive enhancement principles
- Test on various devices and screen sizes

### Development Workflow
- Use ESLint and Prettier for code consistency
- Implement Husky for pre-commit hooks
- Set up Storybook for component development
- Use TypeScript for better developer experience
- Implement hot module replacement for faster development

## 🚀 Next Steps
1. Copy the component code into your React application
2. Install any required dependencies (check package.json)
3. Import and use the component in your application
4. Customize styling to match your design system
5. Add additional props or functionality as needed
6. Write tests for the component functionality
7. Test accessibility with screen readers and tools
8. Optimize performance if handling large datasets

**Generated by Marcus Dev - Senior Frontend Developer**
*Specialized in React, TypeScript, and modern web development*
"""
        
        return enhancement
    
    def _assess_complexity(self, description: str) -> str:
        """Assess the complexity of the frontend task"""
        description_lower = description.lower()
        
        # High complexity indicators
        high_complexity_keywords = [
            "complex state management", "redux", "context api", "performance optimization",
            "real-time", "websocket", "animation", "drag and drop", "data visualization",
            "virtual scrolling", "infinite scroll", "advanced ui", "custom hooks"
        ]
        
        # Medium complexity indicators
        medium_complexity_keywords = [
            "component", "form", "modal", "table", "chart", "responsive",
            "typescript", "testing", "accessibility", "routing", "api integration"
        ]
        
        high_score = sum(1 for keyword in high_complexity_keywords if keyword in description_lower)
        medium_score = sum(1 for keyword in medium_complexity_keywords if keyword in description_lower)
        word_count = len(description.split())
        
        if high_score >= 2 or word_count > 100:
            return "High - Advanced React patterns and complex interactions"
        elif medium_score >= 2 or word_count > 50:
            return "Medium - Standard component with multiple features"
        else:
            return "Low - Simple UI component or styling"
    
    def _generate_fallback_response(self, task: Task, error: str) -> str:
        """Generate a fallback response when AI processing fails"""
        return f"""# ⚛️ Marcus Dev - Frontend Task Analysis

## Task: {task.title}

I encountered an issue processing this frontend development task: {error}

## Recommended Approach

Based on the task description: "{task.description}"

### Suggested Implementation Structure:

1. **React Component Template**
   ```jsx
   import React, {{ useState, useEffect }} from 'react';
   import PropTypes from 'prop-types';
   
   const ComponentName = ({{ prop1, prop2, ...props }}) => {{
     const [state, setState] = useState(initialState);
     
     useEffect(() => {{
       // Side effects here
     }}, [dependencies]);
     
     const handleEvent = (event) => {{
       // Event handling logic
     }};
     
     return (
       <div className="component-container">
         {{/* Component JSX */}}
       </div>
     );
   }};
   
   ComponentName.propTypes = {{
     prop1: PropTypes.string.isRequired,
     prop2: PropTypes.func,
   }};
   
   export default ComponentName;
   ```

2. **Styling Approach**
   ```css
   /* CSS Module or Tailwind classes */
   .component-container {{
     /* Base styles */
   }}
   
   /* Responsive design */
   @media (max-width: 768px) {{
     .component-container {{
       /* Mobile styles */
     }}
   }}
   ```

3. **TypeScript Interface (if using TypeScript)**
   ```typescript
   interface ComponentProps {{
     prop1: string;
     prop2?: () => void;
     children?: React.ReactNode;
   }}
   ```

### Development Checklist:
- [ ] Create component structure with proper props
- [ ] Implement responsive design
- [ ] Add accessibility attributes (ARIA labels, semantic HTML)
- [ ] Handle loading and error states
- [ ] Add prop validation or TypeScript types
- [ ] Write unit tests
- [ ] Test on multiple devices and browsers
- [ ] Optimize performance if needed

### Next Steps:
1. Clarify specific UI requirements and design specifications
2. Define the component's props and state management needs
3. Determine styling approach (CSS modules, Tailwind, styled-components)
4. Specify accessibility and responsive design requirements
5. Plan testing strategy and browser compatibility needs

Please provide more specific requirements or try the task again with additional context.

**Marcus Dev - Senior Frontend Developer**
*Ready to build modern, accessible React applications*
"""
    
    def can_handle_task(self, task_description: str) -> float:
        """Calculate confidence score for handling this task"""
        description_lower = task_description.lower()
        
        # Frontend-specific keywords with weights
        frontend_indicators = {
            'react': 1.0, 'component': 0.9, 'jsx': 0.9, 'typescript': 0.8,
            'javascript': 0.8, 'html': 0.7, 'css': 0.8, 'scss': 0.7,
            'frontend': 1.0, 'ui': 0.9, 'user interface': 0.9, 'responsive': 0.8,
            'mobile': 0.7, 'desktop': 0.6, 'browser': 0.6, 'web': 0.6,
            'form': 0.8, 'button': 0.7, 'modal': 0.8, 'dropdown': 0.7,
            'menu': 0.7, 'navigation': 0.8, 'layout': 0.8, 'grid': 0.7,
            'flexbox': 0.8, 'animation': 0.7, 'transition': 0.7, 'hover': 0.6,
            'click': 0.6, 'event': 0.6, 'state': 0.7, 'props': 0.8,
            'hooks': 0.9, 'context': 0.8, 'redux': 0.8, 'styling': 0.8,
            'tailwind': 0.9, 'bootstrap': 0.7, 'material ui': 0.8,
            'accessibility': 0.8, 'responsive design': 0.9, 'mobile first': 0.8
        }
        
        # Calculate base confidence
        total_weight = 0
        matched_weight = 0
        
        for keyword, weight in frontend_indicators.items():
            total_weight += weight
            if keyword in description_lower:
                matched_weight += weight
        
        base_confidence = matched_weight / total_weight if total_weight > 0 else 0
        
        # Boost for frontend-specific task types
        if any(phrase in description_lower for phrase in [
            'create component', 'build ui', 'frontend', 'user interface',
            'react component', 'web page', 'responsive design', 'css styling'
        ]):
            base_confidence += 0.2
        
        # Reduce confidence for backend-specific tasks
        if any(phrase in description_lower for phrase in [
            'api', 'database', 'server', 'backend', 'sql', 'authentication',
            'rest', 'graphql', 'microservice', 'deployment'
        ]):
            base_confidence *= 0.2
        
        return min(base_confidence, 1.0)
