import React, { useState, useEffect } from 'react';

const AGENT_COLORS = {
  product_manager: 'bg-purple-100 text-purple-800 border-purple-300',
  frontend_developer: 'bg-blue-100 text-blue-800 border-blue-300',
  backend_developer: 'bg-green-100 text-green-800 border-green-300',
  ui_ux_designer: 'bg-pink-100 text-pink-800 border-pink-300',
  qa_tester: 'bg-orange-100 text-orange-800 border-orange-300',
};

const AGENT_ICONS = {
  product_manager: '👩‍💼',
  frontend_developer: '👨‍💻',
  backend_developer: '👩‍💻',
  ui_ux_designer: '🎨',
  qa_tester: '🔍',
};

const AgentCard = ({ agent, onViewTasks, onViewPerformance, isLoading = false }) => {
  const completionRate = agent.task_count > 0
    ? agent.completed_tasks / agent.task_count
    : 0;

  const getPerformanceIndicator = (rate) => {
    if (rate >= 0.9) return { color: 'bg-green-500', label: 'Excellent' };
    if (rate >= 0.7) return { color: 'bg-yellow-500', label: 'Good' };
    if (rate >= 0.5) return { color: 'bg-orange-500', label: 'Fair' };
    return { color: 'bg-red-500', label: 'Improving' };
  };

  const performance = getPerformanceIndicator(completionRate);
  const currentWorkload = agent.current_workload || 0;

  if (isLoading) {
    return (
      <div className="border rounded-lg p-4 bg-white animate-pulse">
        <div className="flex items-center mb-3">
          <div className="w-12 h-12 bg-gray-200 rounded-full mr-3"></div>
          <div className="flex-1">
            <div className="h-4 bg-gray-200 rounded mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
        <div className="h-3 bg-gray-200 rounded mb-3"></div>
        <div className="h-3 bg-gray-200 rounded mb-3"></div>
        <div className="flex space-x-2">
          <div className="h-8 bg-gray-200 rounded flex-1"></div>
          <div className="h-8 bg-gray-200 rounded flex-1"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`border rounded-lg p-4 bg-white hover:shadow-lg transition-shadow card-hover ${AGENT_COLORS[agent.type] || 'bg-gray-100'}`}>
      {/* Header */}
      <div className="flex items-center mb-3">
        <span className="text-3xl mr-3">{AGENT_ICONS[agent.type] || '🤖'}</span>
        <div className="flex-1">
          <h3 className="font-bold text-lg">{agent.name}</h3>
          <p className="text-sm opacity-75 capitalize">
            {agent.type.replace('_', ' ')}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div
            className={`w-3 h-3 rounded-full ${performance.color}`}
            title={performance.label}
          ></div>
          <span className="text-xs opacity-75">{performance.label}</span>
        </div>
      </div>
      
      {/* Description */}
      <p className="text-sm mb-3 opacity-90 line-clamp-2">{agent.description}</p>
      
      {/* Task Stats */}
      <div className="flex justify-between items-center text-sm mb-3">
        <div>
          <span className="font-medium">{agent.completed_tasks}</span>
          <span className="opacity-75"> / {agent.task_count} tasks</span>
        </div>
        <div className="font-medium">
          {Math.round(completionRate * 100)}% success
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
        <div
          className="bg-current h-2 rounded-full transition-all duration-300"
          style={{ width: `${Math.round(completionRate * 100)}%` }}
        ></div>
      </div>

      {/* Workload Indicator */}
      <div className="mb-3">
        <div className="flex justify-between text-xs opacity-75 mb-1">
          <span>Current Workload</span>
          <span>{currentWorkload}h</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              currentWorkload > 30 ? 'bg-red-500' :
              currentWorkload > 20 ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(currentWorkload / 40 * 100, 100)}%` }}
          ></div>
        </div>
      </div>
      
      {/* Expertise Tags */}
      <div className="mb-4">
        <div className="text-xs opacity-75 mb-1">Expertise:</div>
        <div className="flex flex-wrap gap-1">
          {(agent.expertise || []).slice(0, 3).map((skill, index) => (
            <span key={index} className="text-xs px-2 py-1 bg-white bg-opacity-50 rounded">
              {skill}
            </span>
          ))}
          {(agent.expertise || []).length > 3 && (
            <span className="text-xs px-2 py-1 bg-white bg-opacity-50 rounded">
              +{agent.expertise.length - 3}
            </span>
          )}
        </div>
      </div>

      {/* Status Indicator */}
      <div className="flex items-center mb-4 text-xs">
        <div className={`w-2 h-2 rounded-full mr-2 ${
          agent.is_active ? 'bg-green-500' : 'bg-gray-400'
        }`}></div>
        <span className="opacity-75">
          {agent.is_active ? 'Active' : 'Inactive'}
        </span>
        {currentWorkload > 0 && (
          <span className="ml-auto opacity-75">
            {currentWorkload > 30 ? '🔥 Busy' : currentWorkload > 15 ? '⚡ Working' : '✅ Available'}
          </span>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-2">
        <button
          onClick={() => onViewTasks(agent)}
          className="flex-1 text-current hover:opacity-80 text-sm font-medium py-2 px-3 bg-white bg-opacity-50 hover:bg-opacity-75 rounded transition-all"
        >
          View Tasks
        </button>
        <button
          onClick={() => onViewPerformance(agent)}
          className="flex-1 text-current hover:opacity-80 text-sm font-medium py-2 px-3 bg-white bg-opacity-50 hover:bg-opacity-75 rounded transition-all"
        >
          📊 Analytics
        </button>
      </div>
    </div>
  );
};

const AgentGrid = ({ agents, onViewTasks, onViewPerformance, isLoading = false }) => {
  const [sortBy, setSortBy] = useState('name');
  const [filterActive, setFilterActive] = useState('all');

  const sortedAndFilteredAgents = React.useMemo(() => {
    let filtered = agents;
    
    // Filter by active status
    if (filterActive === 'active') {
      filtered = agents.filter(agent => agent.is_active);
    } else if (filterActive === 'inactive') {
      filtered = agents.filter(agent => !agent.is_active);
    }
    
    // Sort agents
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'performance':
          const aRate = a.task_count > 0 ? a.completed_tasks / a.task_count : 0;
          const bRate = b.task_count > 0 ? b.completed_tasks / b.task_count : 0;
          return bRate - aRate;
        case 'workload':
          return (b.current_workload || 0) - (a.current_workload || 0);
        case 'tasks':
          return b.task_count - a.task_count;
        default:
          return 0;
      }
    });
  }, [agents, sortBy, filterActive]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div className="h-6 bg-gray-200 rounded w-32 animate-pulse"></div>
          <div className="flex space-x-2">
            <div className="h-8 bg-gray-200 rounded w-20 animate-pulse"></div>
            <div className="h-8 bg-gray-200 rounded w-24 animate-pulse"></div>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, index) => (
            <AgentCard key={index} agent={{}} isLoading={true} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-xl font-bold text-gray-900">
          🤖 AI Development Team ({sortedAndFilteredAgents.length})
        </h2>
        
        <div className="flex space-x-2">
          {/* Filter Dropdown */}
          <select
            value={filterActive}
            onChange={(e) => setFilterActive(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Agents</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive Only</option>
          </select>
          
          {/* Sort Dropdown */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="name">Sort by Name</option>
            <option value="performance">Sort by Performance</option>
            <option value="workload">Sort by Workload</option>
            <option value="tasks">Sort by Task Count</option>
          </select>
        </div>
      </div>

      {/* Agent Grid */}
      {sortedAndFilteredAgents.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-4xl mb-4">🤖</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No agents found</h3>
          <p className="text-gray-600">
            {filterActive === 'all'
              ? "Your AI team hasn't been initialized yet."
              : `No ${filterActive} agents found.`
            }
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedAndFilteredAgents.map(agent => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onViewTasks={onViewTasks}
              onViewPerformance={onViewPerformance}
            />
          ))}
        </div>
      )}

      {/* Team Summary */}
      {sortedAndFilteredAgents.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Team Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {sortedAndFilteredAgents.filter(a => a.is_active).length}
              </div>
              <div className="text-sm text-gray-600">Active Agents</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {sortedAndFilteredAgents.reduce((sum, a) => sum + a.completed_tasks, 0)}
              </div>
              <div className="text-sm text-gray-600">Total Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {sortedAndFilteredAgents.reduce((sum, a) => sum + (a.current_workload || 0), 0)}h
              </div>
              <div className="text-sm text-gray-600">Total Workload</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {Math.round(
                  sortedAndFilteredAgents.reduce((sum, a) => {
                    const rate = a.task_count > 0 ? a.completed_tasks / a.task_count : 0;
                    return sum + rate;
                  }, 0) / sortedAndFilteredAgents.length * 100
                )}%
              </div>
              <div className="text-sm text-gray-600">Avg Success Rate</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Individual Agent Detail Component
const AgentDetail = ({ agent, tasks = [], onBack, onAssignTask }) => {
  const [activeTab, setActiveTab] = useState('overview');
  
  const agentTasks = tasks.filter(task => task.agent_id === agent.id);
  const completedTasks = agentTasks.filter(task => task.status === 'completed');
  const inProgressTasks = agentTasks.filter(task => task.status === 'in_progress');
  const pendingTasks = agentTasks.filter(task => task.status === 'pending');
  
  const completionRate = agentTasks.length > 0
    ? completedTasks.length / agentTasks.length
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <button
              onClick={onBack}
              className="text-gray-500 hover:text-gray-700 mr-4 p-2 rounded-lg hover:bg-gray-100"
            >
              ← Back
            </button>
            <span className="text-3xl mr-4">{AGENT_ICONS[agent.type]}</span>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{agent.name}</h2>
              <p className="text-gray-600 capitalize">
                {agent.type.replace('_', ' ')}
              </p>
            </div>
          </div>
          
          <button
            onClick={() => onAssignTask(agent)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Assign Task
          </button>
        </div>
        
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{agentTasks.length}</div>
            <div className="text-sm text-gray-600">Total Tasks</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{completedTasks.length}</div>
            <div className="text-sm text-gray-600">Completed</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{inProgressTasks.length}</div>
            <div className="text-sm text-gray-600">In Progress</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {Math.round(completionRate * 100)}%
            </div>
            <div className="text-sm text-gray-600">Success Rate</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {['overview', 'tasks', 'performance'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Description</h3>
                <p className="text-gray-700">{agent.description}</p>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Expertise</h3>
                <div className="flex flex-wrap gap-2">
                  {(agent.expertise || []).map((skill, index) => (
                    <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'tasks' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">Recent Tasks</h3>
                <span className="text-sm text-gray-500">{agentTasks.length} total</span>
              </div>
              
              {agentTasks.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">📝</div>
                  <p>No tasks assigned yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {agentTasks.slice(0, 10).map(task => (
                    <div key={task.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{task.title}</h4>
                        <p className="text-sm text-gray-600 truncate">{task.description}</p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          task.status === 'completed' ? 'bg-green-100 text-green-800' :
                          task.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                          task.status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {task.status.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'performance' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Task Distribution</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Completed</span>
                      <span className="text-sm font-medium">{completedTasks.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">In Progress</span>
                      <span className="text-sm font-medium">{inProgressTasks.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Pending</span>
                      <span className="text-sm font-medium">{pendingTasks.length}</span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Performance Metrics</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Success Rate</span>
                      <span className="text-sm font-medium">{Math.round(completionRate * 100)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Avg. Completion Time</span>
                      <span className="text-sm font-medium">2.3 hours</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Current Workload</span>
                      <span className="text-sm font-medium">{agent.current_workload || 0}h</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export { AgentCard, AgentGrid, AgentDetail };
export default AgentGrid;
