// VirtuAI Office - Application Constants

// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  WEBSOCKET_URL: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws',
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000 // 1 second
};

// Agent Configuration
export const AGENT_TYPES = {
  PRODUCT_MANAGER: 'product_manager',
  FRONTEND_DEVELOPER: 'frontend_developer',
  BACKEND_DEVELOPER: 'backend_developer',
  UI_UX_DESIGNER: 'ui_ux_designer',
  QA_TESTER: 'qa_tester',
  BOSS_AI: 'boss_ai'
};

export const AGENT_INFO = {
  [AGENT_TYPES.PRODUCT_MANAGER]: {
    name: 'Alice Chen',
    title: 'Product Manager',
    icon: '👩‍💼',
    description: 'Senior Product Manager with expertise in user stories, requirements, and project planning',
    expertise: ['user stories', 'requirements', 'product roadmap', 'stakeholder analysis', 'project planning', 'agile', 'scrum'],
    color: 'purple',
    bgColor: 'bg-purple-100',
    textColor: 'text-purple-800',
    borderColor: 'border-purple-300'
  },
  [AGENT_TYPES.FRONTEND_DEVELOPER]: {
    name: 'Marcus Dev',
    title: 'Frontend Developer',
    icon: '👨‍💻',
    description: 'Senior Frontend Developer specializing in React, modern UI frameworks, and responsive design',
    expertise: ['react', 'javascript', 'typescript', 'css', 'html', 'responsive design', 'ui components', 'state management', 'testing'],
    color: 'blue',
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-800',
    borderColor: 'border-blue-300'
  },
  [AGENT_TYPES.BACKEND_DEVELOPER]: {
    name: 'Sarah Backend',
    title: 'Backend Developer',
    icon: '👩‍💻',
    description: 'Senior Backend Developer with expertise in Python, APIs, databases, and system architecture',
    expertise: ['python', 'fastapi', 'django', 'postgresql', 'mongodb', 'rest apis', 'authentication', 'database design', 'testing', 'docker'],
    color: 'green',
    bgColor: 'bg-green-100',
    textColor: 'text-green-800',
    borderColor: 'border-green-300'
  },
  [AGENT_TYPES.UI_UX_DESIGNER]: {
    name: 'Luna Design',
    title: 'UI/UX Designer',
    icon: '🎨',
    description: 'Senior UI/UX Designer with expertise in user-centered design, wireframing, and design systems',
    expertise: ['ui design', 'ux design', 'wireframing', 'prototyping', 'design systems', 'accessibility', 'user research', 'figma', 'responsive design'],
    color: 'pink',
    bgColor: 'bg-pink-100',
    textColor: 'text-pink-800',
    borderColor: 'border-pink-300'
  },
  [AGENT_TYPES.QA_TESTER]: {
    name: 'TestBot QA',
    title: 'QA Tester',
    icon: '🔍',
    description: 'Senior QA Engineer with expertise in test planning, automation, and quality assurance',
    expertise: ['test planning', 'test automation', 'manual testing', 'pytest', 'jest', 'selenium', 'api testing', 'performance testing', 'bug reporting'],
    color: 'orange',
    bgColor: 'bg-orange-100',
    textColor: 'text-orange-800',
    borderColor: 'border-orange-300'
  },
  [AGENT_TYPES.BOSS_AI]: {
    name: 'Boss AI',
    title: 'AI Orchestrator',
    icon: '🧠',
    description: 'AI orchestration system that coordinates team activities and optimizes task assignments',
    expertise: ['task analysis', 'agent coordination', 'performance optimization', 'team insights', 'workload balancing'],
    color: 'purple',
    bgColor: 'bg-purple-100',
    textColor: 'text-purple-800',
    borderColor: 'border-purple-300'
  }
};

// Task Configuration
export const TASK_STATUS = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  FAILED: 'failed'
};

export const TASK_PRIORITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  URGENT: 'urgent'
};

export const TASK_STATUS_CONFIG = {
  [TASK_STATUS.PENDING]: {
    label: 'Pending',
    icon: '🟡',
    color: 'yellow',
    bgColor: 'bg-yellow-100',
    textColor: 'text-yellow-800',
    borderColor: 'border-yellow-300'
  },
  [TASK_STATUS.IN_PROGRESS]: {
    label: 'In Progress',
    icon: '🔵',
    color: 'blue',
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-800',
    borderColor: 'border-blue-300'
  },
  [TASK_STATUS.COMPLETED]: {
    label: 'Completed',
    icon: '🟢',
    color: 'green',
    bgColor: 'bg-green-100',
    textColor: 'text-green-800',
    borderColor: 'border-green-300'
  },
  [TASK_STATUS.FAILED]: {
    label: 'Failed',
    icon: '🔴',
    color: 'red',
    bgColor: 'bg-red-100',
    textColor: 'text-red-800',
    borderColor: 'border-red-300'
  }
};

