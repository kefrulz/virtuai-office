import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

const AgentPerformanceDashboard = ({ agentId, agentName, onClose }) => {
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (agentId) {
      loadAgentPerformance();
    }
  }, [agentId]);

  const loadAgentPerformance = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE}/api/agents/${agentId}/performance`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setPerformance(data);
    } catch (error) {
      console.error('Failed to load agent performance:', error);
      setError('Failed to load performance data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
            Loading performance data...
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md">
          <div className="text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Data</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <div className="flex space-x-3">
              <button
                onClick={loadAgentPerformance}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Try Again
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!performance) {
    return null;
  }

  const getPerformanceColor = (score) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPerformanceLabel = (score) => {
    if (score >= 0.8) return 'Excellent';
    if (score >= 0.6) return 'Good';
    return 'Needs Improvement';
  };

  const getPerformanceBgColor = (score) => {
    if (score >= 0.8) return 'from-green-50 to-green-100';
    if (score >= 0.6) return 'from-yellow-50 to-yellow-100';
    return 'from-red-50 to-red-100';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-5xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">
            📊 {agentName} Performance Analytics
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
          >
            ×
          </button>
        </div>

        {/* Performance Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className={`bg-gradient-to-br ${getPerformanceBgColor(performance.performance.performance_score)} p-6 rounded-lg`}>
            <div className="text-3xl font-bold text-gray-800">
              {Math.round(performance.performance.performance_score * 100)}%
            </div>
            <div className="text-sm text-gray-700 font-medium">Overall Performance</div>
            <div className={`text-xs mt-2 font-semibold ${getPerformanceColor(performance.performance.performance_score)}`}>
              {getPerformanceLabel(performance.performance.performance_score)}
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-lg">
            <div className="text-3xl font-bold text-green-600">
              {Math.round(performance.performance.efficiency * 100)}%
            </div>
            <div className="text-sm text-green-700 font-medium">Efficiency</div>
            <div className="text-xs text-green-600 mt-2 font-medium">Time Management</div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-lg">
            <div className="text-3xl font-bold text-purple-600">
              {Math.round(performance.performance.quality * 100)}%
            </div>
            <div className="text-sm text-purple-700 font-medium">Output Quality</div>
            <div className="text-xs text-purple-600 mt-2 font-medium">Content Assessment</div>
          </div>

          <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-6 rounded-lg">
            <div className="text-3xl font-bold text-orange-600">
              {performance.collaboration_count}
            </div>
            <div className="text-sm text-orange-700 font-medium">Collaborations</div>
            <div className="text-xs text-orange-600 mt-2 font-medium">Team Projects</div>
          </div>
        </div>

        {/* Detailed Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          {/* Performance Breakdown */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-bold mb-4">📈 Performance Breakdown</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Task Completion Rate</span>
                  <span className="font-medium">{Math.round(performance.performance.performance_score * 100)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${performance.performance.performance_score * 100}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Efficiency Score</span>
                  <span className="font-medium">{Math.round(performance.performance.efficiency * 100)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${performance.performance.efficiency * 100}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Quality Score</span>
                  <span className="font-medium">{Math.round(performance.performance.quality * 100)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-purple-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${performance.performance.quality * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-bold mb-4">🎯 Key Metrics</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Tasks Analyzed</span>
                <span className="font-medium text-gray-900">{performance.performance.tasks_analyzed}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Avg Completion Time</span>
                <span className="font-medium text-gray-900">{performance.performance.avg_completion_time}h</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Collaboration Projects</span>
                <span className="font-medium text-gray-900">{performance.collaboration_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Agent Type</span>
                <span className="font-medium text-gray-900 capitalize">
                  {performance.agent.type.replace('_', ' ')}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Task Distribution */}
        <div className="mb-8">
          <h3 className="text-lg font-bold mb-4">📋 Task Distribution (Last 30 Days)</h3>
          <div className="bg-gray-50 rounded-lg p-6">
            {Object.keys(performance.task_distribution).length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {Object.entries(performance.task_distribution).map(([type, count]) => (
                  <div key={type} className="text-center">
                    <div className="text-2xl font-bold text-gray-800">{count}</div>
                    <div className="text-sm text-gray-600 capitalize">
                      {type.replace('_', ' ')}
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
                      <div
                        className="bg-blue-600 h-1 rounded-full"
                        style={{
                          width: `${(count / Math.max(...Object.values(performance.task_distribution))) * 100}%`
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                No task distribution data available
              </div>
            )}
          </div>
        </div>

        {/* Recent Tasks */}
        <div className="mb-6">
          <h3 className="text-lg font-bold mb-4">🕒 Recent Completed Tasks</h3>
          <div className="space-y-3">
            {performance.recent_tasks && performance.recent_tasks.length > 0 ? (
              performance.recent_tasks.map(task => (
                <div key={task.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900 mb-1">{task.title}</h4>
                      <div className="text-sm text-gray-600">
                        Completed: {new Date(task.completed_at).toLocaleDateString()} at {new Date(task.completed_at).toLocaleTimeString()}
                      </div>
                    </div>
                    <div className="text-right ml-4">
                      <div className="text-sm font-medium text-blue-600">
                        {task.effort_hours}h
                      </div>
                      <div className="text-xs text-gray-500">Effort</div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">📝</div>
                <p>No recent tasks completed</p>
              </div>
            )}
          </div>
        </div>

        {/* Performance Insights */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h4 className="font-medium text-blue-800 mb-3 flex items-center">
            <span className="mr-2">🎯</span>
            Performance Insights
          </h4>
          <div className="space-y-2 text-sm text-blue-700">
            {performance.performance.tasks_analyzed > 0 ? (
              <>
                <p>• Analyzed {performance.performance.tasks_analyzed} completed tasks</p>
                <p>• Average completion time: {performance.performance.avg_completion_time} hours</p>
                {performance.performance.efficiency > 1.2 && (
                  <p>• 🏆 Consistently delivers faster than estimated</p>
                )}
                {performance.performance.quality > 0.8 && (
                  <p>• ⭐ High-quality output with good structure and examples</p>
                )}
                {performance.collaboration_count > 5 && (
                  <p>• 🤝 Active collaborator in team projects</p>
                )}
                {performance.performance.performance_score > 0.9 && (
                  <p>• 🎉 Outstanding performance - top tier agent!</p>
                )}
                {performance.performance.efficiency < 0.8 && (
                  <p>• 💡 Consider optimizing task complexity for better efficiency</p>
                )}
              </>
            ) : (
              <p>• No completed tasks to analyze yet</p>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end mt-6 space-x-3">
          <button
            onClick={loadAgentPerformance}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors"
          >
            🔄 Refresh Data
          </button>
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default AgentPerformanceDashboard;
