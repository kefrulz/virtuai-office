import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AgentContext = createContext();

export const useAgents = () => {
  const context = useContext(AgentContext);
  if (!context) {
    throw new Error('useAgents must be used within an AgentProvider');
  }
  return context;
};

export const AgentProvider = ({ children }) => {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [agentTasks, setAgentTasks] = useState({});
  const [agentPerformance, setAgentPerformance] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE = 'http://localhost:8000';

  // Fetch all agents
  const fetchAgents = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/agents`);
      if (!response.ok) throw new Error('Failed to fetch agents');
      
      const data = await response.json();
      setAgents(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching agents:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch agent tasks
  const fetchAgentTasks = useCallback(async (agentId) => {
    try {
      const response = await fetch(`${API_BASE}/api/agents/${agentId}/tasks`);
      if (!response.ok) throw new Error('Failed to fetch agent tasks');
      
      const data = await response.json();
      setAgentTasks(prev => ({
        ...prev,
        [agentId]: data
      }));
      return data;
    } catch (err) {
      console.error('Error fetching agent tasks:', err);
      return [];
    }
  }, []);

  // Fetch agent performance
  const fetchAgentPerformance = useCallback(async (agentId) => {
    try {
      const response = await fetch(`${API_BASE}/api/agents/${agentId}/performance`);
      if (!response.ok) throw new Error('Failed to fetch agent performance');
      
      const data = await response.json();
      setAgentPerformance(prev => ({
        ...prev,
        [agentId]: data
      }));
      return data;
    } catch (err) {
      console.error('Error fetching agent performance:', err);
      return null;
    }
  }, []);

  // Get agent by ID
  const getAgentById = useCallback((agentId) => {
    return agents.find(agent => agent.id === agentId);
  }, [agents]);

  // Get agent by type
  const getAgentByType = useCallback((agentType) => {
    return agents.find(agent => agent.type === agentType);
  }, [agents]);

  // Get agents by status
  const getAgentsByStatus = useCallback((isActive = true) => {
    return agents.filter(agent => agent.is_active === isActive);
  }, [agents]);

  // Get agent workload
  const getAgentWorkload = useCallback((agentId) => {
    const tasks = agentTasks[agentId] || [];
    const activeTasks = tasks.filter(task =>
      task.status === 'pending' || task.status === 'in_progress'
    );
    return {
      total: tasks.length,
      active: activeTasks.length,
      completed: tasks.filter(task => task.status === 'completed').length,
      failed: tasks.filter(task => task.status === 'failed').length
    };
  }, [agentTasks]);

  // Get best agent for task
  const getBestAgentForTask = useCallback((taskDescription, priority = 'medium') => {
    const activeAgents = getAgentsByStatus(true);
    
    // Simple scoring based on expertise matching and workload
    const agentScores = activeAgents.map(agent => {
      const expertise = agent.expertise || [];
      const workload = getAgentWorkload(agent.id);
      
      // Calculate expertise match score
      const descriptionLower = taskDescription.toLowerCase();
      const expertiseScore = expertise.reduce((score, skill) => {
        return descriptionLower.includes(skill.toLowerCase()) ? score + 1 : score;
      }, 0) / Math.max(expertise.length, 1);
      
      // Calculate workload penalty
      const workloadPenalty = workload.active * 0.2;
      
      // Priority bonus for certain agent types
      const priorityBonus = priority === 'urgent' ? 0.1 : 0;
      
      const totalScore = expertiseScore - workloadPenalty + priorityBonus;
      
      return {
        agent,
        score: totalScore,
        workload: workload.active
      };
    });
    
    // Sort by score and return best match
    agentScores.sort((a, b) => b.score - a.score);
    return agentScores[0]?.agent || null;
  }, [getAgentsByStatus, getAgentWorkload]);

  // Update agent status
  const updateAgentStatus = useCallback(async (agentId, isActive) => {
    try {
      const response = await fetch(`${API_BASE}/api/agents/${agentId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_active: isActive }),
      });
      
      if (!response.ok) throw new Error('Failed to update agent status');
      
      // Update local state
      setAgents(prev =>
        prev.map(agent =>
          agent.id === agentId
            ? { ...agent, is_active: isActive }
            : agent
        )
      );
      
      return true;
    } catch (err) {
      console.error('Error updating agent status:', err);
      return false;
    }
  }, []);

  // Assign task to agent
  const assignTaskToAgent = useCallback(async (taskId, agentId) => {
    try {
      const response = await fetch(`${API_BASE}/api/tasks/${taskId}/assign/${agentId}`, {
        method: 'POST',
      });
      
      if (!response.ok) throw new Error('Failed to assign task');
      
      // Refresh agent tasks
      await fetchAgentTasks(agentId);
      
      return true;
    } catch (err) {
      console.error('Error assigning task:', err);
      return false;
    }
  }, [fetchAgentTasks]);

  // Get agent statistics
  const getAgentStatistics = useCallback(() => {
    const stats = {
      total: agents.length,
      active: 0,
      inactive: 0,
      totalTasks: 0,
      completedTasks: 0,
      activeTasks: 0,
      avgPerformance: 0
    };

    agents.forEach(agent => {
      if (agent.is_active) {
        stats.active++;
      } else {
        stats.inactive++;
      }

      const workload = getAgentWorkload(agent.id);
      stats.totalTasks += workload.total;
      stats.completedTasks += workload.completed;
      stats.activeTasks += workload.active;

      const performance = agentPerformance[agent.id];
      if (performance) {
        stats.avgPerformance += performance.performance?.performance_score || 0;
      }
    });

    if (agents.length > 0) {
      stats.avgPerformance = stats.avgPerformance / agents.length;
    }

    return stats;
  }, [agents, getAgentWorkload, agentPerformance]);

  // Refresh all agent data
  const refreshAgentData = useCallback(async () => {
    await fetchAgents();
    
    // Fetch tasks and performance for all agents
    const agentPromises = agents.map(async (agent) => {
      await Promise.all([
        fetchAgentTasks(agent.id),
        fetchAgentPerformance(agent.id)
      ]);
    });
    
    await Promise.all(agentPromises);
  }, [fetchAgents, fetchAgentTasks, fetchAgentPerformance, agents]);

  // Agent type configurations
  const agentTypeConfig = {
    product_manager: {
      icon: '👩‍💼',
      name: 'Product Manager',
      color: 'purple',
      description: 'User stories, requirements, project planning'
    },
    frontend_developer: {
      icon: '👨‍💻',
      name: 'Frontend Developer',
      color: 'blue',
      description: 'React components, UI, responsive design'
    },
    backend_developer: {
      icon: '👩‍💻',
      name: 'Backend Developer',
      color: 'green',
      description: 'APIs, databases, server-side logic'
    },
    ui_ux_designer: {
      icon: '🎨',
      name: 'UI/UX Designer',
      color: 'pink',
      description: 'Design systems, wireframes, user experience'
    },
    qa_tester: {
      icon: '🔍',
      name: 'QA Tester',
      color: 'orange',
      description: 'Test plans, automation, quality assurance'
    }
  };

  // Get agent type configuration
  const getAgentTypeConfig = useCallback((agentType) => {
    return agentTypeConfig[agentType] || {
      icon: '🤖',
      name: 'AI Agent',
      color: 'gray',
      description: 'Specialized AI assistant'
    };
  }, []);

  // Initialize data on mount
  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  // Auto-refresh agent data periodically
  useEffect(() => {
    const interval = setInterval(() => {
      if (!loading) {
        refreshAgentData();
      }
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [refreshAgentData, loading]);

  const contextValue = {
    // State
    agents,
    selectedAgent,
    agentTasks,
    agentPerformance,
    loading,
    error,

    // Actions
    setSelectedAgent,
    fetchAgents,
    fetchAgentTasks,
    fetchAgentPerformance,
    refreshAgentData,

    // Utilities
    getAgentById,
    getAgentByType,
    getAgentsByStatus,
    getAgentWorkload,
    getBestAgentForTask,
    getAgentStatistics,
    getAgentTypeConfig,

    // Operations
    updateAgentStatus,
    assignTaskToAgent,

    // Configuration
    agentTypeConfig
  };

  return (
    <AgentContext.Provider value={contextValue}>
      {children}
    </AgentContext.Provider>
  );
};

export default AgentProvider;
