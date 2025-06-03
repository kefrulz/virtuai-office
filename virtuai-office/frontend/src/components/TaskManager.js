import React, { useState, useEffect, useRef } from 'react';
import { useNotifications } from './NotificationSystem';

const API_BASE = 'http://localhost:8000';

// Task status colors and icons
const STATUS_CONFIG = {
  pending: { color: 'bg-yellow-100 text-yellow-800', icon: '⏳', label: 'Pending' },
  in_progress: { color: 'bg-blue-100 text-blue-800', icon: '🔄', label: 'In Progress' },
  completed: { color: 'bg-green-100 text-green-800', icon: '✅', label: 'Completed' },
  failed: { color: 'bg-red-100 text-red-800', icon: '❌', label: 'Failed' }
};

const PRIORITY_CONFIG = {
  low: { color: 'bg-gray-100 text-gray-600', icon: '⬇️' },
  medium: { color: 'bg-blue-100 text-blue-600', icon: '➡️' },
  high: { color: 'bg-orange-100 text-orange-600', icon: '⬆️' },
  urgent: { color: 'bg-red-100 text-red-600', icon: '🔥' }
};

// Task Card Component
const TaskCard = ({ task, onViewDetails, onRetry, onDelete, onEdit }) => {
  const formatDate = (dateString) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleString();
  };

  const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  const statusConfig = STATUS_CONFIG[task.status] || STATUS_CONFIG.pending;
  const priorityConfig = PRIORITY_CONFIG[task.priority] || PRIORITY_CONFIG.medium;

  const getDurationText = () => {
    if (task.status === 'completed' && task.started_at && task.completed_at) {
      const start = new Date(task.started_at);
      const end = new Date(task.completed_at);
      const duration = Math.round((end - start) / 1000 / 60); // minutes
      return `${duration}m`;
    }
    if (task.status === 'in_progress' && task.started_at) {
      const start = new Date(task.started_at);
      const now = new Date();
      const duration = Math.round((now - start) / 1000 / 60); // minutes
      return `${duration}m`;
    }
    return null;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-all duration-200 card-hover">
      <div className="flex justify-between items-start mb-3">
        <h3 className="font-semibold text-gray-900 flex-1 pr-2 cursor-pointer hover:text-blue-600"
            onClick={() => onViewDetails(task)}>
          {task.title}
        </h3>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusConfig.color}`}>
            {statusConfig.icon} {statusConfig.label}
          </span>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityConfig.color}`}>
            {priorityConfig.icon} {task.priority}
          </span>
        </div>
      </div>
      
      <p className="text-gray-600 text-sm mb-3 leading-relaxed">
        {truncateText(task.description)}
      </p>
      
      {/* Agent and Progress Info */}
      <div className="flex items-center justify-between mb-3">
        {task.agent_name ? (
          <div className="flex items-center text-sm">
            <span className="text-lg mr-2">🤖</span>
            <span className="font-medium text-gray-700">{task.agent_name}</span>
          </div>
        ) : (
          <div className="flex items-center text-sm text-gray-500">
            <span className="text-lg mr-2">⏳</span>
            <span>Assigning agent...</span>
          </div>
        )}
        
        {getDurationText() && (
          <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
            {getDurationText()}
          </div>
        )}
      </div>
      
      {/* Progress Bar for In Progress Tasks */}
      {task.status === 'in_progress' && (
        <div className="mb-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
          </div>
          <p className="text-xs text-gray-500 mt-1">Processing...</p>
        </div>
      )}
      
      {/* Effort Information */}
      {(task.estimated_effort || task.actual_effort) && (
        <div className="flex justify-between text-xs text-gray-500 mb-3">
          {task.estimated_effort && (
            <span>Est: {task.estimated_effort}h</span>
          )}
          {task.actual_effort && (
            <span>Actual: {task.actual_effort}h</span>
          )}
        </div>
      )}
      
      {/* Timestamps */}
      <div className="text-xs text-gray-500 mb-3 space-y-1">
        <div>Created: {formatDate(task.created_at)}</div>
        {task.started_at && <div>Started: {formatDate(task.started_at)}</div>}
        {task.completed_at && <div>Completed: {formatDate(task.completed_at)}</div>}
      </div>
      
      {/* Action Buttons */}
      <div className="flex justify-between items-center">
        <button
          onClick={() => onViewDetails(task)}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
        >
          View Details
        </button>
        
        <div className="flex space-x-2">
          {task.status !== 'in_progress' && (
            <button
              onClick={() => onEdit(task)}
              className="text-gray-600 hover:text-gray-800 text-sm font-medium transition-colors"
            >
              Edit
            </button>
          )}
          
          {task.status === 'failed' && (
            <button
              onClick={() => onRetry(task.id)}
              className="text-orange-600 hover:text-orange-800 text-sm font-medium transition-colors"
            >
              Retry
            </button>
          )}
          
          {task.status !== 'in_progress' && (
            <button
              onClick={() => onDelete(task.id)}
              className="text-red-600 hover:text-red-800 text-sm font-medium transition-colors"
            >
              Delete
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Task Creation/Edit Modal
const TaskModal = ({ isOpen, onClose, onSubmit, projects, task = null, agents = [] }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    project_id: '',
    agent_id: ''
  });
  
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (task) {
      setFormData({
        title: task.title || '',
        description: task.description || '',
        priority: task.priority || 'medium',
        project_id: task.project_id || '',
        agent_id: task.agent_id || ''
      });
    } else {
      setFormData({
        title: '',
        description: '',
        priority: 'medium',
        project_id: '',
        agent_id: ''
      });
    }
    setErrors({});
  }, [task, isOpen]);

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    } else if (formData.title.length < 3) {
      newErrors.title = 'Title must be at least 3 characters';
    }
    
    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    } else if (formData.description.length < 10) {
      newErrors.description = 'Description must be at least 10 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsSubmitting(true);
    try {
      await onSubmit(formData);
      setFormData({ title: '', description: '', priority: 'medium', project_id: '', agent_id: '' });
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 modal-overlay">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-fade-in">
        <h2 className="text-xl font-bold mb-4">
          {task ? 'Edit Task' : 'Create New Task'}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Task Title *
            </label>
            <input
              type="text"
              required
              className={`w-full p-3 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors ${
                errors.title ? 'border-red-500 bg-red-50' : 'border-gray-300'
              }`}
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              placeholder="e.g., Create user login page with validation"
              maxLength={200}
            />
            {errors.title && (
              <p className="text-red-600 text-sm mt-1">{errors.title}</p>
            )}
            <p className="text-gray-500 text-xs mt-1">
              {formData.title.length}/200 characters
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description *
            </label>
            <textarea
              required
              rows="6"
              className={`w-full p-3 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors resize-vertical ${
                errors.description ? 'border-red-500 bg-red-50' : 'border-gray-300'
              }`}
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Describe what you need in detail. Include requirements, constraints, and expected outcomes..."
            />
            {errors.description && (
              <p className="text-red-600 text-sm mt-1">{errors.description}</p>
            )}
            <p className="text-gray-500 text-xs mt-1">
              Be specific for better results. The more detail you provide, the better your AI team can help.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priority
              </label>
              <select
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={formData.priority}
                onChange={(e) => setFormData({...formData, priority: e.target.value})}
              >
                <option value="low">🔽 Low</option>
                <option value="medium">➡️ Medium</option>
                <option value="high">🔼 High</option>
                <option value="urgent">🔥 Urgent</option>
              </select>
            </div>
            
            {projects.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project (Optional)
                </label>
                <select
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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

          {agents.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Assign to Agent (Optional)
              </label>
              <select
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={formData.agent_id}
                onChange={(e) => setFormData({...formData, agent_id: e.target.value})}
              >
                <option value="">🧠 Let Boss AI decide (recommended)</option>
                {agents.map(agent => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name} - {agent.type.replace('_', ' ')}
                  </option>
                ))}
              </select>
              <p className="text-gray-500 text-xs mt-1">
                Boss AI will automatically assign the best agent based on the task requirements
              </p>
            </div>
          )}
          
          {/* Task Tips */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-800 mb-2">💡 Tips for great results:</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Be specific about requirements and constraints</li>
              <li>• Include context about your project or use case</li>
              <li>• Mention any technical preferences (frameworks, styles, etc.)</li>
              <li>• Break complex tasks into smaller, focused pieces</li>
            </ul>
          </div>
          
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
            >
              {isSubmitting && <div className="loading-spinner mr-2"></div>}
              {isSubmitting ? 'Creating...' : (task ? 'Update Task' : 'Create Task')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Task Details Modal
const TaskDetailsModal = ({ task, isOpen, onClose, onEdit, onRetry, onDelete }) => {
  const formatDate = (dateString) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleString();
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!');
    });
  };

  if (!isOpen || !task) return null;

  const statusConfig = STATUS_CONFIG[task.status] || STATUS_CONFIG.pending;
  const priorityConfig = PRIORITY_CONFIG[task.priority] || PRIORITY_CONFIG.medium;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 modal-overlay">
      <div className="bg-white rounded-lg w-full max-w-5xl max-h-[90vh] overflow-y-auto animate-fade-in">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-900">{task.title}</h2>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => onEdit(task)}
              className="text-gray-600 hover:text-gray-800 text-sm font-medium"
            >
              Edit
            </button>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-xl"
            >
              ×
            </button>
          </div>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            {/* Task Information */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">📋 Task Information</h3>
              <div className="space-y-3">
                <div className="flex items-center">
                  <span className="font-medium text-gray-700 w-24">Status:</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusConfig.color}`}>
                    {statusConfig.icon} {statusConfig.label}
                  </span>
                </div>
                <div className="flex items-center">
                  <span className="font-medium text-gray-700 w-24">Priority:</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${priorityConfig.color}`}>
                    {priorityConfig.icon} {task.priority}
                  </span>
                </div>
                <div className="flex items-start">
                  <span className="font-medium text-gray-700 w-24">Created:</span>
                  <span className="text-gray-600">{formatDate(task.created_at)}</span>
                </div>
                {task.started_at && (
                  <div className="flex items-start">
                    <span className="font-medium text-gray-700 w-24">Started:</span>
                    <span className="text-gray-600">{formatDate(task.started_at)}</span>
                  </div>
                )}
                {task.completed_at && (
                  <div className="flex items-start">
                    <span className="font-medium text-gray-700 w-24">Completed:</span>
                    <span className="text-gray-600">{formatDate(task.completed_at)}</span>
                  </div>
                )}
                {task.actual_effort && (
                  <div className="flex items-start">
                    <span className="font-medium text-gray-700 w-24">Effort:</span>
                    <span className="text-gray-600">{task.actual_effort} hours</span>
                  </div>
                )}
              </div>
            </div>
            
            {/* Agent Information */}
            {task.agent_name && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">🤖 Assigned Agent</h3>
                <div className="flex items-center p-4 bg-gray-50 rounded-lg">
                  <span className="text-3xl mr-4">🤖</span>
                  <div>
                    <div className="font-semibold text-gray-900">{task.agent_name}</div>
                    <div className="text-sm text-gray-600">
                      {task.agent_id ? task.agent_id.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'AI Agent'}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Task Description */}
          <div className="mb-8">
            <h3 className="font-semibold text-gray-900 mb-4">📝 Description</h3>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{task.description}</p>
            </div>
          </div>
          
          {/* AI Generated Output */}
          {task.output && (
            <div className="mb-8">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-gray-900">🎯 AI Generated Output</h3>
                <button
                  onClick={() => copyToClipboard(task.output)}
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center"
                >
                  📋 Copy Output
                </button>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto">
                <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono leading-relaxed">
                  {task.output}
                </pre>
              </div>
            </div>
          )}
          
          {/* Action Buttons */}
          <div className="flex justify-between items-center pt-6 border-t border-gray-200">
            <div className="flex space-x-3">
              {task.status === 'failed' && (
                <button
                  onClick={() => onRetry(task.id)}
                  className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors"
                >
                  🔄 Retry Task
                </button>
              )}
              <button
                onClick={() => onEdit(task)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                ✏️ Edit Task
              </button>
            </div>
            
            {task.status !== 'in_progress' && (
              <button
                onClick={() => {
                  if (window.confirm('Are you sure you want to delete this task?')) {
                    onDelete(task.id);
                    onClose();
                  }
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              >
                🗑️ Delete Task
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Filters Component
const TaskFilters = ({ filters, onFiltersChange, projects, agents, taskCounts }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
          <select
            value={filters.status}
            onChange={(e) => onFiltersChange({...filters, status: e.target.value})}
            className="w-full p-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="">All Statuses ({taskCounts.total})</option>
            <option value="pending">Pending ({taskCounts.pending})</option>
            <option value="in_progress">In Progress ({taskCounts.in_progress})</option>
            <option value="completed">Completed ({taskCounts.completed})</option>
            <option value="failed">Failed ({taskCounts.failed})</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
          <select
            value={filters.priority}
            onChange={(e) => onFiltersChange({...filters, priority: e.target.value})}
            className="w-full p-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="">All Priorities</option>
            <option value="urgent">🔥 Urgent</option>
            <option value="high">🔼 High</option>
            <option value="medium">➡️ Medium</option>
            <option value="low">🔽 Low</option>
          </select>
        </div>
        
        {projects.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Project</label>
            <select
              value={filters.project_id}
              onChange={(e) => onFiltersChange({...filters, project_id: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="">All Projects</option>
              {projects.map(project => (
                <option key={project.id} value={project.id}>{project.name}</option>
              ))}
            </select>
          </div>
        )}
        
        {agents.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Agent</label>
            <select
              value={filters.agent_id}
              onChange={(e) => onFiltersChange({...filters, agent_id: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="">All Agents</option>
              {agents.map(agent => (
                <option key={agent.id} value={agent.id}>{agent.name}</option>
              ))}
            </select>
          </div>
        )}
      </div>
      
      {/* Search */}
      <div className="mt-4">
        <input
          type="text"
          placeholder="Search tasks by title or description..."
          value={filters.search}
          onChange={(e) => onFiltersChange({...filters, search: e.target.value})}
          className="w-full p-2 border border-gray-300 rounded-md text-sm"
        />
      </div>
      
      {/* Clear Filters */}
      {(filters.status || filters.priority || filters.project_id || filters.agent_id || filters.search) && (
        <div className="mt-4">
          <button
            onClick={() => onFiltersChange({ status: '', priority: '', project_id: '', agent_id: '', search: '' })}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            Clear all filters
          </button>
        </div>
      )}
    </div>
  );
};

// Main TaskManager Component
const TaskManager = () => {
  const [tasks, setTasks] = useState([]);
  const [projects, setProjects] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    project_id: '',
    agent_id: '',
    search: ''
  });
  
  const { addNotification } = useNotifications();
  const wsRef = useRef(null);

  // Load data
  useEffect(() => {
    loadTasks();
    loadProjects();
    loadAgents();
    setupWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const setupWebSocket = () => {
    try {
      wsRef.current = new WebSocket('ws://localhost:8000/ws');
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.log('WebSocket message:', event.data);
        }
      };
      
      wsRef.current.onopen = () => {
        console.log('TaskManager WebSocket connected');
      };
      
      wsRef.current.onclose = () => {
        console.log('TaskManager WebSocket disconnected');
        setTimeout(setupWebSocket, 5000);
      };
      
    } catch (error) {
      console.error('WebSocket setup failed:', error);
    }
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'task_update':
        addNotification(`Task ${data.task_id} status updated to ${data.status}`, 'info');
        loadTasks();
        break;
      case 'task_completed':
        addNotification(`${data.agent_name} completed a task!`, 'success');
        loadTasks();
        break;
      case 'task_failed':
        addNotification(`Task ${data.task_id} failed: ${data.error}`, 'error');
        loadTasks();
        break;
    }
  };

  const loadTasks = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/tasks`);
      const data = await response.json();
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
      addNotification('Failed to load tasks', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadProjects = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/projects`);
      const data = await response.json();
      setProjects(data);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const loadAgents = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/agents`);
      const data = await response.json();
      setAgents(data);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const createTask = async (taskData) => {
    try {
      const response = await fetch(`${API_BASE}/api/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      addNotification('Task created successfully!', 'success');
      setShowCreateModal(false);
      loadTasks();
    } catch (error) {
      console.error('Failed to create task:', error);
      addNotification('Failed to create task', 'error');
      throw error;
    }
  };

  const updateTask = async (taskData) => {
    try {
      const response = await fetch(`${API_BASE}/api/tasks/${selectedTask.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      addNotification('Task updated successfully!', 'success');
      setShowEditModal(false);
      setSelectedTask(null);
      loadTasks();
    } catch (error) {
      console.error('Failed to update task:', error);
      addNotification('Failed to update task', 'error');
      throw error;
    }
  };

  const retryTask = async (taskId) => {
    try {
      const response = await fetch(`${API_BASE}/api/tasks/${taskId}/retry`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
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
      const response = await fetch(`${API_BASE}/api/tasks/${taskId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      addNotification('Task deleted successfully', 'success');
      loadTasks();
    } catch (error) {
      console.error('Failed to delete task:', error);
      addNotification('Failed to delete task', 'error');
    }
  };

  const handleViewDetails = (task) => {
    setSelectedTask(task);
    setShowDetailsModal(true);
  };

  const handleEditTask = (task) => {
    setSelectedTask(task);
    setShowEditModal(true);
  };

  // Filter and search tasks
  const filteredTasks = tasks.filter(task => {
    if (filters.status && task.status !== filters.status) return false;
    if (filters.priority && task.priority !== filters.priority) return false;
    if (filters.project_id && task.project_id !== filters.project_id) return false;
    if (filters.agent_id && task.agent_id !== filters.agent_id) return false;
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      if (!task.title.toLowerCase().includes(searchLower) &&
          !task.description.toLowerCase().includes(searchLower)) {
        return false;
      }
    }
    return true;
  });

  // Calculate task counts
  const taskCounts = {
    total: tasks.length,
    pending: tasks.filter(t => t.status === 'pending').length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    failed: tasks.filter(t => t.status === 'failed').length
  };

  // Sort tasks by priority and creation date
  const sortedTasks = [...filteredTasks].sort((a, b) => {
    const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
    if (priorityOrder[a.priority] !== priorityOrder[b.priority]) {
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    }
    return new Date(b.created_at) - new Date(a.created_at);
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="loading-spinner mr-3"></div>
        <span>Loading tasks...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">📋 Task Management</h2>
          <p className="text-gray-600 mt-1">
            Manage and track your AI development team's work
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center"
        >
          ✨ New Task
        </button>
      </div>

      {/* Task Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-gray-900">{taskCounts.total}</div>
          <div className="text-sm text-gray-600">Total Tasks</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-yellow-600">{taskCounts.pending}</div>
          <div className="text-sm text-gray-600">Pending</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-600">{taskCounts.in_progress}</div>
          <div className="text-sm text-gray-600">In Progress</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600">{taskCounts.completed}</div>
          <div className="text-sm text-gray-600">Completed</div>
        </div>
      </div>

      {/* Filters */}
      <TaskFilters
        filters={filters}
        onFiltersChange={setFilters}
        projects={projects}
        agents={agents}
        taskCounts={taskCounts}
      />

      {/* Tasks Grid */}
      {sortedTasks.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <div className="text-4xl mb-4">🤖</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {tasks.length === 0 ? 'No tasks yet' : 'No tasks match your filters'}
          </h3>
          <p className="text-gray-600 mb-6">
            {tasks.length === 0
              ? 'Create your first task to get your AI development team started!'
              : 'Try adjusting your filters or search terms.'
            }
          </p>
          {tasks.length === 0 && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              ✨ Create Your First Task
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedTasks.map(task => (
            <TaskCard
              key={task.id}
              task={task}
              onViewDetails={handleViewDetails}
              onRetry={retryTask}
              onDelete={deleteTask}
              onEdit={handleEditTask}
            />
          ))}
        </div>
      )}

      {/* Results count */}
      {filteredTasks.length !== tasks.length && (
        <div className="text-center text-gray-500 text-sm">
          Showing {filteredTasks.length} of {tasks.length} tasks
        </div>
      )}

      {/* Modals */}
      <TaskModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={createTask}
        projects={projects}
        agents={agents}
      />

      <TaskModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedTask(null);
        }}
        onSubmit={updateTask}
        projects={projects}
        agents={agents}
        task={selectedTask}
      />

      <TaskDetailsModal
        task={selectedTask}
        isOpen={showDetailsModal}
        onClose={() => {
          setShowDetailsModal(false);
          setSelectedTask(null);
        }}
        onEdit={handleEditTask}
        onRetry={retryTask}
        onDelete={deleteTask}
      />
    </div>
  );
};

export default TaskManager;
