// VirtuAI Office - Data Formatting Utilities

/**
 * Format date and time strings for display
 */
export const formatDate = (dateString, options = {}) => {
  if (!dateString) return 'Not set';
  
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return 'Invalid date';
  
  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    ...options
  };
  
  return date.toLocaleString(undefined, defaultOptions);
};

/**
 * Format relative time (e.g., "2 hours ago")
 */
export const formatRelativeTime = (dateString) => {
  if (!dateString) return 'Unknown';
  
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffSeconds < 60) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  
  return formatDate(dateString, { year: 'numeric', month: 'short', day: 'numeric' });
};

/**
 * Format duration in human-readable format
 */
export const formatDuration = (seconds) => {
  if (!seconds || seconds < 0) return '0 seconds';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;
  
  const parts = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (remainingSeconds > 0 || parts.length === 0) parts.push(`${remainingSeconds}s`);
  
  return parts.join(' ');
};

/**
 * Format effort hours in human-readable format
 */
export const formatEffort = (hours) => {
  if (!hours || hours <= 0) return '0 hours';
  
  if (hours < 1) {
    const minutes = Math.round(hours * 60);
    return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
  }
  
  if (hours === 1) return '1 hour';
  
  if (hours < 24) {
    return `${hours} hour${hours !== 1 ? 's' : ''}`;
  }
  
  const days = Math.floor(hours / 24);
  const remainingHours = hours % 24;
  
  if (remainingHours === 0) {
    return `${days} day${days !== 1 ? 's' : ''}`;
  }
  
  return `${days}d ${remainingHours}h`;
};

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text, maxLength = 100, suffix = '...') => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  
  return text.substring(0, maxLength - suffix.length) + suffix;
};

/**
 * Capitalize first letter of each word
 */
