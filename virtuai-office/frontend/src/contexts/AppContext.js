import React, { createContext, useContext, useReducer, useEffect } from 'react';

// Action Types
const ActionTypes = {
  // System
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  SET_SYSTEM_STATUS: 'SET_SYSTEM_STATUS',
  
  // Tasks
  SET_TASKS: 'SET_TASKS',
  ADD_TASK: 'ADD_TASK',
  UPDATE_TASK: 'UPDATE_TASK',
  REMOVE_TASK: 'REMOVE_TASK',
  SET_SELECTED_TASK: 'SET_SELECTED_TASK',
  
  // Agents
  SET_AGENTS: 'SET_AGENTS',
  UPDATE_AGENT: 'UPDATE_AGENT',
  SET_SELECTED_AGENT: 'SET_SELECTED_AGENT',
  
  // Projects
  SET_PROJECTS: 'SET_PROJECTS',
  ADD_PROJECT: 'ADD_PROJECT',
  UPDATE_PROJECT: 'UPDATE_PROJECT',
  SET_SELECTED_PROJECT: 'SET_SELECTED_PROJECT',
  
  // Analytics
  SET_ANALYTICS: 'SET_ANALYTICS',
  
  // UI State
  SET_ACTIVE_TAB: 'SET_ACTIVE_TAB',
  SET_MODAL_STATE: 'SET_MODAL_STATE',
  SET_SIDEBAR_OPEN: 'SET_SIDEBAR_OPEN',
  
  // Apple Silicon
  SET_APPLE_SILICON_STATUS: 'SET_APPLE_SILICON_STATUS',
  SET_PERFORMANCE_METRICS: 'SET_PERFORMANCE_METRICS',
  
  // Real-time updates
  WEBSOCKET_CONNECTED: 'WEBSOCKET_CONNECTED',
  WEBSOCKET_DISCONNECTED: 'WEBSOCKET_DISCONNECTED',
  WEBSOCKET_MESSAGE: 'WEBSOCKET_MESSAGE'
};

// Initial State
const initialState = {
  // System state
  loading: false,
  error: null,
  systemStatus: null,
  
  // Data
  tasks: [],
  agents: [],
  projects: [],
  analytics: null,
  
  // Selected items
  selectedTask: null,
  selectedAgent: null,
  selectedProject: null,
  
  // UI state
  activeTab: 'dashboard',
  modals: {
    createTask: false,
    taskDetails: false,
    agentDetails: false,
    standup: false,
    help: false,
    settings: false
  },
  sidebarOpen: true,
  
  // Apple Silicon
  appleSiliconStatus: null,
  performanceMetrics: null,
  
  // WebSocket
  wsConnected: false,
  lastUpdate: null
};

// Reducer
const appReducer = (state, action) => {
  switch (action.type) {
    case ActionTypes.SET_LOADING:
      return { ...state, loading: action.payload };
      
    case ActionTypes.SET_ERROR:
      return { ...state, error: action.payload, loading: false };
      
    case ActionTypes.CLEAR_ERROR:
      return { ...state, error: null };
      
    case ActionTypes.SET_SYSTEM_STATUS:
      return { ...state, systemStatus: action.payload };
      
    case ActionTypes.SET_TASKS:
      return { ...state, tasks: action.payload };
      
    case ActionTypes.ADD_TASK:
      return { ...state, tasks: [...state.tasks, action.payload] };
      
    case ActionTypes.UPDATE_TASK:
      return {
        ...state,
        tasks: state.tasks.map(task =>
          task.id === action.payload.id ? { ...task, ...action.payload } : task
        ),
        selectedTask: state.selectedTask?.id === action.payload.id
          ? { ...state.selectedTask, ...action.payload }
          : state.selectedTask
      };
      
    case ActionTypes.REMOVE_TASK:
      return {
        ...state,
        tasks: state.tasks.filter(task => task.id !== action.payload),
        selectedTask: state.selectedTask?.id === action.payload ? null : state.selectedTask
      };
      
    case ActionTypes.SET_SELECTED_TASK:
      return { ...state, selectedTask: action.payload };
      
    case ActionTypes.SET_AGENTS:
      return { ...state, agents: action.payload };
      
    case ActionTypes.UPDATE_AGENT:
      return {
        ...state,
        agents: state.agents.map(agent =>
          agent.id === action.payload.id ? { ...agent, ...action.payload } : agent
        ),
        selectedAgent: state.selectedAgent?.id === action.payload.id
          ? { ...state.selectedAgent, ...action.payload }
          : state.selectedAgent
      };
      
    case ActionTypes.SET_SELECTED_AGENT:
      return { ...state, selectedAgent: action.payload };
      
    case ActionTypes.SET_PROJECTS:
      return { ...state, projects: action.payload };
      
    case ActionTypes.ADD_PROJECT:
      return { ...state, projects: [...state.projects, action.payload] };
      
    case ActionTypes.UPDATE_PROJECT:
      return {
        ...state,
        projects: state.projects.map(project =>
          project.id === action.payload.id ? { ...project, ...action.payload } : project
        ),
        selectedProject: state.selectedProject?.id === action.payload.id
          ? { ...state.selectedProject, ...action.payload }
          : state.selectedProject
      };
      
    case ActionTypes.SET_SELECTED_PROJECT:
      return { ...state, selectedProject: action.payload };
      
    case ActionTypes.SET_ANALYTICS:
      return { ...state, analytics: action.payload };
      
    case ActionTypes.SET_ACTIVE_TAB:
      return { ...state, activeTab: action.payload };
      
    case ActionTypes.SET_MODAL_STATE:
      return {
        ...state,
        modals: { ...state.modals, [action.payload.modal]: action.payload.open }
      };
      
    case ActionTypes.SET_SIDEBAR_OPEN:
      return { ...state, sidebarOpen: action.payload };
      
    case ActionTypes.SET_APPLE_SILICON_STATUS:
      return { ...state, appleSiliconStatus: action.payload };
      
    case ActionTypes.SET_PERFORMANCE_METRICS:
      return { ...state, performanceMetrics: action.payload };
      
    case ActionTypes.WEBSOCKET_CONNECTED:
      return { ...state, wsConnected: true };
      
    case ActionTypes.WEBSOCKET_DISCONNECTED:
      return { ...state, wsConnected: false };
      
    case ActionTypes.WEBSOCKET_MESSAGE:
      return { ...state, lastUpdate: action.payload };
      
    default:
      return state;
  }
};

