// VirtuAI Office - Custom React Hooks Collection
import { useState, useEffect, useRef, useCallback, useMemo } from 'react';

const API_BASE = 'http://localhost:8000';

// WebSocket connection hook
export const useWebSocket = (url = 'ws://localhost:8000/ws') => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const reconnectTimeoutRef = useRef();

  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(url);
        
        ws.onopen = () => {
          setIsConnected(true);
          setSocket(ws);
          console.log('WebSocket connected');
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setLastMessage(data);
          } catch (error) {
            setLastMessage({ type: 'raw', data: event.data });
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          setSocket(null);
          // Reconnect after 5 seconds
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
      }
    };

    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socket) {
        socket.close();
      }
    };
  }, [url]);

  const sendMessage = useCallback((message) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(message));
    }
  }, [socket, isConnected]);

  return { isConnected, lastMessage, sendMessage };
};

// API call hook with loading states
export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const apiCall = useCallback(async (endpoint, options = {}) => {
    setLoading(true);
    setError(null);

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

      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { apiCall, loading, error };
};

// Task management hook
export const useTasks = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const { apiCall } = useApi();

  const loadTasks = useCallback(async () => {
    try {
      const data = await apiCall('/api/tasks');
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  }, [apiCall]);

  const createTask = useCallback(async (taskData) => {
    try {
      const newTask = await apiCall('/api/tasks', {
        method: 'POST',
        body: JSON.stringify(taskData),
      });
      setTasks(prev => [...prev, newTask]);
      return newTask;
    } catch (error) {
      console.error('Failed to create task:', error);
      throw error;
    }
  }, [apiCall]);

  const updateTask = useCallback(async (taskId, updates) => {
    try {
      const updatedTask = await apiCall(`/api/tasks/${taskId}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
      });
      setTasks(prev => prev.map(task =>
        task.id === taskId ? { ...task, ...updatedTask } : task
      ));
      return updatedTask;
    } catch (error) {
      console.error('Failed to update task:', error);
      throw error;
    }
  }, [apiCall]);

  const deleteTask = useCallback(async (taskId) => {
    try {
      await apiCall(`/api/tasks/${taskId}`, { method: 'DELETE' });
      setTasks(prev => prev.filter(task => task.id !== taskId));
    } catch (error) {
      console.error('Failed to delete task:', error);
      throw error;
    }
  }, [apiCall]);

  const retryTask = useCallback(async (taskId) => {
    try {
      await apiCall(`/api/tasks/${taskId}/retry`, { method: 'POST' });
      // Reload tasks to get updated status
      loadTasks();
    } catch (error) {
      console.error('Failed to retry task:', error);
      throw error;
    }
  }, [apiCall, loadTasks]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  return {
    tasks,
    loading,
    createTask,
    updateTask,
    deleteTask,
    retryTask,
    reloadTasks: loadTasks
  };
};

// Agents management hook
export const useAgents = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const { apiCall } = useApi();

  const loadAgents = useCallback(async () => {
    try {
      const data = await apiCall('/api/agents');
      setAgents(data);
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setLoading(false);
    }
  }, [apiCall]);

  const getAgentPerformance = useCallback(async (agentId) => {
    try {
      return await apiCall(`/api/agents/${agentId}/performance`);
    } catch (error) {
      console.error('Failed to get agent performance:', error);
      throw error;
    }
  }, [apiCall]);

  const getAgentTasks = useCallback(async (agentId) => {
    try {
      return await apiCall(`/api/agents/${agentId}/tasks`);
    } catch (error) {
      console.error('Failed to get agent tasks:', error);
      throw error;
    }
  }, [apiCall]);

  useEffect(() => {
    loadAgents();
  }, [loadAgents]);

  return {
    agents,
    loading,
    getAgentPerformance,
    getAgentTasks,
    reloadAgents: loadAgents
  };
};

// Local storage hook
export const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error('Error reading from localStorage:', error);
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error('Error writing to localStorage:', error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue];
};

// Performance monitoring hook
export const usePerformance = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const { apiCall } = useApi();

  const loadMetrics = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiCall('/api/analytics');
      setMetrics(data);
    } catch (error) {
      console.error('Failed to load performance metrics:', error);
    } finally {
      setLoading(false);
    }
  }, [apiCall]);

  useEffect(() => {
    loadMetrics();
    // Refresh metrics every 30 seconds
    const interval = setInterval(loadMetrics, 30000);
    return () => clearInterval(interval);
  }, [loadMetrics]);

  return { metrics, loading, refreshMetrics: loadMetrics };
};

// Apple Silicon detection hook
export const useAppleSilicon = () => {
  const [systemInfo, setSystemInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const { apiCall } = useApi();

  const detectSystem = useCallback(async () => {
    try {
      const data = await apiCall('/api/apple-silicon/detect');
      setSystemInfo(data);
    } catch (error) {
      console.error('Failed to detect Apple Silicon:', error);
      setSystemInfo({ is_apple_silicon: false, error: error.message });
    } finally {
      setLoading(false);
    }
  }, [apiCall]);

  const optimizeSystem = useCallback(async () => {
    try {
      return await apiCall('/api/apple-silicon/optimize', { method: 'POST' });
    } catch (error) {
      console.error('Failed to optimize system:', error);
      throw error;
    }
  }, [apiCall]);

  const getPerformance = useCallback(async () => {
    try {
      return await apiCall('/api/apple-silicon/performance');
    } catch (error) {
      console.error('Failed to get performance:', error);
      throw error;
    }
  }, [apiCall]);

  useEffect(() => {
    detectSystem();
  }, [detectSystem]);

  return {
    systemInfo,
    loading,
    optimizeSystem,
    getPerformance,
    redetect: detectSystem
  };
};

// Keyboard shortcuts hook
export const useKeyboardShortcuts = (shortcuts) => {
  useEffect(() => {
    const handleKeyDown = (event) => {
      const key = event.key.toLowerCase();
      const ctrl = event.ctrlKey || event.metaKey;
      const shift = event.shiftKey;
      const alt = event.altKey;

      for (const shortcut of shortcuts) {
        const matches =
          shortcut.key === key &&
          (shortcut.ctrl || false) === ctrl &&
          (shortcut.shift || false) === shift &&
          (shortcut.alt || false) === alt;

        if (matches) {
          event.preventDefault();
          shortcut.action();
          break;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
};

// Debounced value hook
export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// Intersection observer hook
export const useIntersectionObserver = (options = {}) => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const targetRef = useRef();

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
    }, options);

    if (targetRef.current) {
      observer.observe(targetRef.current);
    }

    return () => {
      observer.disconnect();
    };
  }, [options]);

  return [targetRef, isIntersecting];
};

// Previous value hook
export const usePrevious = (value) => {
  const ref = useRef();
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
};

// Online status hook
export const useOnlineStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
};

// Focus trap hook
export const useFocusTrap = (isActive) => {
  const containerRef = useRef();

  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement?.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement?.focus();
            e.preventDefault();
          }
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);
    firstElement?.focus();

    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  }, [isActive]);

  return containerRef;
};

// Interval hook
export const useInterval = (callback, delay) => {
  const savedCallback = useRef();

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay !== null) {
      const id = setInterval(() => savedCallback.current(), delay);
      return () => clearInterval(id);
    }
  }, [delay]);
};

// System status hook
export const useSystemStatus = () => {
  const [status, setStatus] = useState(null);
  const { apiCall } = useApi();

  const checkStatus = useCallback(async () => {
    try {
      const data = await apiCall('/api/status');
      setStatus(data);
    } catch (error) {
      setStatus({ status: 'error', error: error.message });
    }
  }, [apiCall]);

  useInterval(checkStatus, 30000); // Check every 30 seconds

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  return { status, refreshStatus: checkStatus };
};

export default {
  useWebSocket,
  useApi,
  useTasks,
  useAgents,
  useLocalStorage,
  usePerformance,
  useAppleSilicon,
  useKeyboardShortcuts,
  useDebounce,
  useIntersectionObserver,
  usePrevious,
  useOnlineStatus,
  useFocusTrap,
  useInterval,
  useSystemStatus
};
