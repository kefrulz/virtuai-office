import React, { useState, useEffect } from 'react';
import { useNotifications } from './NotificationSystem';

const TaskDetails = ({ task, isOpen, onClose, onRetry, onDelete, onUpdate }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedTask, setEditedTask] = useState({});
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const { addNotification } = useNotifications();

  useEffect(() => {
    if (task) {
      setEditedTask({
        title: task.title || '',
        description: task.description || '',
        priority: task.priority || 'medium'
      });
    }
  }, [task]);

  if (!isOpen || !task) return null;

  const formatDate = (dateString) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      in_progress: 'bg-blue-100 text-blue-800 border-blue-300',
      completed: 'bg-green-100 text-green-800 border-green-300',
      failed: 'bg-red-100 text-red-800 border-red-300'
    };
    return colors[status] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: 'bg-gray-100 text-gray-600',
      medium: 'bg-blue-100 text-blue-600',
      high: 'bg-orange-100 text-orange-600',
      urgent: 'bg-red-100 text-red-600'
    };
    return colors[priority] || 'bg-gray-100 text-gray-600';
  };

  const getAgentIcon = (agentType) => {
    const icons = {
      product_manager: '👩‍💼',
      frontend_developer: '👨‍💻',
      backend_developer: '👩‍💻',
      ui_ux_designer: '🎨',
      qa_tester: '🔍'
    };
    return icons[agentType] || '🤖';
  };

  const handleSave = async () => {
    try {
      if (onUpdate) {
        await onUpdate(task.id, editedTask);
        addNotification('Task updated successfully', 'success');
        setIsEditing(false);
      }
    } catch (error) {
      addNotification('Failed to update task', 'error');
    }
  };

  const handleRetry = async () => {
    try {
      if (onRetry) {
        await onRetry(task.id);
        addNotification('Task queued for retry', 'success');
      }
    } catch (error) {
      addNotification('Failed to retry task', 'error');
    }
  };

  const handleDelete = async () => {
    try {
      if (onDelete) {
        await onDelete(task.id);
        addNotification('Task deleted successfully', 'success');
        onClose();
      }
    } catch (error) {
      addNotification('Failed to delete task', 'error');
    }
    setShowDeleteConfirm(false);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      addNotification('Copied to clipboard', 'success');
    }).catch(() => {
      addNotification('Failed to copy to clipboard', 'error');
    });
  };

  const downloadOutput = () => {
    if (!task.output) return;
    
    const blob = new Blob([task.output], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${task.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_output.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    addNotification('Output downloaded', 'success');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-start p-6 border-b border-gray-200">
          <div className="flex-1 pr-4">
            {isEditing ? (
              <input
                type="text"
                value={editedTask.title}
                onChange={(e) => setEditedTask({...editedTask, title: e.target.value})}
                className="text-xl font-bold w-full p-2 border border-gray-300 rounded-md"
                placeholder="Task title"
              />
            ) : (
              <h2 className="text-xl font-bold text-gray-900">{task.title}</h2>
            )}
            
            <div className="flex items-center space-x-2 mt-2">
              <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(task.status)}`}>
                {task.status.replace('_', ' ').toUpperCase()}
              </span>
              {isEditing ? (
                <select
                  value={editedTask.priority}
                  onChange={(e) => setEditedTask({...editedTask, priority: e.target.value})}
                  className="px-2 py-1 rounded-full text-xs font-medium border border-gray-300"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              ) : (
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(task.priority)}`}>
                  {task.priority.toUpperCase()}
                </span>
              )}
              <span className="text-xs text-gray-500">
                Created {formatDate(task.created_at)}
              </span>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {task.status !== 'in_progress' && (
              <>
                {isEditing ? (
                  <>
                    <button
                      onClick={handleSave}
                      className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setIsEditing(false)}
                      className="px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 text-sm"
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                    title="Edit Task"
                  >
                    ✏️ Edit
                  </button>
                )}
              </>
            )}
            
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-xl p-1"
              title="Close"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Task Information Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left Column */}
            <div className="space-y-4">
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Description</h3>
                {isEditing ? (
                  <textarea
                    value={editedTask.description}
                    onChange={(e) => setEditedTask({...editedTask, description: e.target.value})}
                    rows="6"
                    className="w-full p-3 border border-gray-300 rounded-md resize-none"
                    placeholder="Task description"
                  />
                ) : (
                  <div className="p-3 bg-gray-50 rounded-md">
                    <p className="text-gray-700 whitespace-pre-wrap">{task.description}</p>
                  </div>
                )}
              </div>

              {/* Timestamps */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-3">Timeline</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Created:</span>
                    <span className="font-mono">{formatDate(task.created_at)}</span>
                  </div>
                  {task.started_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Started:</span>
                      <span className="font-mono">{formatDate(task.started_at)}</span>
                    </div>
                  )}
                  {task.completed_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Completed:</span>
                      <span className="font-mono">{formatDate(task.completed_at)}</span>
                    </div>
                  )}
                  {task.actual_effort && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Effort:</span>
                      <span>{task.actual_effort} hours</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-4">
              {/* Assigned Agent */}
              {task.agent_name && (
                <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                  <h4 className="font-medium text-blue-800 mb-3">Assigned Agent</h4>
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">
                      {getAgentIcon(task.agent_type)}
                    </span>
                    <div>
                      <div className="font-medium text-blue-900">{task.agent_name}</div>
                      <div className="text-sm text-blue-700">
                        {task.agent_type ? task.agent_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'AI Agent'}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Project Information */}
              {task.project_name && (
                <div className="bg-purple-50 border border-purple-200 p-4 rounded-lg">
                  <h4 className="font-medium text-purple-800 mb-2">Project</h4>
                  <div className="text-purple-900 font-medium">{task.project_name}</div>
                </div>
              )}

              {/* Performance Metrics */}
              {(task.estimated_effort || task.actual_effort) && (
                <div className="bg-gray-50 border border-gray-200 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-800 mb-3">Performance</h4>
                  <div className="space-y-2 text-sm">
                    {task.estimated_effort && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Estimated:</span>
                        <span>{task.estimated_effort}h</span>
                      </div>
                    )}
                    {task.actual_effort && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Actual:</span>
                        <span>{task.actual_effort}h</span>
                      </div>
                    )}
                    {task.estimated_effort && task.actual_effort && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Efficiency:</span>
                        <span className={
                          task.actual_effort <= task.estimated_effort
                            ? 'text-green-600 font-medium'
                            : 'text-orange-600 font-medium'
                        }>
                          {Math.round((task.estimated_effort / task.actual_effort) * 100)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* AI Generated Output */}
          {task.output && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium text-gray-900">AI Generated Output</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => copyToClipboard(task.output)}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                    title="Copy to clipboard"
                  >
                    📋 Copy
                  </button>
                  <button
                    onClick={downloadOutput}
                    className="text-sm text-green-600 hover:text-green-800 font-medium"
                    title="Download output"
                  >
                    💾 Download
                  </button>
                  <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="text-sm text-purple-600 hover:text-purple-800 font-medium"
                  >
                    {isExpanded ? '📐 Collapse' : '📏 Expand'}
                  </button>
                </div>
              </div>
              
              <div className={`bg-gray-50 border border-gray-200 rounded-lg p-4 ${isExpanded ? '' : 'max-h-96'} overflow-y-auto`}>
                <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono leading-relaxed">
                  {task.output}
                </pre>
              </div>
            </div>
          )}

          {/* Error Information */}
          {task.status === 'failed' && task.error_message && (
            <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
              <h4 className="font-medium text-red-800 mb-2">Error Details</h4>
              <div className="text-red-700 text-sm font-mono bg-red-100 p-3 rounded">
                {task.error_message}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="border-t border-gray-200 p-6">
          <div className="flex justify-between items-center">
            <div className="flex space-x-2">
              {task.status === 'failed' && (
                <button
                  onClick={handleRetry}
                  className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors"
                >
                  🔄 Retry Task
                </button>
              )}
              
              {task.status !== 'in_progress' && (
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                >
                  🗑️ Delete Task
                </button>
              )}
            </div>
            
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors"
            >
              Close
            </button>
          </div>
        </div>

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-bold text-gray-900 mb-2">Delete Task</h3>
              <p className="text-gray-700 mb-4">
                Are you sure you want to delete "{task.title}"? This action cannot be undone.
              </p>
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskDetails;
