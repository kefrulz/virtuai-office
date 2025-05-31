import React, { useState, useEffect } from 'react';
import { useNotifications } from './NotificationSystem';

const CreateTaskModal = ({ isOpen, onClose, onSubmit, projects = [] }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    project_id: '',
    use_smart_assignment: true
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [errors, setErrors] = useState({});
  
  const { addNotification } = useNotifications();

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setFormData({
        title: '',
        description: '',
        priority: 'medium',
        project_id: '',
        use_smart_assignment: true
      });
      setErrors({});
      setAiAnalysis(null);
    }
  }, [isOpen]);

  // AI Analysis with debouncing
  useEffect(() => {
    if (formData.title && formData.description && formData.use_smart_assignment) {
      const debounceTimer = setTimeout(() => {
        analyzeTask();
      }, 1000);
      return () => clearTimeout(debounceTimer);
    } else {
      setAiAnalysis(null);
    }
  }, [formData.title, formData.description, formData.use_smart_assignment]);

  const analyzeTask = async () => {
    if (!formData.title.trim() || !formData.description.trim()) return;

    setAnalyzing(true);
    try {
      // Simulate AI analysis - in real implementation, this would call Boss AI
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Mock analysis based on keywords
      const description = formData.description.toLowerCase();
      let suggestedAgent = 'Marcus Dev';
      let complexity = 'medium';
      let estimatedEffort = 3.0;
      let requiredSkills = ['general'];
      let collaborationNeeded = false;

      // Analyze content for agent assignment
      if (description.includes('react') || description.includes('component') || description.includes('frontend')) {
        suggestedAgent = 'Marcus Dev';
        requiredSkills = ['react', 'javascript', 'css'];
      } else if (description.includes('api') || description.includes('backend') || description.includes('database')) {
        suggestedAgent = 'Sarah Backend';
        requiredSkills = ['python', 'fastapi', 'database'];
      } else if (description.includes('design') || description.includes('wireframe') || description.includes('mockup')) {
        suggestedAgent = 'Luna Design';
        requiredSkills = ['ui-ux', 'design', 'wireframing'];
      } else if (description.includes('test') || description.includes('qa') || description.includes('quality')) {
        suggestedAgent = 'TestBot QA';
        requiredSkills = ['testing', 'qa', 'automation'];
      } else if (description.includes('story') || description.includes('requirement') || description.includes('plan')) {
        suggestedAgent = 'Alice Chen';
        requiredSkills = ['product-management', 'requirements', 'planning'];
      }

      // Analyze complexity
      const wordCount = formData.description.split(' ').length;
      if (wordCount > 100 || description.includes('complex') || description.includes('system')) {
        complexity = 'complex';
        estimatedEffort = 6.0;
        collaborationNeeded = true;
      } else if (wordCount < 20 || description.includes('simple') || description.includes('quick')) {
        complexity = 'simple';
        estimatedEffort = 1.5;
      }

      setAiAnalysis({
        complexity,
        estimated_effort: estimatedEffort,
        required_skills: requiredSkills,
        suggested_agent: suggestedAgent,
        collaboration_needed: collaborationNeeded,
        confidence: 0.85 + Math.random() * 0.1 // Random confidence between 0.85-0.95
      });
    } catch (error) {
      console.error('Analysis failed:', error);
      addNotification('AI analysis failed', 'warning');
    } finally {
      setAnalyzing(false);
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    } else if (formData.title.length < 5) {
      newErrors.title = 'Title must be at least 5 characters';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    } else if (formData.description.length < 20) {
      newErrors.description = 'Description must be at least 20 characters for better AI results';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    
    try {
      if (formData.use_smart_assignment) {
        // Use smart assignment endpoint
        const response = await fetch('http://localhost:8000/api/tasks/smart-assign', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: formData.title.trim(),
            description: formData.description.trim(),
            priority: formData.priority,
            project_id: formData.project_id || null
          })
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to create task');
        }
        
        const result = await response.json();
        onSubmit(result);
        addNotification(`Task created and assigned to ${aiAnalysis?.suggested_agent || 'AI team'}!`, 'success');
      } else {
        // Use regular task creation
        const response = await fetch('http://localhost:8000/api/tasks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: formData.title.trim(),
            description: formData.description.trim(),
            priority: formData.priority,
            project_id: formData.project_id || null
          })
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to create task');
        }
        
        const result = await response.json();
        onSubmit(result);
        addNotification('Task created successfully!', 'success');
      }
      
      onClose();
    } catch (error) {
      console.error('Task creation failed:', error);
      addNotification(`Failed to create task: ${error.message}`, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const getCharacterCount = (text, min) => {
    const count = text.length;
    const color = count >= min ? 'text-green-600' : 'text-orange-600';
    return <span className={`text-xs ${color}`}>{count}/{min}+ characters</span>;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              {formData.use_smart_assignment ? '🧠 Smart Task Creation' : '📝 Create New Task'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 transition-colors"
              disabled={isSubmitting}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Smart Assignment Toggle */}
            <div className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.use_smart_assignment}
                  onChange={(e) => handleInputChange('use_smart_assignment', e.target.checked)}
                  className="mr-3 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                  disabled={isSubmitting}
                />
                <div>
                  <span className="font-medium text-purple-800">
                    🧠 Use Boss AI for intelligent assignment
                  </span>
                  <p className="text-sm text-purple-600 mt-1">
                    AI will analyze your task and assign it to the optimal agent with collaboration planning
                  </p>
                </div>
              </label>
            </div>

            {/* Task Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Task Title *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors ${
                  errors.title ? 'border-red-500 bg-red-50' : 'border-gray-300'
                }`}
                placeholder="e.g., Create responsive user dashboard component"
                disabled={isSubmitting}
              />
              <div className="flex justify-between mt-1">
                {errors.title && <p className="text-red-600 text-sm">{errors.title}</p>}
                <div className="ml-auto">{getCharacterCount(formData.title, 5)}</div>
              </div>
            </div>
            
            {/* Task Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description *
              </label>
              <textarea
                rows={6}
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors ${
                  errors.description ? 'border-red-500 bg-red-50' : 'border-gray-300'
                }`}
                placeholder="Describe what you need in detail. Include requirements, constraints, and expected outcomes. The more specific you are, the better results you'll get from your AI team."
                disabled={isSubmitting}
              />
              <div className="flex justify-between mt-1">
                {errors.description && <p className="text-red-600 text-sm">{errors.description}</p>}
                <div className="ml-auto">{getCharacterCount(formData.description, 20)}</div>
              </div>
              
              {/* Writing Tips */}
              <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="text-sm font-medium text-blue-800 mb-1">💡 Tips for better results:</h4>
                <ul className="text-xs text-blue-700 space-y-1">
                  <li>• Be specific about requirements and constraints</li>
                  <li>• Mention technologies, frameworks, or tools you prefer</li>
                  <li>• Include context about your project or use case</li>
                  <li>• Specify the expected output format (code, documentation, etc.)</li>
                </ul>
              </div>
            </div>

            {/* AI Analysis Display */}
            {formData.use_smart_assignment && (
              <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                  🤖 AI Analysis
                  {analyzing && (
                    <div className="ml-2 w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  )}
                </h4>
                
                {analyzing ? (
                  <div className="text-center py-4">
                    <div className="text-blue-600 mb-2">Analyzing task requirements...</div>
                    <div className="text-sm text-gray-600">Boss AI is evaluating complexity, skills needed, and optimal assignment</div>
                  </div>
                ) : aiAnalysis ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Complexity:</span>
                        <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                          aiAnalysis.complexity === 'simple' ? 'bg-green-100 text-green-800' :
                          aiAnalysis.complexity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {aiAnalysis.complexity}
                        </span>
                      </div>
                      <div>
                        <span className="font-medium">Estimated:</span> {aiAnalysis.estimated_effort}h
                      </div>
                      <div>
                        <span className="font-medium">Suggested Agent:</span> {aiAnalysis.suggested_agent}
                      </div>
                      <div>
                        <span className="font-medium">Confidence:</span> {Math.round(aiAnalysis.confidence * 100)}%
                      </div>
                    </div>
                    
                    <div>
                      <span className="font-medium text-sm">Required Skills:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {aiAnalysis.required_skills.map(skill => (
                          <span key={skill} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    {aiAnalysis.collaboration_needed && (
                      <div className="p-2 bg-amber-100 border border-amber-300 rounded">
                        <span className="text-amber-800 text-sm flex items-center">
                          🤝 <span className="ml-1">Multi-agent collaboration recommended for this complex task</span>
                        </span>
                      </div>
                    )}
                  </div>
                ) : formData.title && formData.description ? (
                  <p className="text-gray-600 text-sm">Ready to analyze - Boss AI will evaluate this task when you finish writing</p>
                ) : (
                  <p className="text-gray-500 text-sm">Enter task details above to see AI analysis</p>
                )}
              </div>
            )}
            
            {/* Priority and Project */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority
                </label>
                <select
                  value={formData.priority}
                  onChange={(e) => handleInputChange('priority', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isSubmitting}
                >
                  <option value="low">🟢 Low - Nice to have</option>
                  <option value="medium">🟡 Medium - Standard priority</option>
                  <option value="high">🟠 High - Important</option>
                  <option value="urgent">🔴 Urgent - Critical</option>
                </select>
              </div>
              
              {projects.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Project (Optional)
                  </label>
                  <select
                    value={formData.project_id}
                    onChange={(e) => handleInputChange('project_id', e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isSubmitting}
                  >
                    <option value="">No project</option>
                    {projects.map(project => (
                      <option key={project.id} value={project.id}>{project.name}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
            
            {/* Submit Buttons */}
            <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-3 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !formData.title.trim() || !formData.description.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    Creating...
                  </>
                ) : (
                  <>
                    {formData.use_smart_assignment && '🧠 '}
                    Create Task
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateTaskModal;
