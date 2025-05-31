import React, { useState, useEffect, useRef } from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import TutorialSystem from './components/Tutorial';
import HelpSystem from './components/HelpSystem';
import OnboardingWizard from './components/OnboardingWizard';
import { useNotifications, useCommonNotifications } from './components/NotificationSystem';
import { PWAInstallBanner } from './utils/pwa';
import { useKeyboardNavigation, useScreenReader } from './utils/accessibility';

const API_BASE = 'http://localhost:8000';

// Utility function for API calls
const apiCall = async (endpoint, options = {}) => {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
};

// Agent color scheme
const AGENT_COLORS = {
  product_manager: 'bg-purple-100 text-purple-800 border-purple-300',
  frontend_developer: 'bg-blue-100 text-blue-800 border-blue-300',
  backend_developer: 'bg-green-100 text-green-800 border-green-300',
  ui_ux_designer: 'bg-pink-100 text-pink-800 border-pink-300',
  qa_tester: 'bg-orange-100 text-orange-800 border-orange-300',
};

// Agent icons
const AGENT_ICONS = {
  product_manager: '👩‍💼',
  frontend_developer: '👨‍💻',
  backend_developer: '👩‍💻',
  ui_ux_designer: '🎨',
  qa_tester: '🔍',
};

// Task status colors
const STATUS_COLORS = {
  pending: 'bg-gray-100 text-gray-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

// Priority colors
const PRIORITY_COLORS = {
  low: 'bg-gray-100 text-gray-600',
  medium: 'bg-blue-100 text-blue-600',
  high: 'bg-orange-100 text-orange-600',
  urgent: 'bg-red-100 text-red-600',
};

// TaskCard Component
const TaskCard = ({ task, onViewDetails, onRetry, onDelete }) => {
  const formatDate = (dateString) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleString();
  };

  const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow card-hover">
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-medium text-gray-900 flex-1 pr-2">{task.title}</h3>
        <div className="flex space-x-1">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[task.status]}`}>
            {task.status.replace('_', ' ')}
          </span>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${PRIORITY_COLORS[task.priority]}`}>
            {task.priority}
          </span>
        </div>
      </div>
      
      <p className="text-gray-600 text-sm mb-3">{truncateText(task.description)}</p>
      
      {task.agent_name && (
        <div className="flex items-center mb-2">
          <span className="text-lg mr-2">{AGENT_ICONS[task.agent_id] || '🤖'}</span>
          <span className="text-sm font-medium text-gray-700">{task.agent_name}</span>
        </div>
      )}
      
      <div className="text-xs text-gray-500 mb-3">
        <div>Created: {formatDate(task.created_at)}</div>
        {task.completed_at && <div>Completed: {formatDate(task.completed_at)}</div>}
      </div>
      
      <div className="flex justify-between items-center">
        <button
          onClick={() => onViewDetails(task)}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          View Details
        </button>
        
        <div className="flex space-x-2">
          {task.status === 'failed' && (
            <button
              onClick={() => onRetry(task.id)}
              className="text-orange-600 hover:text-orange-800 text-sm font-medium"
            >
              Retry
            </button>
          )}
          {task.status !== 'in_progress' && (
            <button
              onClick={() => onDelete(task.id)}
              className="text-red-600 hover:text-red-800 text-sm font-medium"
            >
              Delete
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// AgentCard Component
const AgentCard = ({ agent, onViewTasks, onViewPerformance }) => {
  const completionRate = agent.task_count > 0
    ? Math.round((agent.completed_tasks / agent.task_count) * 100)
    : 0;

  const getPerformanceIndicator = (rate) => {
    if (rate >= 90) return { color: 'bg-green-500', label: 'Excellent' };
    if (rate >= 70) return { color: 'bg-yellow-500', label: 'Good' };
    if (rate >= 50) return { color: 'bg-orange-500', label: 'Fair' };
    return { color: 'bg-red-500', label: 'Improving' };
  };

  const performance = getPerformanceIndicator(completionRate);

  return (
    <div className={`border rounded-lg p-4 ${AGENT_COLORS[agent.type]} hover:shadow-md transition-shadow cursor-pointer card-hover`}
         onClick={() => onViewTasks(agent)}>
      <div className="flex items-center mb-3">
        <span className="text-3xl mr-3">{AGENT_ICONS[agent.type]}</span>
        <div className="flex-1">
          <h3 className="font-bold text-lg">{agent.name}</h3>
          <p className="text-sm opacity-75">{agent.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${performance.color}`} title={performance.label}></div>
          <span className="text-xs opacity-75">{performance.label}</span>
        </div>
      </div>
      
      <p className="text-sm mb-3 opacity-90">{agent.description}</p>
      
      <div className="flex justify-between items-center text-sm mb-3">
        <div>
          <span className="font-medium">{agent.completed_tasks}</span>
          <span className="opacity-75"> / {agent.task_count} tasks</span>
        </div>
        <div className="font-medium">{completionRate}% complete</div>
      </div>
      
      <div className="mb-4">
        <div className="text-xs opacity-75 mb-1">Expertise:</div>
        <div className="flex flex-wrap gap-1">
          {agent.expertise.slice(0, 3).map((skill, index) => (
            <span key={index} className="text-xs px-2 py-1 bg-white bg-opacity-50 rounded">
              {skill}
            </span>
          ))}
          {agent.expertise.length > 3 && (
            <span className="text-xs px-2 py-1 bg-white bg-opacity-50 rounded">
              +{agent.expertise.length - 3} more
            </span>
          )}
        </div>
      </div>

      <div className="flex space-x-2" onClick={(e) => e.stopPropagation()}>
        <button
          onClick={() => onViewTasks(agent)}
          className="flex-1 text-blue-600 hover:text-blue-800 text-sm font-medium py-2 px-3 bg-blue-50 hover:bg-blue-100 rounded"
        >
          View Tasks
        </button>
        <button
          onClick={() => onViewPerformance && onViewPerformance(agent)}
          className="flex-1 text-purple-600 hover:text-purple-800 text-sm font-medium py-2 px-3 bg-purple-50 hover:bg-purple-100 rounded"
        >
          📊 Analytics
        </button>
      </div>
    </div>
  );
};

// CreateTaskModal Component
const CreateTaskModal = ({ isOpen, onClose, onSubmit, projects }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    project_id: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
    setFormData({ title: '', description: '', priority: 'medium', project_id: '' });
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto animate-fade-in" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold mb-4">Create New Task</h2>
        
        <form onSubmit={handleSubmit}>
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
              placeholder="e.g., Create user login page"
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
          
          <div className="mb-4">
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
            <div className="mb-4">
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
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Create Task
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// TaskDetailsModal Component
const TaskDetailsModal = ({ task, isOpen, onClose }) => {
  if (!isOpen || !task) return null;

  const formatDate = (dateString) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto animate-fade-in" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-xl font-bold">{task.title}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
          >
            ×
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Task Information</h3>
            <div className="space-y-2 text-sm">
              <div><span className="font-medium">Status:</span>
                <span className={`ml-2 px-2 py-1 rounded-full text-xs ${STATUS_COLORS[task.status]}`}>
                  {task.status.replace('_', ' ')}
                </span>
              </div>
              <div><span className="font-medium">Priority:</span>
                <span className={`ml-2 px-2 py-1 rounded-full text-xs ${PRIORITY_COLORS[task.priority]}`}>
                  {task.priority}
                </span>
              </div>
              <div><span className="font-medium">Created:</span> {formatDate(task.created_at)}</div>
              {task.started_at && <div><span className="font-medium">Started:</span> {formatDate(task.started_at)}</div>}
              {task.completed_at && <div><span className="font-medium">Completed:</span> {formatDate(task.completed_at)}</div>}
              {task.actual_effort && <div><span className="font-medium">Effort:</span> {task.actual_effort} hours</div>}
            </div>
          </div>
          
          {task.agent_name && (
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Assigned Agent</h3>
              <div className="flex items-center">
                <span className="text-2xl mr-3">{AGENT_ICONS[task.agent_id] || '🤖'}</span>
                <div>
                  <div className="font-medium">{task.agent_name}</div>
                  <div className="text-sm text-gray-600">
                    {task.agent_id ? task.agent_id.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'AI Agent'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        
        <div className="mb-6">
          <h3 className="font-medium text-gray-900 mb-2">Description</h3>
          <p className="text-gray-700 whitespace-pre-wrap">{task.description}</p>
        </div>
        
        {task.output && (
          <div>
            <h3 className="font-medium text-gray-900 mb-2">AI Generated Output</h3>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                {task.output}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// StandupModal Component
const StandupModal = ({ isOpen, onClose }) => {
  const [standupData, setStandupData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      generateStandup();
    }
  }, [isOpen]);

  const generateStandup = async () => {
    setLoading(true);
    try {
      const data = await apiCall('/api/standup', { method: 'POST' });
      setStandupData(data);
    } catch (error) {
      console.error('Failed to generate standup:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-fade-in" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Daily Standup Report</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
          >
            ×
          </button>
        </div>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-gray-600">Generating standup report...</p>
          </div>
        ) : standupData ? (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900">
                Team Standup - {standupData.date}
              </h3>
              <p className="text-gray-600 mt-1">{standupData.team_summary}</p>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-3">✅ Completed Yesterday</h4>
              {standupData.completed_yesterday.length > 0 ? (
                <div className="space-y-2">
                  {standupData.completed_yesterday.map((task) => (
                    <div key={task.task_id} className="bg-green-50 border border-green-200 rounded p-3">
                      <div className="font-medium text-green-900">{task.title}</div>
                      <div className="text-sm text-green-700">By {task.agent_name}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 italic">No tasks completed yesterday</p>
              )}
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-3">🔄 In Progress Today</h4>
              {standupData.in_progress_today.length > 0 ? (
                <div className="space-y-2">
                  {standupData.in_progress_today.map((task) => (
                    <div key={task.task_id} className="bg-yellow-50 border border-yellow-200 rounded p-3">
                      <div className="font-medium text-yellow-900">{task.title}</div>
                      <div className="text-sm text-yellow-700">By {task.agent_name}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 italic">No tasks currently in progress</p>
              )}
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-3">📋 Upcoming Tasks</h4>
              {standupData.upcoming_tasks.length > 0 ? (
                <div className="space-y-2">
                  {standupData.upcoming_tasks.map((task) => (
                    <div key={task.task_id} className="bg-blue-50 border border-blue-200 rounded p-3">
                      <div className="font-medium text-blue-900">{task.title}</div>
                      <div className="text-sm text-blue-700">Priority: {task.priority}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 italic">No pending tasks</p>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-red-600">Failed to generate standup report</p>
            <button
              onClick={generateStandup}
              className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// AppleSiliconDashboard Component
const AppleSiliconDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const data = await apiCall('/api/apple-silicon/dashboard');
      setDashboardData(data);
    } catch (error) {
      console.error('Failed to load Apple Silicon dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const optimizeSystem = async () => {
    try {
      await apiCall('/api/apple-silicon/optimize', { method: 'POST' });
      loadDashboardData();
    } catch (error) {
      console.error('Optimization failed:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="loading-spinner mr-3"></div>
        <span>Loading Apple Silicon dashboard...</span>
      </div>
    );
  }

  if (!dashboardData?.system_info?.is_apple_silicon) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-bold text-blue-800 mb-2">Apple Silicon Not Detected</h3>
        <p className="text-blue-700">
          Apple Silicon optimizations are available for M1, M2, and M3 Macs.
          Your system will still work great with VirtuAI Office!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">🍎 Apple Silicon Dashboard</h2>
            <p className="text-purple-100 mt-1">
              {dashboardData.system_info.chip_type.toUpperCase()} • {dashboardData.system_info.memory_gb}GB Unified Memory
            </p>
          </div>
          <button
            onClick={optimizeSystem}
            className="bg-white text-purple-600 px-4 py-2 rounded-md hover:bg-gray-100 font-medium"
          >
            ⚡ Optimize System
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-2xl font-bold text-blue-600">
            {Math.round(dashboardData.optimization.score)}%
          </div>
          <div className="text-sm text-gray-600">Optimization Score</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-2xl font-bold text-green-600">
            {dashboardData.current_performance.inference_speed.toFixed(1)}
          </div>
          <div className="text-sm text-gray-600">Tokens/Second</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-2xl font-bold text-purple-600">
            {dashboardData.current_performance.memory_usage.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Memory Usage</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-2xl font-bold text-orange-600">
            {dashboardData.current_performance.thermal_state}
          </div>
          <div className="text-sm text-gray-600">Thermal State</div>
        </div>
      </div>

      {dashboardData.optimization.recommendations.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg">
          <h4 className="font-medium text-amber-800 mb-2">💡 Recommendations</h4>
          <ul className="list-disc list-inside space-y-1">
            {dashboardData.optimization.recommendations.map((rec, index) => (
              <li key={index} className="text-amber-700">{rec}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// Main App Component
function App() {
  // Hooks
  const { addNotification } = useNotifications();
  const notifications = useCommonNotifications();
  const { announce } = useScreenReader();
  useKeyboardNavigation();

  // State management
  const [activeTab, setActiveTab] = useState('dashboard');
  const [tasks, setTasks] = useState([]);
  const [agents, setAgents] = useState([]);
  const [projects, setProjects] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [agentTasks, setAgentTasks] = useState([]);
  const [showCreateTask, setShowCreateTask] = useState(false);
  const [showTaskDetails, setShowTaskDetails] = useState(false);
  const [showStandup, setShowStandup] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);

  // WebSocket for real-time updates
  const ws = useRef(null);

  // Load initial data
  useEffect(() => {
    // Check if first time user
    const hasCompletedOnboarding = localStorage.getItem('virtuai-onboarding-completed');
    if (!hasCompletedOnboarding) {
      setShowOnboarding(true);
    }

    loadData();
    setupWebSocket();
    
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  const setupWebSocket = () => {
    try {
      ws.current = new WebSocket('ws://localhost:8000/ws');
      
      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.log('WebSocket message:', event.data);
        }
      };
      
      ws.current.onopen = () => {
        console.log('WebSocket connected');
        notifications.connectionRestored();
      };
      
      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        notifications.connectionLost();
        // Attempt to reconnect after 5 seconds
        setTimeout(setupWebSocket, 5000);
      };
      
    } catch (error) {
      console.error('WebSocket setup failed:', error);
    }
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'task_update':
        announce(`Task ${data.task_id} status updated to ${data.status}`);
        loadTasks();
        break;
      case 'task_completed':
        notifications.taskCompleted(data.task_id, data.agent_name);
        announce(`${data.agent_name} completed a task`);
        loadTasks();
        loadAnalytics();
        break;
      case 'task_failed':
        notifications.taskFailed(data.task_id, data.error);
        announce(`Task ${data.task_id} failed`);
        loadTasks();
        break;
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadTasks(),
        loadAgents(),
        loadProjects(),
        loadAnalytics(),
        loadSystemStatus()
      ]);
    } catch (error) {
      console.error('Failed to load data:', error);
      addNotification('Failed to load data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadTasks = async () => {
    try {
      const data = await apiCall('/api/tasks');
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    }
  };

  const loadAgents = async () => {
    try {
      const data = await apiCall('/api/agents');
      setAgents(data);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const loadProjects = async () => {
    try {
      const data = await apiCall('/api/projects');
      setProjects(data);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const loadAnalytics = async () => {
    try {
      const data = await apiCall('/api/analytics');
      setAnalytics(data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    }
  };

  const loadSystemStatus = async () => {
    try {
      const data = await apiCall('/api/status');
      setSystemStatus(data);
    } catch (error) {
      console.error('Failed to load system status:', error);
    }
  };

  const loadAgentTasks = async (agentId) => {
    try {
      const data = await apiCall(`/api/agents/${agentId}/tasks`);
      setAgentTasks(data);
    } catch (error) {
      console.error('Failed to load agent tasks:', error);
      addNotification('Failed to load agent tasks', 'error');
    }
  };

  const createTask = async (taskData) => {
    try {
      await apiCall('/api/tasks', {
        method: 'POST',
        body: JSON.stringify(taskData),
      });
      
      notifications.taskCreated(taskData.title);
      setShowCreateTask(false);
      loadTasks();
      loadAnalytics();
    } catch (error) {
      console.error('Failed to create task:', error);
      addNotification('Failed to create task', 'error');
    }
  };

  const retryTask = async (taskId) => {
    try {
      await apiCall(`/api/tasks/${taskId}/retry`, { method: 'POST' });
      addNotification('Task queued for retry', 'success');
      loadTasks();
    } catch (error) {
      console.error('Failed to retry task:', error);
      addNotification('Failed to retry task', 'error');
    }
  };

  const deleteTask = async (taskId) => {
    if (!window.confirm('Are you sure you want to delete this task?')) return;
    
    try {
      await apiCall(`/api/tasks/${taskId}`, { method: 'DELETE' });
      addNotification('Task deleted successfully', 'success');
      loadTasks();
      loadAnalytics();
    } catch (error) {
      console.error('Failed to delete task:', error);
      addNotification('Failed to delete task', 'error');
    }
  };

  const populateDemoData = async () => {
    try {
      await apiCall('/api/demo/populate', { method: 'POST' });
      addNotification('Demo data created successfully!', 'success');
      loadData();
    } catch (error) {
      console.error('Failed to populate demo data:', error);
      addNotification('Failed to create demo data', 'error');
    }
  };

  const handleViewTaskDetails = (task) => {
    setSelectedTask(task);
    setShowTaskDetails(true);
  };

  const handleViewAgentTasks = (agent) => {
    setSelectedAgent(agent);
    setActiveTab('agent-detail');
    loadAgentTasks(agent.id);
  };

  const handleOnboardingComplete = () => {
    setShowOnboarding(false);
    // Create first task if provided in onboarding
    const preferences = JSON.parse(localStorage.getItem('virtuai-user-preferences') || '{}');
    if (preferences.first_task) {
      createTask(preferences.first_task);
    }
  };

  // Dashboard Tab
  const renderDashboard = () => (
    <div className="space-y-6">
      {/* System Status */}
      {systemStatus && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">🚀 VirtuAI Office Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-gray-600">System Status</div>
              <div className={`font-medium ${systemStatus.status === 'healthy' ? 'text-green-600' : 'text-red-600'}`}>
                {systemStatus.status === 'healthy' ? '✅ Healthy' : '❌ Issues Detected'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Ollama Connection</div>
              <div className={`font-medium ${systemStatus.ollama_status === 'connected' ? 'text-green-600' : 'text-red-600'}`}>
                {systemStatus.ollama_status === 'connected' ? '✅ Connected' : '❌ Disconnected'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Available Models</div>
              <div className="font-medium text-blue-600">
                {systemStatus.available_models?.length || 0} models
              </div>
            </div>
          </div>
          
          {systemStatus.available_models && systemStatus.available_models.length > 0 && (
            <div className="mt-4">
              <div className="text-sm text-gray-600 mb-2">AI Models:</div>
              <div className="flex flex-wrap gap-2">
                {systemStatus.available_models.map(model => (
                  <span key={model} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                    {model}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Analytics Overview */}
      {analytics && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">📊 Team Performance</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{analytics.total_tasks}</div>
              <div className="text-sm text-gray-600">Total Tasks</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{analytics.completed_tasks}</div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{analytics.in_progress_tasks}</div>
              <div className="text-sm text-gray-600">In Progress</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {Math.round(analytics.completion_rate * 100)}%
              </div>
              <div className="text-sm text-gray-600">Success Rate</div>
            </div>
          </div>
          
          {/* Agent Performance */}
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Agent Performance</h3>
            <div className="space-y-2">
              {analytics.agent_performance.map(agent => (
                <div key={agent.agent_id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div className="flex items-center">
                    <span className="text-lg mr-3">{AGENT_ICONS[agent.agent_type] || '🤖'}</span>
                    <div>
                      <div className="font-medium">{agent.agent_name}</div>
                      <div className="text-sm text-gray-600">
                        {agent.completed_tasks} / {agent.total_tasks} tasks
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-green-600">
                      {Math.round(agent.completion_rate * 100)}%
                    </div>
                    <div className="text-sm text-gray-600">
                      {agent.avg_effort_hours}h avg
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Recent Tasks */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">📋 Recent Tasks</h2>
          <button
            id="create-task-button"
            onClick={() => setShowCreateTask(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            + New Task
          </button>
        </div>
        
        <div className="task-list">
          {tasks.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">No tasks yet. Create your first task to get started!</p>
              <button
                onClick={populateDemoData}
                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
              >
                📝 Create Demo Tasks
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {tasks.slice(0, 6).map(task => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onViewDetails={handleViewTaskDetails}
                  onRetry={retryTask}
                  onDelete={deleteTask}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Agents Tab
  const renderAgents = () => (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">🤖 AI Development Team</h2>
        <p className="text-gray-600 mb-6">
          Meet your specialized AI agents. Each agent has unique expertise and will automatically handle tasks that match their skills.
        </p>
        
        <div className="agent-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map(agent => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onViewTasks={handleViewAgentTasks}
            />
          ))}
        </div>
      </div>
    </div>
  );

  // Tasks Tab
  const renderTasks = () => (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">📋 All Tasks</h2>
          <div className="flex space-x-2">
            <button
              onClick={() => setShowStandup(true)}
              className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition-colors"
            >
              📊 Daily Standup
            </button>
            <button
              onClick={() => setShowCreateTask(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              + New Task
            </button>
          </div>
        </div>
        
        {/* Task Filters */}
        <div className="flex space-x-4 mb-6">
          <select className="border border-gray-300 rounded-md px-3 py-2">
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
          
          <select className="border border-gray-300 rounded-md px-3 py-2">
            <option value="">All Priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        </div>
        
        {tasks.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">No tasks found.</p>
            <button
              onClick={populateDemoData}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
            >
              📝 Create Demo Tasks
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tasks.map(task => (
              <TaskCard
                key={task.id}
                task={task}
                onViewDetails={handleViewTaskDetails}
                onRetry={retryTask}
                onDelete={deleteTask}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );

  // Agent Detail Tab
  const renderAgentDetail = () => {
    if (!selectedAgent) return null;

    return (
      <div className="space-y-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <button
                onClick={() => setActiveTab('agents')}
                className="text-gray-500 hover:text-gray-700 mr-4"
              >
                ← Back to Agents
              </button>
              <span className="text-3xl mr-4">{AGENT_ICONS[selectedAgent.type]}</span>
              <div>
                <h2 className="text-2xl font-bold">{selectedAgent.name}</h2>
                <p className="text-gray-600">
                  {selectedAgent.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </p>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Description</h3>
              <p className="text-gray-700">{selectedAgent.description}</p>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Expertise</h3>
              <div className="flex flex-wrap gap-2">
                {selectedAgent.expertise.map((skill, index) => (
                  <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-2xl font-bold text-blue-600">{selectedAgent.task_count}</div>
              <div className="text-sm text-gray-600">Total Tasks</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-2xl font-bold text-green-600">{selectedAgent.completed_tasks}</div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-2xl font-bold text-purple-600">
                {selectedAgent.task_count > 0
                  ? Math.round((selectedAgent.completed_tasks / selectedAgent.task_count) * 100)
                  : 0}%
              </div>
              <div className="text-sm text-gray-600">Success Rate</div>
            </div>
          </div>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-bold mb-4">Tasks Handled by {selectedAgent.name}</h3>
          
          {agentTasks.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No tasks assigned yet.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agentTasks.map(task => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onViewDetails={handleViewTaskDetails}
                  onRetry={retryTask}
                  onDelete={deleteTask}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  // Apple Silicon Tab
  const renderAppleSilicon = () => (
    <div className="space-y-6">
      <AppleSiliconDashboard />
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600">Loading VirtuAI Office...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* PWA Install Banner */}
      <PWAInstallBanner />

      {/* Onboarding */}
      {showOnboarding && (
        <OnboardingWizard onComplete={handleOnboardingComplete} />
      )}

      {/* Header */}
      <header className="dashboard-header bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-900">🤖 VirtuAI Office</h1>
            <span className="ml-3 px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm font-medium">
              Your AI Development Team
            </span>
          </div>
          
          <nav className="flex space-x-1">
            {[
              { id: 'dashboard', label: '🏠 Dashboard' },
              { id: 'agents', label: '🤖 Agents' },
              { id: 'tasks', label: '📋 Tasks' },
              { id: 'apple-silicon', label: '🍎 Apple Silicon' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="boss-ai-section">
          {activeTab === 'dashboard' && renderDashboard()}
          {activeTab === 'agents' && renderAgents()}
          {activeTab === 'tasks' && renderTasks()}
          {activeTab === 'agent-detail' && renderAgentDetail()}
          {activeTab === 'apple-silicon' && renderAppleSilicon()}
        </div>
      </main>

      {/* Modals */}
      <CreateTaskModal
        isOpen={showCreateTask}
        onClose={() => setShowCreateTask(false)}
        onSubmit={createTask}
        projects={projects}
      />

      <TaskDetailsModal
        task={selectedTask}
        isOpen={showTaskDetails}
        onClose={() => setShowTaskDetails(false)}
      />

      <StandupModal
        isOpen={showStandup}
        onClose={() => setShowStandup(false)}
      />

      {/* Tutorial and Help Systems */}
      <TutorialSystem />
      <HelpSystem />
    </div>
  );
}

export default App;
