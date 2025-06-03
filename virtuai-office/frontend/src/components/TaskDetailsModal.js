import React, { useState, useEffect } from 'react';

const TaskDetailsModal = ({ task, isOpen, onClose, onRetry, onDelete }) => {
  const [isRetrying, setIsRetrying] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen || !task) return null;

  const formatDate = (dateString) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-100 text-red-600 border-red-300';
      case 'high':
        return 'bg-orange-100 text-orange-600 border-orange-300';
      case 'medium':
        return 'bg-blue-100 text-blue-600 border-blue-300';
      case 'low':
        return 'bg-gray-100 text-gray-600 border-gray-300';
      default:
        return 'bg-gray-100 text-gray-600 border-gray-300';
    }
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

  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      await onRetry(task.id);
      onClose();
    } catch (error) {
      console.error('Failed to retry task:', error);
    } finally {
      setIsRetrying(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this task? This action cannot be undone.')) {
      return;
    }

    setIsDeleting(true);
    try {
      await onDelete(task.id);
      onClose();
    } catch (error) {
      console.error('Failed to delete task:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const calculateDuration = () => {
    if (task.started_at && task.completed_at) {
      const start = new Date(task.started_at);
      const end = new Date(task.completed_at);
      const durationMs = end - start;
      
      const hours = Math.floor(durationMs / (1000 * 60 * 60));
      const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
      
      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      } else {
        return `${minutes}m`;
      }
    }
    
    if (task.started_at && !task.completed_at) {
      const start = new Date(task.started_at);
      const now = new Date();
      const durationMs = now - start;
      
      const hours = Math.floor(durationMs / (1000 * 60 * 60));
      const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
      
      if (hours > 0) {
        return `${hours}h ${minutes}m (ongoing)`;
      } else {
        return `${minutes}m (ongoing)`;
      }
    }
    
    return 'Not started';
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto m-4">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-lg">
          <div className="flex justify-between items-start">
            <div className="flex-1 pr-4">
              <h2 className="text-xl font-bold text-gray-900 mb-2">{task.title}</h2>
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(task.status)}`}>
                  {task.status.replace('_', ' ')}
                </span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(task.priority)}`}>
                  {task.priority}
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 p-2 hover:bg-gray-100 rounded-full"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Task Information Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Left Column - Task Details */}
            <div className="space-y-6">
              <div>
                <h3 className="font-medium text-gray-900 mb-3">Task Information</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(task.status)}`}>
                      {task.status.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Priority:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(task.priority)}`}>
                      {task.priority}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Created:</span>
                    <span className="text-gray-900">{formatDate(task.created_at)}</span>
                  </div>
                  {task.started_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Started:</span>
                      <span className="text-gray-900">{formatDate(task.started_at)}</span>
                    </div>
                  )}
                  {task.completed_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Completed:</span>
                      <span className="text-gray-900">{formatDate(task.completed_at)}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-600">Duration:</span>
                    <span className="text-gray-900">{calculateDuration()}</span>
                  </div>
                  {task.estimated_effort && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Estimated Effort:</span>
                      <span className="text-gray-900">{task.estimated_effort}h</span>
                    </div>
                  )}
                  {task.actual_effort && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Actual Effort:</span>
                      <span className="text-gray-900">{task.actual_effort}h</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Project Information */}
              {task.project_id && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Project</h3>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="text-sm text-blue-800">
                      Project ID: {task.project_id}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right Column - Agent Information */}
            <div className="space-y-6">
              {task.agent_name && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Assigned Agent</h3>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center">
                      <span className="text-3xl mr-3">{getAgentIcon(task.agent_type)}</span>
                      <div>
                        <div className="font-medium text-gray-900">{task.agent_name}</div>
                        <div className="text-sm text-gray-600">
                          {task.agent_type ? task.agent_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'AI Agent'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Performance Metrics */}
              {(task.estimated_effort || task.actual_effort) && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Performance</h3>
                  <div className="space-y-2">
                    {task.estimated_effort && task.actual_effort && (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                        <div className="text-sm">
                          <div className="flex justify-between mb-1">
                            <span className="text-gray-600">Efficiency:</span>
                            <span className={`font-medium ${
                              task.actual_effort <= task.estimated_effort ? 'text-green-600' : 'text-orange-600'
                            }`}>
                              {Math.round((task.estimated_effort / task.actual_effort) * 100)}%
                            </span>
                          </div>
                          <div className="text-xs text-gray-500">
                            {task.actual_effort <= task.estimated_effort
                              ? 'Completed ahead of schedule'
                              : 'Took longer than estimated'
                            }
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Task Description */}
          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-3">Description</h3>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <p className="text-gray-700 whitespace-pre-wrap">{task.description}</p>
            </div>
          </div>

          {/* AI Generated Output */}
          {task.output && (
            <div className="mb-6">
              <h3 className="font-medium text-gray-900 mb-3">AI Generated Output</h3>
              <div className="bg-gray-900 text-gray-100 rounded-lg p-4 max-h-96 overflow-y-auto">
                <pre className="whitespace-pre-wrap text-sm font-mono leading-relaxed">
                  {task.output}
                </pre>
              </div>
              <div className="mt-2 flex justify-end">
                <button
                  onClick={() => navigator.clipboard.writeText(task.output)}
                  className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy to Clipboard
                </button>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-between items-center pt-6 border-t border-gray-200">
            <div className="flex space-x-3">
              {task.status === 'failed' && (
                <button
                  onClick={handleRetry}
                  disabled={isRetrying}
                  className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {isRetrying ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Retrying...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Retry Task
                    </>
                  )}
                </button>
              )}
              
              {task.status !== 'in_progress' && (
                <button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {isDeleting ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Deleting...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Delete Task
                    </>
                  )}
                </button>
              )}
            </div>

            <button
              onClick={onClose}
              className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskDetailsModal;
