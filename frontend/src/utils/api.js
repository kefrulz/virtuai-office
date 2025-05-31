// VirtuAI Office - API Utility Functions
// Centralized API communication layer

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
const API_PREFIX = '/api';

// Request timeout in milliseconds
const REQUEST_TIMEOUT = 30000;

/**
 * HTTP Status Codes
 */
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  UNPROCESSABLE_ENTITY: 422,
  INTERNAL_SERVER_ERROR: 500
};

/**
 * API Error Class
 */
export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Network Error Class
 */
export class NetworkError extends Error {
  constructor(message) {
    super(message);
    this.name = 'NetworkError';
  }
}

/**
 * Create request headers
 */
const createHeaders = (options = {}) => {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };

  // Add authentication token if available
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
};

/**
 * Handle API response
 */
const handleResponse = async (response) => {
  const contentType = response.headers.get('content-type');
  
  let data;
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const errorMessage = data?.detail || data?.message || `HTTP ${response.status}: ${response.statusText}`;
    throw new ApiError(errorMessage, response.status, data);
  }

  return data;
};

/**
 * Create timeout controller
 */
const createTimeoutController = (timeout = REQUEST_TIMEOUT) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  return {
    controller,
    cleanup: () => clearTimeout(timeoutId)
  };
};

/**
 * Base API call function
 */
export const apiCall = async (endpoint, options = {}) => {
  const { timeout = REQUEST_TIMEOUT, ...fetchOptions } = options;
  const { controller, cleanup } = createTimeoutController(timeout);

  try {
    const url = `${API_BASE}${API_PREFIX}${endpoint}`;
    
    const response = await fetch(url, {
      headers: createHeaders(options),
      signal: controller.signal,
      ...fetchOptions
    });

    cleanup();
    return await handleResponse(response);
    
  } catch (error) {
    cleanup();
    
    if (error.name === 'AbortError') {
      throw new NetworkError('Request timeout');
    }
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new NetworkError('Network connection failed');
    }
    
    if (error instanceof ApiError) {
      throw error;
    }
    
    throw new NetworkError(error.message);
  }
};

/**
 * GET request helper
 */
export const apiGet = (endpoint, options = {}) => {
  return apiCall(endpoint, {
    method: 'GET',
    ...options
  });
};

/**
 * POST request helper
 */
export const apiPost = (endpoint, data = null, options = {}) => {
  return apiCall(endpoint, {
    method: 'POST',
    body: data ? JSON.stringify(data) : null,
    ...options
  });
};

/**
 * PUT request helper
 */
export const apiPut = (endpoint, data = null, options = {}) => {
  return apiCall(endpoint, {
    method: 'PUT',
    body: data ? JSON.stringify(data) : null,
    ...options
  });
};

/**
 * PATCH request helper
 */
export const apiPatch = (endpoint, data = null, options = {}) => {
  return apiCall(endpoint, {
    method: 'PATCH',
    body: data ? JSON.stringify(data) : null,
    ...options
  });
};

/**
 * DELETE request helper
 */
export const apiDelete = (endpoint, options = {}) => {
  return apiCall(endpoint, {
    method: 'DELETE',
    ...options
  });
};

/**
 * File upload helper
 */
export const apiUpload = (endpoint, file, options = {}) => {
  const formData = new FormData();
  formData.append('file', file);

  return apiCall(endpoint, {
    method: 'POST',
    body: formData,
    headers: {
      // Don't set Content-Type for FormData, let browser set it
      ...options.headers
    },
    ...options
  });
};

// =============================================================================
// SPECIFIC API ENDPOINTS
// =============================================================================

/**
 * System Status API
 */
export const systemApi = {
  getStatus: () => apiGet('/status'),
  getAnalytics: () => apiGet('/analytics'),
};

/**
 * Tasks API
 */