// Context
const AppContext = createContext();

// Custom hook to use context
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

// Provider Component
export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Action creators
  const actions = {
    // System actions
    setLoading: (loading) => dispatch({ type: ActionTypes.SET_LOADING, payload: loading }),
    setError: (error) => dispatch({ type: ActionTypes.SET_ERROR, payload: error }),
    clearError: () => dispatch({ type: ActionTypes.CLEAR_ERROR }),
    setSystemStatus: (status) => dispatch({ type: ActionTypes.SET_SYSTEM_STATUS, payload: status }),
    
    // Task actions
    setTasks: (tasks) => dispatch({ type: ActionTypes.SET_TASKS, payload: tasks }),
    addTask: (task) => dispatch({ type: ActionTypes.ADD_TASK, payload: task }),
    updateTask: (task) => dispatch({ type: ActionTypes.UPDATE_TASK, payload: task }),
    removeTask: (taskId) => dispatch({ type: ActionTypes.REMOVE_TASK, payload: taskId }),
    setSelectedTask: (task) => dispatch({ type: ActionTypes.SET_SELECTED_TASK, payload: task }),
    
    // Agent actions
    setAgents: (agents) => dispatch({ type: ActionTypes.SET_AGENTS, payload: agents }),
    updateAgent: (agent) => dispatch({ type: ActionTypes.UPDATE_AGENT, payload: agent }),
    setSelectedAgent: (agent) => dispatch({ type: ActionTypes.SET_SELECTED_AGENT, payload: agent }),
    
    // Project actions
    setProjects: (projects) => dispatch({ type: ActionTypes.SET_PROJECTS, payload: projects }),
    addProject: (project) => dispatch({ type: ActionTypes.ADD_PROJECT, payload: project }),
    updateProject: (project) => dispatch({ type: ActionTypes.UPDATE_PROJECT, payload: project }),
    setSelectedProject: (project) => dispatch({ type: ActionTypes.SET_SELECTED_PROJECT, payload: project }),
    
    // Analytics actions
    setAnalytics: (analytics) => dispatch({ type: ActionTypes.SET_ANALYTICS, payload: analytics }),
    
    // UI actions
    setActiveTab: (tab) => dispatch({ type: ActionTypes.SET_ACTIVE_TAB, payload: tab }),
    openModal: (modal) => dispatch({ type: ActionTypes.SET_MODAL_STATE, payload: { modal, open: true } }),
    closeModal: (modal) => dispatch({ type: ActionTypes.SET_MODAL_STATE, payload: { modal, open: false } }),
    toggleSidebar: () => dispatch({ type: ActionTypes.SET_SIDEBAR_OPEN, payload: !state.sidebarOpen }),
    setSidebarOpen: (open) => dispatch({ type: ActionTypes.SET_SIDEBAR_OPEN, payload: open }),
    
    // Apple Silicon actions
    setAppleSiliconStatus: (status) => dispatch({ type: ActionTypes.SET_APPLE_SILICON_STATUS, payload: status }),
    setPerformanceMetrics: (metrics) => dispatch({ type: ActionTypes.SET_PERFORMANCE_METRICS, payload: metrics }),
    
    // WebSocket actions
    setWebSocketConnected: () => dispatch({ type: ActionTypes.WEBSOCKET_CONNECTED }),
    setWebSocketDisconnected: () => dispatch({ type: ActionTypes.WEBSOCKET_DISCONNECTED }),
    handleWebSocketMessage: (message) => dispatch({ type: ActionTypes.WEBSOCKET_MESSAGE, payload: message })
  };

  // API helper functions
  const api = {
    async get(endpoint) {
      try {
        const response = await fetch(`/api${endpoint}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
      } catch (error) {
        actions.setError(error.message);
        throw error;
      }
    },

    async post(endpoint, data) {
      try {
        const response = await fetch(`/api${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
      } catch (error) {
        actions.setError(error.message);
        throw error;
      }
    },

    async put(endpoint, data) {
      try {
        const response = await fetch(`/api${endpoint}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
      } catch (error) {
        actions.setError(error.message);
        throw error;
      }
    },

    async delete(endpoint) {
      try {
        const response = await fetch(`/api${endpoint}`, {
          method: 'DELETE'
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.status === 204 ? null : await response.json();
      } catch (error) {
        actions.setError(error.message);
        throw error;
      }
    }
  };

  // Data loading functions
  const loadData = {
    async tasks() {
      actions.setLoading(true);
      try {
        const tasks = await api.get('/tasks');
        actions.setTasks(tasks);
      } finally {
        actions.setLoading(false);
      }
    },

    async agents() {
      try {
        const agents = await api.get('/agents');
        actions.setAgents(agents);
      } catch (error) {
        console.error('Failed to load agents:', error);
      }
    },

    async projects() {
      try {
        const projects = await api.get('/projects');
        actions.setProjects(projects);
      } catch (error) {
        console.error('Failed to load projects:', error);
      }
    },

    async analytics() {
      try {
        const analytics = await api.get('/analytics');
        actions.setAnalytics(analytics);
      } catch (error) {
        console.error('Failed to load analytics:', error);
      }
    },

    async systemStatus() {
      try {
        const status = await api.get('/status');
        actions.setSystemStatus(status);
      } catch (error) {
        console.error('Failed to load system status:', error);
      }
    },

    async appleSiliconStatus() {
      try {
        const status = await api.get('/apple-silicon/detect');
        actions.setAppleSiliconStatus(status);
      } catch (error) {
        console.error('Failed to load Apple Silicon status:', error);
      }
    },

    async all() {
      await Promise.allSettled([
        loadData.tasks(),
        loadData.agents(),
        loadData.projects(),
        loadData.analytics(),
        loadData.systemStatus(),
        loadData.appleSiliconStatus()
      ]);
    }
  };

  // Task operations
  const taskOperations = {
    async create(taskData) {
      try {
        const task = await api.post('/tasks', taskData);
        actions.addTask(task);
        return task;
      } catch (error) {
        throw error;
      }
    },

    async update(taskId, updates) {
      try {
        const task = await api.put(`/tasks/${taskId}`, updates);
        actions.updateTask(task);
        return task;
      } catch (error) {
        throw error;
      }
    },

    async delete(taskId) {
      try {
        await api.delete(`/tasks/${taskId}`);
        actions.removeTask(taskId);
      } catch (error) {
        throw error;
      }
    },

    async retry(taskId) {
      try {
        await api.post(`/tasks/${taskId}/retry`);
        // Task will be updated via WebSocket
      } catch (error) {
        throw error;
      }
    }
  };

  // Project operations
  const projectOperations = {
    async create(projectData) {
      try {
        const project = await api.post('/projects', projectData);
        actions.addProject(project);
        return project;
      } catch (error) {
        throw error;
      }
    },

    async update(projectId, updates) {
      try {
        const project = await api.put(`/projects/${projectId}`, updates);
        actions.updateProject(project);
        return project;
      } catch (error) {
        throw error;
      }
    }
  };

  // WebSocket setup
  useEffect(() => {
    let ws = null;
    
    const connectWebSocket = () => {
      try {
        ws = new WebSocket('ws://localhost:8000/ws');
        
        ws.onopen = () => {
          actions.setWebSocketConnected();
          console.log('WebSocket connected');
        };
        
        ws.onclose = () => {
          actions.setWebSocketDisconnected();
          console.log('WebSocket disconnected');
          // Attempt to reconnect after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };
        
        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            actions.handleWebSocketMessage(message);
            
            // Handle specific message types
            switch (message.type) {
              case 'task_update':
                // Reload tasks to get latest data
                loadData.tasks();
                break;
              case 'task_completed':
                loadData.tasks();
                loadData.analytics();
                break;
              case 'task_failed':
                loadData.tasks();
                break;
              case 'agent_status':
                loadData.agents();
                break;
            }
          } catch (error) {
            console.error('WebSocket message parsing error:', error);
          }
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
        
      } catch (error) {
        console.error('WebSocket connection error:', error);
      }
    };
    
    connectWebSocket();
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  // Load initial data
  useEffect(() => {
    loadData.all();
  }, []);

  const contextValue = {
    state,
    actions,
    api,
    loadData,
    taskOperations,
    projectOperations
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};

export default AppContext;
