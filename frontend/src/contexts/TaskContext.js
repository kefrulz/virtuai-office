import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';

// Task Context
const TaskContext = createContext();

// Action Types
const TASK_ACTIONS = {
  SET_TASKS: 'SET_TASKS',
  ADD_TASK: 'ADD_TASK',
  UPDATE_TASK: 'UPDATE_TASK',
  DELETE_TASK: 'DELETE_TASK',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  SET_FILTER: 'SET_FILTER',
  SET_SORT: 'SET_SORT',
  CLEAR_ERROR: 'CLEAR_ERROR'
};

// Initial State
const initialState = {
  tasks: [],
  loading: false,
  error: null,
  filter: {
    status: '',
    priority: '',
    agent_id: '',
    project_id: ''
  },
  sort: {
    field: 'created_at',
    order: 'desc'
  }
};

// Reducer
const taskReducer = (state, action) => {
  switch (action.type) {
    case TASK_ACTIONS.SET_TASKS:
      return {
        ...state,
        tasks: action.payload,
        loading: false,
        error: null
      };

    case TASK_ACTIONS.ADD_TASK:
      return {
        ...state,
        tasks: [action.payload, ...state.tasks],
        error: null
      };

    case TASK_ACTIONS.UPDATE_TASK:
      return {
        ...state,
        tasks: state.tasks.map(task =>
          task.id === action.payload.id ? { ...task, ...action.payload } : task
        ),
        error: null
      };

    case TASK_ACTIONS.DELETE_TASK:
      return {
        ...state,
        tasks: state.tasks.filter(task => task.id !== action.payload),
        error: null
      };

    case TASK_ACTIONS.SET_LOADING:
      return {
        ...state,
        loading: action.payload
      };

    case TASK_ACTIONS.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        loading: false
      };

    case TASK_ACTIONS.SET_FILTER:
      return {
        ...state,
        filter: {
          ...state.filter,
          ...action.payload
        }
      };

    case TASK_ACTIONS.SET_SORT:
      return {
        ...state,
        sort: action.payload
      };

    case TASK_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null
      };

    default:
      return state;
  }
};