export const tasksApi = {
  getAll: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    const endpoint = queryString ? `/tasks?${queryString}` : '/tasks';
    return apiGet(endpoint);
  },
  
  getById: (taskId) => apiGet(`/tasks/${taskId}`),
  
  create: (taskData) => apiPost('/tasks', taskData),
  
  smartCreate: (taskData) => apiPost('/tasks/smart-assign', taskData),
  
  update: (taskId, updates) => apiPatch(`/tasks/${taskId}`, updates),
  
  delete: (taskId) => apiDelete(`/tasks/${taskId}`),
  
  retry: (taskId) => apiPost(`/tasks/${taskId}/retry`),
  
  assign: (taskId, agentId) => apiPost(`/tasks/${taskId}/assign/${agentId}`),
  
  bulkCreate: (tasks) => apiPost('/tasks/bulk', { tasks }),
  
  bulkUpdate: (taskIds, updates) => apiPatch('/tasks/bulk', { task_ids: taskIds, updates })
};

/**
 * Agents API
 */
export const agentsApi = {
  getAll: () => apiGet('/agents'),
  
  getById: (agentId) => apiGet(`/agents/${agentId}`),
  
  getTasks: (agentId) => apiGet(`/agents/${agentId}/tasks`),
  
  getPerformance: (agentId) => apiGet(`/agents/${agentId}/performance`)
};

/**
 * Projects API
 */
export const projectsApi = {
  getAll: () => apiGet('/projects'),
  
  getById: (projectId) => apiGet(`/projects/${projectId}`),
  
  create: (name, description = '') => apiPost('/projects', { name, description }),
  
  update: (projectId, updates) => apiPatch(`/projects/${projectId}`, updates),
  
  delete: (projectId) => apiDelete(`/projects/${projectId}`)
};

/**
 * Boss AI API
 */
export const bossApi = {
  getInsights: () => apiGet('/boss/insights'),
  
  optimizeAssignments: () => apiPost('/boss/optimize-assignments'),
  
  rebalanceWorkload: () => apiPost('/boss/rebalance-workload'),
  
  generateStandup: () => apiPost('/standup')
};

/**
 * Collaboration API
 */
export const collaborationApi = {
  getActive: () => apiGet('/collaboration/active'),
  
  getById: (collaborationId) => apiGet(`/collaboration/${collaborationId}`)
};

/**
 * Apple Silicon API
 */
export const appleSiliconApi = {
  detect: () => apiGet('/apple-silicon/detect'),
  
  optimize: (level = 'balanced') => apiPost('/apple-silicon/optimize', { optimization_level: level }),
  
  getPerformance: () => apiGet('/apple-silicon/performance'),
  
  getDashboard: () => apiGet('/apple-silicon/dashboard'),
  
  benchmark: () => apiPost('/apple-silicon/benchmark'),
  
  models: {
    recommend: () => apiGet('/apple-silicon/models/recommend'),
    download: () => apiPost('/apple-silicon/models/download'),
    getProgress: () => apiGet('/apple-silicon/models/download-progress')
  }
};

/**
 * Demo Data API
 */
export const demoApi = {
  populate: () => apiPost('/demo/populate')
};

// =============================================================================
// WEBSOCKET UTILITIES
// =============================================================================

/**
 * WebSocket Connection Manager
 */
export class WebSocketManager {
  constructor(url = `ws://localhost:8000/ws`) {
    this.url = url;
    this.ws = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.isConnecting = false;
  }

  connect() {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return Promise.resolve();
    }

    this.isConnecting = true;

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.emit('message', data);
            
            // Emit specific event types
            if (data.type) {
              this.emit(data.type, data);
            }
          } catch (error) {
            console.warn('Failed to parse WebSocket message:', event.data);
          }
        };

        this.ws.onclose = () => {
          this.isConnecting = false;
          this.emit('disconnected');
          
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
              this.reconnectAttempts++;
              this.connect();
            }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
          }
        };

        this.ws.onerror = (error) => {
          this.isConnecting = false;
          this.emit('error', error);
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.listeners.clear();
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('WebSocket event callback error:', error);
        }
      });
    }
  }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

// =============================================================================
// REACT HOOKS
// =============================================================================

/**
 * Hook for making API calls with loading and error states
 */