export const TASK_PRIORITY_CONFIG = {
  [TASK_PRIORITY.LOW]: {
    label: 'Low',
    color: 'gray',
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-600',
    borderColor: 'border-gray-300',
    weight: 1
  },
  [TASK_PRIORITY.MEDIUM]: {
    label: 'Medium',
    color: 'blue',
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-600',
    borderColor: 'border-blue-300',
    weight: 2
  },
  [TASK_PRIORITY.HIGH]: {
    label: 'High',
    color: 'orange',
    bgColor: 'bg-orange-100',
    textColor: 'text-orange-600',
    borderColor: 'border-orange-300',
    weight: 3
  },
  [TASK_PRIORITY.URGENT]: {
    label: 'Urgent',
    color: 'red',
    bgColor: 'bg-red-100',
    textColor: 'text-red-600',
    borderColor: 'border-red-300',
    weight: 4
  }
};

// Apple Silicon Configuration
export const APPLE_SILICON_CHIPS = {
  M1: 'm1',
  M1_PRO: 'm1_pro',
  M1_MAX: 'm1_max',
  M1_ULTRA: 'm1_ultra',
  M2: 'm2',
  M2_PRO: 'm2_pro',
  M2_MAX: 'm2_max',
  M2_ULTRA: 'm2_ultra',
  M3: 'm3',
  M3_PRO: 'm3_pro',
  M3_MAX: 'm3_max',
  INTEL: 'intel',
  UNKNOWN: 'unknown'
};

export const CHIP_DISPLAY_NAMES = {
  [APPLE_SILICON_CHIPS.M1]: 'Apple M1',
  [APPLE_SILICON_CHIPS.M1_PRO]: 'Apple M1 Pro',
  [APPLE_SILICON_CHIPS.M1_MAX]: 'Apple M1 Max',
  [APPLE_SILICON_CHIPS.M1_ULTRA]: 'Apple M1 Ultra',
  [APPLE_SILICON_CHIPS.M2]: 'Apple M2',
  [APPLE_SILICON_CHIPS.M2_PRO]: 'Apple M2 Pro',
  [APPLE_SILICON_CHIPS.M2_MAX]: 'Apple M2 Max',
  [APPLE_SILICON_CHIPS.M2_ULTRA]: 'Apple M2 Ultra',
  [APPLE_SILICON_CHIPS.M3]: 'Apple M3',
  [APPLE_SILICON_CHIPS.M3_PRO]: 'Apple M3 Pro',
  [APPLE_SILICON_CHIPS.M3_MAX]: 'Apple M3 Max',
  [APPLE_SILICON_CHIPS.INTEL]: 'Intel Mac',
  [APPLE_SILICON_CHIPS.UNKNOWN]: 'Unknown'
};

// AI Model Configuration
export const AI_MODELS = {
  LLAMA2_7B: 'llama2:7b',
  LLAMA2_13B: 'llama2:13b',
  LLAMA2_70B: 'llama2:70b',
  CODELLAMA_7B: 'codellama:7b',
  CODELLAMA_13B: 'codellama:13b',
  CODELLAMA_34B: 'codellama:34b'
};

export const MODEL_INFO = {
  [AI_MODELS.LLAMA2_7B]: {
    name: 'Llama 2 7B',
    size: '3.8 GB',
    complexity: 'medium',
    speed: 'fast',
    minRam: 8,
    description: 'Fast and efficient general-purpose model'
  },
  [AI_MODELS.LLAMA2_13B]: {
    name: 'Llama 2 13B',
    size: '7.3 GB',
    complexity: 'high',
    speed: 'medium',
    minRam: 16,
    description: 'Higher quality responses, requires more memory'
  },
  [AI_MODELS.LLAMA2_70B]: {
    name: 'Llama 2 70B',
    size: '39 GB',
    complexity: 'very_high',
    speed: 'slow',
    minRam: 64,
    description: 'Highest quality, requires significant resources'
  },
  [AI_MODELS.CODELLAMA_7B]: {
    name: 'Code Llama 7B',
    size: '3.8 GB',
    complexity: 'medium',
    speed: 'fast',
    minRam: 8,
    description: 'Optimized for code generation tasks'
  },
  [AI_MODELS.CODELLAMA_13B]: {
    name: 'Code Llama 13B',
    size: '7.3 GB',
    complexity: 'high',
    speed: 'medium',
    minRam: 16,
    description: 'Higher quality code generation'
  },
  [AI_MODELS.CODELLAMA_34B]: {
    name: 'Code Llama 34B',
    size: '19 GB',
    complexity: 'very_high',
    speed: 'slow',
    minRam: 32,
    description: 'Professional-grade code generation'
  }
};