// API Base URL
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Task Provider Component
export const TaskProvider = ({ children }) => {
  const [state, dispatch] = useReducer(taskReducer, initialState);

  // API Helper Function
  const apiCall = useCallback(async (endpoint, options = {}) => {
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
  }, []);

  // Load Tasks
  const loadTasks = useCallback(async (filters = {}) => {
    dispatch({ type: TASK_ACTIONS.SET_LOADING, payload: true });
    
    try {
      const queryParams = new URLSearchParams();
      
      // Apply filters
      Object.entries({ ...state.filter, ...filters }).forEach(([key, value]) => {
        if (value) {
          queryParams.append(key, value);
        }
      });

      // Apply sorting
      if (state.sort.field) {
        queryParams.append('sort_by', state.sort.field);
        queryParams.append('sort_order', state.sort.order);
      }

      const tasks = await apiCall(`/api/tasks?${queryParams.toString()}`);
      dispatch({ type: TASK_ACTIONS.SET_TASKS, payload: tasks });
    } catch (error) {
      dispatch({ type: TASK_ACTIONS.SET_ERROR, payload: error.message });
    }
  }, [apiCall, state.filter, state.sort]);

  // Create Task
  const createTask = useCallback(async (taskData) => {
    dispatch({ type: TASK_ACTIONS.SET_LOADING, payload: true });
    
    try {
      const newTask = await apiCall('/api/tasks', {
        method: 'POST',
        body: JSON.stringify(taskData),
      });
      
      dispatch({ type: TASK_ACTIONS.ADD_TASK, payload: newTask });
      return newTask;
    } catch (error) {
      dispatch({ type: TASK_ACTIONS.SET_ERROR, payload: error.message });
      throw error;
    } finally {
      dispatch({ type: TASK_ACTIONS.SET_LOADING, payload: false });
    }
  }, [apiCall]);

  // Create Smart Task (with Boss AI assignment)
  const createSmartTask = useCallback(async (taskData) => {
    dispatch({ type: TASK_ACTIONS.SET_LOADING, payload: true });
    
    try {
      const result = await apiCall('/api/tasks/smart-assign', {
        method: 'POST',
        body: JSON.stringify(taskData),
      });
      
      // The smart assignment returns more detailed information
      dispatch({ type: TASK_ACTIONS.ADD_TASK, payload: result.task || result });
      return result;
    } catch (error) {
      dispatch({ type: TASK_ACTIONS.SET_ERROR, payload: error.message });
      throw error;
    } finally {
      dispatch({ type: TASK_ACTIONS.SET_LOADING, payload: false });
    }
  }, [apiCall]);

  // Update Task
  const updateTask = useCallback(async (taskId, updates) => {
    try {
      const updatedTask = await apiCall(`/api/tasks/${taskId}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
      });
      
      dispatch({ type: TASK_ACTIONS.UPDATE_TASK, payload: updatedTask });
      return updatedTask;
    } catch (error) {
      dispatch({ type: TASK_ACTIONS.SET_ERROR, payload: error.message });
      throw error;
    }
  }, [apiCall]);

  // Delete Task
  const deleteTask = useCallback(async (taskId) => {
    try {
      await apiCall(`/api/tasks/${taskId}`, {
        method: 'DELETE',
      });
      
      dispatch({ type: TASK_ACTIONS.DELETE_TASK, payload: taskId });
    } catch (error) {
      dispatch({ type: TASK_ACTIONS.SET_ERROR, payload: error.message });
      throw error;
    }
  }, [apiCall]);

  // Retry Failed Task
  const retryTask = useCallback(async (taskId) => {
    try {
      await apiCall(`/api/tasks/${taskId}/retry`, {
        method: 'POST',
      });
      
      // Reload tasks to get updated status
      await loadTasks();
    } catch (error) {
      dispatch({ type: TASK_ACTIONS.SET_ERROR, payload: error.message });
      throw error;
    }
  }, [apiCall, loadTasks]);

  // Assign Task to Agent
  const assignTask = useCallback(async (taskId, agentId) => {
    try {
      await apiCall(`/api/tasks/${taskId}/assign/${agentId}`, {
        method: 'POST',
      });
      
      // Reload tasks to get updated assignment
      await loadTasks();
    } catch (error) {
      dispatch({ type: TASK_ACTIONS.SET_ERROR, payload: error.message });
      throw error;
    }
  }, [apiCall, loadTasks]);

  // Get Task Details
  const getTask = useCallback(async (taskId) => {
    try {
      const task = await apiCall(`/api/tasks/${taskId}`);
      return task;
    } catch (error) {
      dispatch({ type: TASK_ACTIONS.SET_ERROR, payload: error.message });
      throw error;
    }
  }, [apiCall]);

  // Set Filter
  const setFilter = useCallback((filterUpdates) => {
    dispatch({ type: TASK_ACTIONS.SET_FILTER, payload: filterUpdates });
  }, []);

  // Set Sort
  const setSort = useCallback((field, order = 'desc') => {
    dispatch({ type: TASK_ACTIONS.SET_SORT, payload: { field, order } });
  }, []);

  // Clear Error
  const clearError = useCallback(() => {
    dispatch({ type: TASK_ACTIONS.CLEAR_ERROR });
  }, []);

  // Get Filtered and Sorted Tasks
  const getFilteredTasks = useCallback(() => {
    let filtered = [...state.tasks];

    // Apply filters
    if (state.filter.status) {
      filtered = filtered.filter(task => task.status === state.filter.status);
    }
    if (state.filter.priority) {
      filtered = filtered.filter(task => task.priority === state.filter.priority);
    }
    if (state.filter.agent_id) {
      filtered = filtered.filter(task => task.agent_id === state.filter.agent_id);
    }
    if (state.filter.project_id) {
      filtered = filtered.filter(task => task.project_id === state.filter.project_id);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      const aValue = a[state.sort.field];
      const bValue = b[state.sort.field];
      
      if (state.sort.order === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [state.tasks, state.filter, state.sort]);

  // Get Task Statistics
  const getTaskStats = useCallback(() => {
    const stats = {
      total: state.tasks.length,
      pending: 0,
      in_progress: 0,
      completed: 0,
      failed: 0,
      by_priority: {
        low: 0,
        medium: 0,
        high: 0,
        urgent: 0
      },
      by_agent: {}
    };

    state.tasks.forEach(task => {
      // Count by status
      stats[task.status] = (stats[task.status] || 0) + 1;
      
      // Count by priority
      stats.by_priority[task.priority] = (stats.by_priority[task.priority] || 0) + 1;
      
      // Count by agent
      if (task.agent_id) {
        stats.by_agent[task.agent_id] = (stats.by_agent[task.agent_id] || 0) + 1;
      }
    });

    return stats;
  }, [state.tasks]);

  // Auto-refresh tasks
  useEffect(() => {
    loadTasks();
    
    // Set up polling for task updates
    const interval = setInterval(() => {
      if (!state.loading) {
        loadTasks();
      }
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [loadTasks, state.loading]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    let ws;
    
    try {
      ws = new WebSocket(`ws://localhost:8000/ws`);
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.type) {
            case 'task_update':
              dispatch({
                type: TASK_ACTIONS.UPDATE_TASK,
                payload: { id: data.task_id, status: data.status }
              });
              break;
              
            case 'task_completed':
              // Reload tasks to get the complete updated task
              loadTasks();
              break;
              
            case 'task_failed':
              dispatch({
                type: TASK_ACTIONS.UPDATE_TASK,
                payload: { id: data.task_id, status: 'failed', error: data.error }
              });
              break;
              
            default:
              break;
          }
        } catch (error) {
          console.warn('Failed to parse WebSocket message:', error);
        }
      };
      
      ws.onopen = () => {
        console.log('TaskContext: WebSocket connected');
      };
      
      ws.onclose = () => {
        console.log('TaskContext: WebSocket disconnected');
      };
      
      ws.onerror = (error) => {
        console.warn('TaskContext: WebSocket error:', error);
      };
    } catch (error) {
      console.warn('TaskContext: Failed to establish WebSocket connection:', error);
    }
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [loadTasks]);

  const value = {
    // State
    tasks: state.tasks,
    loading: state.loading,
    error: state.error,
    filter: state.filter,
    sort: state.sort,
    
    // Actions
    loadTasks,
    createTask,
    createSmartTask,
    updateTask,
    deleteTask,
    retryTask,
    assignTask,
    getTask,
    setFilter,
    setSort,
    clearError,
    
    // Computed
    filteredTasks: getFilteredTasks(),
    taskStats: getTaskStats()
  };

  return (
    <TaskContext.Provider value={value}>
      {children}
    </TaskContext.Provider>
  );
};

// Custom Hook
export const useTasks = () => {
  const context = useContext(TaskContext);
  
  if (!context) {
    throw new Error('useTasks must be used within a TaskProvider');
  }
  
  return context;
};

// Export action types for external use
export { TASK_ACTIONS };

export default TaskContext;
