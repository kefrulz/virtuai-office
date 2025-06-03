import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

// Enhanced Dashboard with Boss AI Insights
const BossAIDashboard = () => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeCollaborations, setActiveCollaborations] = useState([]);
  const [workloadOptimizing, setWorkloadOptimizing] = useState(false);

  useEffect(() => {
    loadBossInsights();
    loadActiveCollaborations();
  }, []);

  const loadBossInsights = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/boss/insights`);
      const data = await response.json();
      setInsights(data);
    } catch (error) {
      console.error('Failed to load Boss AI insights:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadActiveCollaborations = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/collaboration/active`);
      const data = await response.json();
      setActiveCollaborations(data);
    } catch (error) {
      console.error('Failed to load collaborations:', error);
    }
  };

  const optimizeAssignments = async () => {
    setWorkloadOptimizing(true);
    try {
      const response = await fetch(`${API_BASE}/api/boss/optimize-assignments`, {
        method: 'POST'
      });
      const result = await response.json();
      
      alert(`Optimized ${result.optimized_tasks} out of ${result.total_tasks} tasks`);
      loadBossInsights(); // Refresh insights
    } catch (error) {
      alert('Optimization failed: ' + error.message);
    } finally {
      setWorkloadOptimizing(false);
    }
  };

  const rebalanceWorkload = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/boss/rebalance-workload`, {
        method: 'POST'
      });
      const result = await response.json();
      
      if (result.rebalanced) {
        alert(`Workload rebalanced! ${result.actions_taken} tasks reassigned.`);
        loadBossInsights();
      } else {
        alert('Rebalancing failed: ' + result.error);
      }
    } catch (error) {
      alert('Rebalancing failed: ' + error.message);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading Boss AI insights...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Boss AI Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center">
              🧠 Boss AI Control Center
            </h2>
            <p className="text-purple-100 mt-1">
              Intelligent orchestration and team coordination
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={optimizeAssignments}
              disabled={workloadOptimizing}
              className="bg-white text-purple-600 px-4 py-2 rounded-md hover:bg-gray-100 font-medium disabled:opacity-50"
            >
              {workloadOptimizing ? 'Optimizing...' : '⚡ Optimize Tasks'}
            </button>
            <button
              onClick={rebalanceWorkload}
              className="bg-yellow-500 text-white px-4 py-2 rounded-md hover:bg-yellow-600 font-medium"
            >
              ⚖️ Rebalance Workload
            </button>
          </div>
        </div>
      </div>

      {/* AI Insights Panel */}
      {insights && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="text-lg font-bold mb-4">🎯 Daily Standup Insights</h3>
          
          {/* Team Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {insights.standup?.team_metrics?.velocity || 0}
              </div>
              <div className="text-sm text-blue-700">Tasks Completed Yesterday</div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">
                {insights.standup?.team_metrics?.work_in_progress || 0}
              </div>
              <div className="text-sm text-yellow-700">Work in Progress</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {insights.standup?.team_metrics?.queue_size || 0}
              </div>
              <div className="text-sm text-green-700">Tasks in Queue</div>
            </div>
          </div>

          {/* AI Analysis */}
          <div className="bg-gray-50 p-4 rounded-lg mb-4">
            <h4 className="font-medium text-gray-900 mb-2">🤖 AI Analysis</h4>
            <p className="text-gray-700 whitespace-pre-wrap">
              {insights.standup?.ai_insights || 'No insights available'}
            </p>
          </div>

          {/* System Recommendations */}
          {insights.system_recommendations && insights.system_recommendations.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg">
              <h4 className="font-medium text-amber-800 mb-2">💡 Recommendations</h4>
              <ul className="list-disc list-inside space-y-1">
                {insights.system_recommendations.map((rec, index) => (
                  <li key={index} className="text-amber-700">{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Active Collaborations */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold">🤝 Active Collaborations</h3>
          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm">
            {activeCollaborations.length} active
          </span>
        </div>

        {activeCollaborations.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">🤖</div>
            <p>No active collaborations</p>
            <p className="text-sm">Complex tasks will automatically trigger team collaboration</p>
          </div>
        ) : (
          <div className="space-y-3">
            {activeCollaborations.map(collab => (
              <div key={collab.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{collab.primary_task.title}</h4>
                    <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                      <span>Type: {collab.collaboration_type}</span>
                      <span>Status: {collab.status}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      collab.status === 'active' 
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {collab.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Boss Decisions */}
      {insights?.recent_decisions && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="text-lg font-bold mb-4">🧠 Recent AI Decisions</h3>
          <div className="space-y-3">
            {insights.recent_decisions.map((decision, index) => (
              <div key={index} className="border-l-4 border-purple-500 pl-4 py-2">
                <div className="flex items-center justify-between">
                  <span className="font-medium capitalize">{decision.type.replace('_', ' ')}</span>
                  <span className="text-xs text-gray-500">
                    {new Date(decision.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-gray-700 text-sm mt-1">{decision.reasoning}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Smart Task Creation with AI Assignment
const SmartTaskCreator = ({ isOpen, onClose, onSubmit, projects }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    project_id: '',
    use_smart_assignment: true
  });
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  const analyzeTask = async () => {
    if (!formData.title || !formData.description) return;

    setAnalyzing(true);
    try {
      // Mock AI analysis - in real implementation, this would call Boss AI
      await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate AI thinking
      
      setAiAnalysis({
        complexity: 'medium',
        estimated_effort: 4.5,
        required_skills: ['react', 'ui-ux'],
        suggested_agent: 'Marcus Dev',
        collaboration_needed: false,
        confidence: 0.87
      });
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  useEffect(() => {
    if (formData.title && formData.description && formData.use_smart_assignment) {
      const debounceTimer = setTimeout(analyzeTask, 1000);
      return () => clearTimeout(debounceTimer);
    }
  }, [formData.title, formData.description, formData.use_smart_assignment]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.use_smart_assignment) {
      // Use smart assignment endpoint
      try {
        const response = await fetch(`${API_BASE}/api/tasks/smart-assign`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: formData.title,
            description: formData.description,
            priority: formData.priority,
            project_id: formData.project_id || null
          })
        });
        
        const result = await response.json();
        
        if (response.ok) {
          onSubmit && onSubmit(result);
          setFormData({ title: '', description: '', priority: 'medium', project_id: '', use_smart_assignment: true });
          setAiAnalysis(null);
        } else {
          throw new Error(result.detail || 'Failed to create task');
        }
      } catch (error) {
        alert('Smart assignment failed: ' + error.message);
      }
    } else {
      // Use regular task creation
      onSubmit && onSubmit(formData);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">🧠 Smart Task Creation</h2>
        
        <form onSubmit={handleSubmit}>
          {/* Smart Assignment Toggle */}
          <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.use_smart_assignment}
                onChange={(e) => setFormData({...formData, use_smart_assignment: e.target.checked})}
                className="mr-2"
              />
              <span className="font-medium text-purple-800">
                🧠 Use Boss AI for intelligent assignment
              </span>
            </label>
            <p className="text-sm text-purple-600 mt-1">
              AI will analyze your task and assign it to the optimal agent
            </p>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Task Title *
            </label>
            <input
              type="text"
              required
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              placeholder="e.g., Create user login page with validation"
            />
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description *
            </label>
            <textarea
              required
              rows="4"
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Describe what you need in detail..."
            />
          </div>

          {/* AI Analysis Display */}
          {formData.use_smart_assignment && (
            <div className="mb-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                🤖 AI Analysis
                {analyzing && <div className="ml-2 animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>}
              </h4>
              
              {analyzing ? (
                <p className="text-gray-600">Analyzing task requirements...</p>
              ) : aiAnalysis ? (
                <div className="space-y-2 text-sm">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="font-medium">Complexity:</span> {aiAnalysis.complexity}
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
                    <span className="font-medium">Required Skills:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {aiAnalysis.required_skills.map(skill => (
                        <span key={skill} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                  {aiAnalysis.collaboration_needed && (
                    <div className="p-2 bg-yellow-100 border border-yellow-300 rounded">
                      <span className="text-yellow-800 text-sm">
                        🤝 This task may benefit from multi-agent collaboration
                      </span>
                    </div>
                  )}
                </div>
              ) : formData.title && formData.description ? (
                <p className="text-gray-600">Ready to analyze - Boss AI will evaluate this task</p>
              ) : (
                <p className="text-gray-500">Enter task details to see AI analysis</p>
              )}
            </div>
          )}
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priority
              </label>
              <select
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={formData.priority}
                onChange={(e) => setFormData({...formData, priority: e.target.value})}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            
            {projects.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project (Optional)
                </label>
                <select
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.project_id}
                  onChange={(e) => setFormData({...formData, project_id: e.target.value})}
                >
                  <option value="">No project</option>
                  {projects.map(project => (
                    <option key={project.id} value={project.id}>{project.name}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
          
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center"
            >
              {formData.use_smart_assignment && '🧠 '}
              Create Task
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BossAIDashboard;
export { SmartTaskCreator };
