import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

const BossAIDashboard = () => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeCollaborations, setActiveCollaborations] = useState([]);
  const [workloadOptimizing, setWorkloadOptimizing] = useState(false);
  const [performanceData, setPerformanceData] = useState(null);

  useEffect(() => {
    loadBossInsights();
    loadActiveCollaborations();
    loadPerformanceData();
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

  const loadPerformanceData = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/analytics`);
      const data = await response.json();
      setPerformanceData(data);
    } catch (error) {
      console.error('Failed to load performance data:', error);
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

  const generateStandup = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/standup`, {
        method: 'POST'
      });
      const result = await response.json();
      
      // Update insights with new standup data
      setInsights(prev => ({ ...prev, standup: result }));
    } catch (error) {
      console.error('Failed to generate standup:', error);
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
              onClick={generateStandup}
              className="bg-white bg-opacity-20 text-white px-4 py-2 rounded-md hover:bg-opacity-30 font-medium"
            >
              📊 Generate Standup
            </button>
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

      {/* Team Performance Overview */}
      {performanceData && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="text-lg font-bold mb-4">📈 Team Performance Overview</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {performanceData.total_tasks}
              </div>
              <div className="text-sm text-blue-700">Total Tasks</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {performanceData.completed_tasks}
              </div>
              <div className="text-sm text-green-700">Completed</div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">
                {performanceData.in_progress_tasks}
              </div>
              <div className="text-sm text-yellow-700">In Progress</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {Math.round(performanceData.completion_rate * 100)}%
              </div>
              <div className="text-sm text-purple-700">Success Rate</div>
            </div>
          </div>

          {/* Agent Performance Grid */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Agent Performance</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {performanceData.agent_performance?.map((agent, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="font-medium">{agent.agent_name}</h5>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      agent.completion_rate >= 0.8 ? 'bg-green-100 text-green-800' :
                      agent.completion_rate >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {Math.round(agent.completion_rate * 100)}%
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    <div>{agent.completed_tasks} / {agent.total_tasks} tasks</div>
                    <div>{agent.avg_effort_hours}h avg effort</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

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

      {/* Boss AI Status */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-bold mb-4">🤖 Boss AI Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">Active</div>
            <div className="text-sm text-green-700">System Status</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {insights?.recent_decisions?.length || 0}
            </div>
            <div className="text-sm text-blue-700">Recent Decisions</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {Math.round((performanceData?.completion_rate || 0) * 100)}%
            </div>
            <div className="text-sm text-purple-700">Team Efficiency</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BossAIDashboard;