export const toTitleCase = (str) => {
  if (!str) return '';
  
  return str
    .toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Convert snake_case to Title Case
 */
export const snakeToTitle = (str) => {
  if (!str) return '';
  
  return str
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Format task status for display
 */
export const formatTaskStatus = (status) => {
  const statusMap = {
    pending: 'Pending',
    in_progress: 'In Progress',
    completed: 'Completed',
    failed: 'Failed'
  };
  
  return statusMap[status] || toTitleCase(status);
};

/**
 * Format priority for display
 */
export const formatPriority = (priority) => {
  const priorityMap = {
    low: 'Low',
    medium: 'Medium',
    high: 'High',
    urgent: 'Urgent'
  };
  
  return priorityMap[priority] || toTitleCase(priority);
};

/**
 * Format agent type for display
 */
export const formatAgentType = (type) => {
  const typeMap = {
    product_manager: 'Product Manager',
    frontend_developer: 'Frontend Developer',
    backend_developer: 'Backend Developer',
    ui_ux_designer: 'UI/UX Designer',
    qa_tester: 'QA Tester',
    boss_ai: 'Boss AI'
  };
  
  return typeMap[type] || snakeToTitle(type);
};

/**
 * Format numbers with proper separators
 */
export const formatNumber = (num, options = {}) => {
  if (num === null || num === undefined) return '0';
  
  const defaultOptions = {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
    ...options
  };
  
  return new Intl.NumberFormat(undefined, defaultOptions).format(num);
};

/**
 * Format percentage values
 */
export const formatPercentage = (value, decimals = 1) => {
  if (value === null || value === undefined) return '0%';
  
  const percentage = typeof value === 'number' ? value * 100 : parseFloat(value) * 100;
  return `${percentage.toFixed(decimals)}%`;
};

/**
 * Format file size in human-readable format
 */
export const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B';
  
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
};

/**
 * Format memory usage
 */
export const formatMemory = (bytes) => {
  if (!bytes || bytes === 0) return '0 MB';
  
  const mb = bytes / (1024 * 1024);
  const gb = mb / 1024;
  
  if (gb >= 1) {
    return `${gb.toFixed(1)} GB`;
  }
  
  return `${mb.toFixed(0)} MB`;
};

/**
 * Format Apple Silicon chip names
 */
export const formatChipType = (chipType) => {
  if (!chipType) return 'Unknown';
  
  const chipMap = {
    m1: 'Apple M1',
    m1_pro: 'Apple M1 Pro',
    m1_max: 'Apple M1 Max',
    m1_ultra: 'Apple M1 Ultra',
    m2: 'Apple M2',
    m2_pro: 'Apple M2 Pro',
    m2_max: 'Apple M2 Max',
    m2_ultra: 'Apple M2 Ultra',
    m3: 'Apple M3',
    m3_pro: 'Apple M3 Pro',
    m3_max: 'Apple M3 Max',
    intel: 'Intel',
    unknown: 'Unknown'
  };
  
  return chipMap[chipType.toLowerCase()] || toTitleCase(chipType);
};

/**
 * Format performance scores
 */
export const formatPerformanceScore = (score) => {
  if (score === null || score === undefined) return 'N/A';
  
  const percentage = Math.round(score * 100);
  
  if (percentage >= 90) return `${percentage}% (Excellent)`;
  if (percentage >= 75) return `${percentage}% (Good)`;
  if (percentage >= 60) return `${percentage}% (Fair)`;
  return `${percentage}% (Needs Improvement)`;
};

/**
 * Format tokens per second
 */
export const formatTokensPerSecond = (tokensPerSecond) => {
  if (!tokensPerSecond || tokensPerSecond <= 0) return '0 tokens/sec';
  
  if (tokensPerSecond >= 1000) {
    return `${(tokensPerSecond / 1000).toFixed(1)}k tokens/sec`;
  }
  
  return `${tokensPerSecond.toFixed(1)} tokens/sec`;
};

/**
 * Format task complexity
 */
export const formatComplexity = (complexity) => {
  const complexityMap = {
    simple: '🟢 Simple',
    medium: '🟡 Medium',
    complex: '🔴 Complex',
    epic: '🟣 Epic'
  };
  
  return complexityMap[complexity] || toTitleCase(complexity);
};

/**
 * Format collaboration type
 */
export const formatCollaborationType = (type) => {
  const typeMap = {
    independent: '👤 Independent',
    sequential: '➡️ Sequential',
    parallel: '⚡ Parallel',
    review: '👁️ Review'
  };
  
  return typeMap[type] || toTitleCase(type);
};

/**
 * Format system status
 */
export const formatSystemStatus = (status) => {
  const statusMap = {
    healthy: '✅ Healthy',
    warning: '⚠️ Warning',
    critical: '🔴 Critical',
    unknown: '❓ Unknown'
  };
  
  return statusMap[status] || toTitleCase(status);
};

/**
 * Format thermal state
 */
export const formatThermalState = (state) => {
  const stateMap = {
    normal: '🟢 Normal',
    elevated: '🟡 Elevated',
    throttling: '🔴 Throttling',
    unknown: '❓ Unknown'
  };
  
  return stateMap[state] || toTitleCase(state);
};

/**
 * Format memory pressure
 */
export const formatMemoryPressure = (pressure) => {
  const pressureMap = {
    normal: '🟢 Normal',
    warning: '🟡 Warning',
    critical: '🔴 Critical',
    unknown: '❓ Unknown'
  };
  
  return pressureMap[pressure] || toTitleCase(pressure);
};

/**
 * Format power mode
 */
export const formatPowerMode = (mode) => {
  const modeMap = {
    automatic: '⚡ Automatic',
    power_nap: '😴 Power Nap',
    standard: '🔋 Standard',
    high_performance: '🚀 High Performance',
    unknown: '❓ Unknown'
  };
  
  return modeMap[mode] || toTitleCase(mode);
};

/**
 * Format code language for syntax highlighting
 */
export const formatLanguage = (language) => {
  const languageMap = {
    js: 'JavaScript',
    jsx: 'React JSX',
    ts: 'TypeScript',
    tsx: 'React TSX',
    py: 'Python',
    python: 'Python',
    html: 'HTML',
    css: 'CSS',
    scss: 'SCSS',
    json: 'JSON',
    yaml: 'YAML',
    yml: 'YAML',
    md: 'Markdown',
    sql: 'SQL',
    bash: 'Bash',
    shell: 'Shell'
  };
  
  return languageMap[language.toLowerCase()] || toTitleCase(language);
};

/**
 * Format API endpoint paths
 */
export const formatApiPath = (path) => {
  if (!path) return '';
  
  // Ensure path starts with /
  if (!path.startsWith('/')) {
    path = '/' + path;
  }
  
  return path;
};

/**
 * Format search query highlighting
 */
export const highlightSearchTerm = (text, searchTerm) => {
  if (!text || !searchTerm) return text;
  
  const regex = new RegExp(`(${searchTerm})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
};

/**
 * Format task estimate ranges
 */
export const formatEstimateRange = (min, max) => {
  if (!min && !max) return 'No estimate';
  if (!max) return formatEffort(min);
  if (!min) return `Up to ${formatEffort(max)}`;
  
  if (min === max) return formatEffort(min);
  
  return `${formatEffort(min)} - ${formatEffort(max)}`;
};

/**
 * Format confidence score
 */
export const formatConfidence = (confidence) => {
  if (confidence === null || confidence === undefined) return 'Unknown';
  
  const percentage = Math.round(confidence * 100);
  
  if (percentage >= 90) return `${percentage}% (Very High)`;
  if (percentage >= 75) return `${percentage}% (High)`;
  if (percentage >= 50) return `${percentage}% (Medium)`;
  if (percentage >= 25) return `${percentage}% (Low)`;
  return `${percentage}% (Very Low)`;
};

/**
 * Format error messages for user display
 */
export const formatErrorMessage = (error) => {
  if (!error) return 'Unknown error occurred';
  
  if (typeof error === 'string') return error;
  
  if (error.message) return error.message;
  
  if (error.detail) return error.detail;
  
  return 'An unexpected error occurred';
};

/**
 * Format validation errors
 */
export const formatValidationErrors = (errors) => {
  if (!errors || !Array.isArray(errors)) return [];
  
  return errors.map(error => {
    if (typeof error === 'string') return error;
    
    const field = error.loc ? error.loc.join('.') : 'field';
    const message = error.msg || 'Invalid value';
    
    return `${toTitleCase(field)}: ${message}`;
  });
};

/**
 * Format JSON for display
 */
export const formatJson = (obj, indent = 2) => {
  if (!obj) return '';
  
  try {
    return JSON.stringify(obj, null, indent);
  } catch (e) {
    return String(obj);
  }
};

/**
 * Format list of items with proper grammar
 */
export const formatList = (items, conjunction = 'and') => {
  if (!items || !Array.isArray(items)) return '';
  
  if (items.length === 0) return '';
  if (items.length === 1) return items[0];
  if (items.length === 2) return `${items[0]} ${conjunction} ${items[1]}`;
  
  const lastItem = items[items.length - 1];
  const otherItems = items.slice(0, -1);
  
  return `${otherItems.join(', ')}, ${conjunction} ${lastItem}`;
};