// Performance Thresholds
export const PERFORMANCE_THRESHOLDS = {
  CPU_HIGH: 80,
  CPU_MEDIUM: 60,
  MEMORY_HIGH: 85,
  MEMORY_MEDIUM: 70,
  INFERENCE_GOOD: 10, // tokens per second
  INFERENCE_EXCELLENT: 20
};

// Notification Configuration
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info'
};

export const NOTIFICATION_DURATIONS = {
  SHORT: 3000,
  MEDIUM: 5000,
  LONG: 8000,
  PERSISTENT: 0
};

// WebSocket Event Types
export const WS_EVENTS = {
  TASK_UPDATE: 'task_update',
  TASK_COMPLETED: 'task_completed',
  TASK_FAILED: 'task_failed',
  AGENT_STATUS: 'agent_status',
  SYSTEM_STATUS: 'system_status',
  PERFORMANCE_UPDATE: 'performance_update'
};

// Local Storage Keys
export const STORAGE_KEYS = {
  USER_PREFERENCES: 'virtuai-user-preferences',
  ONBOARDING_COMPLETED: 'virtuai-onboarding-completed',
  TUTORIAL_COMPLETED: 'virtuai-tutorial-completed',
  THEME_PREFERENCE: 'virtuai-theme',
  SIDEBAR_COLLAPSED: 'virtuai-sidebar-collapsed',
  NOTIFICATION_SETTINGS: 'virtuai-notifications'
};

// UI Configuration
export const UI_CONFIG = {
  SIDEBAR_WIDTH: 280,
  SIDEBAR_COLLAPSED_WIDTH: 80,
  HEADER_HEIGHT: 64,
  MOBILE_BREAKPOINT: 768,
  TABLET_BREAKPOINT: 1024,
  DESKTOP_BREAKPOINT: 1280
};

// Pagination Defaults
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100]
};

// Time Formats
export const TIME_FORMATS = {
  SHORT_DATE: 'MMM d, yyyy',
  LONG_DATE: 'MMMM d, yyyy',
  DATE_TIME: 'MMM d, yyyy h:mm a',
  TIME_ONLY: 'h:mm a',
  ISO_DATE: 'yyyy-MM-dd',
  RELATIVE: 'relative'
};

// Keyboard Shortcuts
export const KEYBOARD_SHORTCUTS = {
  CREATE_TASK: 'cmd+n',
  SEARCH: 'cmd+k',
  HELP: '?',
  ESCAPE: 'Escape',
  SAVE: 'cmd+s'
};

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network connection error. Please check your connection.',
  SERVER_ERROR: 'Server error. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  PERMISSION_ERROR: 'You do not have permission to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  TIMEOUT: 'Request timed out. Please try again.',
  UNKNOWN: 'An unexpected error occurred.'
};

// Success Messages
export const SUCCESS_MESSAGES = {
  TASK_CREATED: 'Task created successfully!',
  TASK_UPDATED: 'Task updated successfully!',
  TASK_DELETED: 'Task deleted successfully!',
  SETTINGS_SAVED: 'Settings saved successfully!',
  OPTIMIZATION_APPLIED: 'Optimization applied successfully!',
  MODEL_DOWNLOADED: 'Model downloaded successfully!'
};

// Feature Flags
export const FEATURE_FLAGS = {
  APPLE_SILICON_OPTIMIZATION: true,
  BOSS_AI_INSIGHTS: true,
  REAL_TIME_COLLABORATION: true,
  PWA_FEATURES: true,
  TUTORIAL_SYSTEM: true,
  PERFORMANCE_MONITORING: true,
  ADVANCED_ANALYTICS: true
};

// Development Configuration
export const DEV_CONFIG = {
  ENABLE_LOGS: process.env.NODE_ENV === 'development',
  MOCK_DATA: process.env.REACT_APP_MOCK_DATA === 'true',
  SKIP_AUTH: process.env.REACT_APP_SKIP_AUTH === 'true',
  DEBUG_PERFORMANCE: process.env.REACT_APP_DEBUG_PERFORMANCE === 'true'
};

// Export default configuration object
export default {
  API_CONFIG,
  AGENT_TYPES,
  AGENT_INFO,
  TASK_STATUS,
  TASK_PRIORITY,
  TASK_STATUS_CONFIG,
  TASK_PRIORITY_CONFIG,
  APPLE_SILICON_CHIPS,
  CHIP_DISPLAY_NAMES,
  AI_MODELS,
  MODEL_INFO,
  PERFORMANCE_THRESHOLDS,
  NOTIFICATION_TYPES,
  NOTIFICATION_DURATIONS,
  WS_EVENTS,
  STORAGE_KEYS,
  UI_CONFIG,
  PAGINATION,
  TIME_FORMATS,
  KEYBOARD_SHORTCUTS,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
  FEATURE_FLAGS,
  DEV_CONFIG
};f