export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const callApi = useCallback(async (apiFunction, ...args) => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiFunction(...args);
      setLoading(false);
      return result;
    } catch (err) {
      setError(err);
      setLoading(false);
      throw err;
    }
  }, []);

  return { callApi, loading, error };
};

/**
 * Hook for WebSocket connection
 */
export const useWebSocket = (url) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionError, setConnectionError] = useState(null);
  const wsManager = useRef(null);

  useEffect(() => {
    wsManager.current = new WebSocketManager(url);

    wsManager.current.on('connected', () => {
      setIsConnected(true);
      setConnectionError(null);
    });

    wsManager.current.on('disconnected', () => {
      setIsConnected(false);
    });

    wsManager.current.on('message', (data) => {
      setLastMessage(data);
    });

    wsManager.current.on('error', (error) => {
      setConnectionError(error);
    });

    wsManager.current.connect().catch(console.error);

    return () => {
      wsManager.current?.disconnect();
    };
  }, [url]);

  const sendMessage = useCallback((data) => {
    wsManager.current?.send(data);
  }, []);

  const subscribe = useCallback((event, callback) => {
    wsManager.current?.on(event, callback);
    
    return () => {
      wsManager.current?.off(event, callback);
    };
  }, []);

  return {
    isConnected,
    lastMessage,
    connectionError,
    sendMessage,
    subscribe
  };
};

// =============================================================================
// ERROR HANDLING UTILITIES
// =============================================================================

/**
 * Format API error for display
 */
export const formatApiError = (error) => {
  if (error instanceof ApiError) {
    return {
      title: `Error ${error.status}`,
      message: error.message,
      details: error.data
    };
  }
  
  if (error instanceof NetworkError) {
    return {
      title: 'Connection Error',
      message: error.message,
      details: null
    };
  }
  
  return {
    title: 'Unknown Error',
    message: error.message || 'An unexpected error occurred',
    details: null
  };
};

/**
 * Retry mechanism for failed requests
 */
export const withRetry = async (apiFunction, maxRetries = 3, delay = 1000) => {
  let lastError;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await apiFunction();
    } catch (error) {
      lastError = error;
      
      // Don't retry on client errors (4xx)
      if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
        throw error;
      }
      
      if (attempt < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt)));
      }
    }
  }
  
  throw lastError;
};

// =============================================================================
// CACHE UTILITIES
// =============================================================================

/**
 * Simple in-memory cache for API responses
 */
class ApiCache {
  constructor(defaultTtl = 5 * 60 * 1000) { // 5 minutes default
    this.cache = new Map();
    this.defaultTtl = defaultTtl;
  }

  set(key, value, ttl = this.defaultTtl) {
    const expiry = Date.now() + ttl;
    this.cache.set(key, { value, expiry });
  }

  get(key) {
    const item = this.cache.get(key);
    
    if (!item) {
      return null;
    }
    
    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return null;
    }
    
    return item.value;
  }

  has(key) {
    return this.get(key) !== null;
  }

  delete(key) {
    this.cache.delete(key);
  }

  clear() {
    this.cache.clear();
  }
}

export const apiCache = new ApiCache();

/**
 * Cached API call wrapper
 */
export const cachedApiCall = async (cacheKey, apiFunction, ttl) => {
  const cached = apiCache.get(cacheKey);
  if (cached) {
    return cached;
  }
  
  const result = await apiFunction();
  apiCache.set(cacheKey, result, ttl);
  return result;
};

// =============================================================================
// EXPORTS
// =============================================================================

export default {
  // Core functions
  apiCall,
  apiGet,
  apiPost,
  apiPut,
  apiPatch,
  apiDelete,
  apiUpload,
  
  // API endpoints
  systemApi,
  tasksApi,
  agentsApi,
  projectsApi,
  bossApi,
  collaborationApi,
  appleSiliconApi,
  demoApi,
  
  // WebSocket
  WebSocketManager,
  
  // Utilities
  formatApiError,
  withRetry,
  apiCache,
  cachedApiCall,
  
  // Constants
  API_BASE,
  HTTP_STATUS
};
