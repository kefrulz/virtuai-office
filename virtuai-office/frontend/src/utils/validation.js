// VirtuAI Office - Frontend Validation Utilities
// Comprehensive validation functions for forms, inputs, and data

/**
 * Task validation utilities
 */
export const taskValidation = {
  // Validate task title
  title: (title) => {
    const errors = [];
    
    if (!title || title.trim().length === 0) {
      errors.push('Title is required');
    } else if (title.trim().length < 3) {
      errors.push('Title must be at least 3 characters long');
    } else if (title.trim().length > 200) {
      errors.push('Title cannot exceed 200 characters');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Validate task description
  description: (description) => {
    const errors = [];
    
    if (!description || description.trim().length === 0) {
      errors.push('Description is required');
    } else if (description.trim().length < 10) {
      errors.push('Description must be at least 10 characters long');
    } else if (description.trim().length > 5000) {
      errors.push('Description cannot exceed 5000 characters');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Validate task priority
  priority: (priority) => {
    const validPriorities = ['low', 'medium', 'high', 'urgent'];
    const errors = [];
    
    if (!priority) {
      errors.push('Priority is required');
    } else if (!validPriorities.includes(priority)) {
      errors.push('Priority must be one of: low, medium, high, urgent');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Validate complete task object
  task: (task) => {
    const titleValidation = taskValidation.title(task.title);
    const descriptionValidation = taskValidation.description(task.description);
    const priorityValidation = taskValidation.priority(task.priority);
    
    const allErrors = [
      ...titleValidation.errors,
      ...descriptionValidation.errors,
      ...priorityValidation.errors
    ];
    
    return {
      isValid: allErrors.length === 0,
      errors: allErrors,
      fieldErrors: {
        title: titleValidation.errors,
        description: descriptionValidation.errors,
        priority: priorityValidation.errors
      }
    };
  }
};

/**
 * Project validation utilities
 */
export const projectValidation = {
  // Validate project name
  name: (name) => {
    const errors = [];
    
    if (!name || name.trim().length === 0) {
      errors.push('Project name is required');
    } else if (name.trim().length < 2) {
      errors.push('Project name must be at least 2 characters long');
    } else if (name.trim().length > 100) {
      errors.push('Project name cannot exceed 100 characters');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Validate project description
  description: (description) => {
    const errors = [];
    
    if (description && description.length > 1000) {
      errors.push('Project description cannot exceed 1000 characters');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Validate complete project object
  project: (project) => {
    const nameValidation = projectValidation.name(project.name);
    const descriptionValidation = projectValidation.description(project.description);
    
    const allErrors = [
      ...nameValidation.errors,
      ...descriptionValidation.errors
    ];
    
    return {
      isValid: allErrors.length === 0,
      errors: allErrors,
      fieldErrors: {
        name: nameValidation.errors,
        description: descriptionValidation.errors
      }
    };
  }
};

/**
 * General input validation utilities
 */
export const inputValidation = {
  // Validate email format
  email: (email) => {
    const errors = [];
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!email || email.trim().length === 0) {
      errors.push('Email is required');
    } else if (!emailRegex.test(email)) {
      errors.push('Please enter a valid email address');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Validate URL format
  url: (url) => {
    const errors = [];
    
    if (url && url.trim().length > 0) {
      try {
        new URL(url);
      } catch (e) {
        errors.push('Please enter a valid URL');
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Validate required field
  required: (value, fieldName = 'Field') => {
    const errors = [];
    
    if (!value || (typeof value === 'string' && value.trim().length === 0)) {
      errors.push(`${fieldName} is required`);
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Validate minimum length
  minLength: (value, min, fieldName = 'Field') => {
    const errors = [];
    
    if (value && value.length < min) {
      errors.push(`${fieldName} must be at least ${min} characters long`);
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Validate maximum length
  maxLength: (value, max, fieldName = 'Field') => {
    const errors = [];
    
    if (value && value.length > max) {
      errors.push(`${fieldName} cannot exceed ${max} characters`);
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Validate numeric input
  number: (value, fieldName = 'Field') => {
    const errors = [];
    
    if (value !== null && value !== undefined && value !== '') {
      const num = Number(value);
      if (isNaN(num)) {
        errors.push(`${fieldName} must be a valid number`);
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Validate number range
  numberRange: (value, min, max, fieldName = 'Field') => {
    const errors = [];
    const num = Number(value);
    
    if (!isNaN(num)) {
      if (min !== null && num < min) {
        errors.push(`${fieldName} must be at least ${min}`);
      }
      if (max !== null && num > max) {
        errors.push(`${fieldName} cannot exceed ${max}`);
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }
};

/**
 * API response validation
 */
export const apiValidation = {
  // Validate API response structure
  response: (response, requiredFields = []) => {
    const errors = [];
    
    if (!response || typeof response !== 'object') {
      errors.push('Invalid response format');
      return { isValid: false, errors };
    }
    
    requiredFields.forEach(field => {
      if (!(field in response)) {
        errors.push(`Missing required field: ${field}`);
      }
    });
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Validate task response
  taskResponse: (response) => {
    return apiValidation.response(response, [
      'id', 'title', 'description', 'status', 'priority', 'created_at'
    ]);
  },

  // Validate agent response
  agentResponse: (response) => {
    return apiValidation.response(response, [
      'id', 'name', 'type', 'description', 'expertise', 'is_active'
    ]);
  }
};

/**
 * Form validation helpers
 */
export const formValidation = {
  // Validate entire form
  validateForm: (formData, validationRules) => {
    const fieldErrors = {};
    const allErrors = [];
    
    Object.keys(validationRules).forEach(fieldName => {
      const rules = validationRules[fieldName];
      const value = formData[fieldName];
      const fieldValidationErrors = [];
      
      rules.forEach(rule => {
        if (typeof rule === 'function') {
          const result = rule(value);
          if (!result.isValid) {
            fieldValidationErrors.push(...result.errors);
          }
        } else if (typeof rule === 'object') {
          const { validator, params = [] } = rule;
          const result = validator(value, ...params);
          if (!result.isValid) {
            fieldValidationErrors.push(...result.errors);
          }
        }
      });
      
      if (fieldValidationErrors.length > 0) {
        fieldErrors[fieldName] = fieldValidationErrors;
        allErrors.push(...fieldValidationErrors);
      }
    });
    
    return {
      isValid: allErrors.length === 0,
      errors: allErrors,
      fieldErrors
    };
  },

  // Get first error for a field
  getFirstError: (fieldErrors, fieldName) => {
    return fieldErrors[fieldName] ? fieldErrors[fieldName][0] : null;
  },

  // Check if field has errors
  hasError: (fieldErrors, fieldName) => {
    return fieldErrors[fieldName] && fieldErrors[fieldName].length > 0;
  }
};

/**
 * Real-time validation hooks
 */
export const useValidation = (initialData = {}, validationRules = {}) => {
  const [data, setData] = useState(initialData);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  
  const validateField = useCallback((fieldName, value) => {
    const rules = validationRules[fieldName];
    if (!rules) return { isValid: true, errors: [] };
    
    const fieldValidationErrors = [];
    
    rules.forEach(rule => {
      if (typeof rule === 'function') {
        const result = rule(value);
        if (!result.isValid) {
          fieldValidationErrors.push(...result.errors);
        }
      }
    });
    
    return {
      isValid: fieldValidationErrors.length === 0,
      errors: fieldValidationErrors
    };
  }, [validationRules]);
  
  const updateField = useCallback((fieldName, value) => {
    setData(prev => ({ ...prev, [fieldName]: value }));
    
    // Validate if field has been touched
    if (touched[fieldName]) {
      const validation = validateField(fieldName, value);
      setErrors(prev => ({
        ...prev,
        [fieldName]: validation.errors
      }));
    }
  }, [touched, validateField]);
  
  const touchField = useCallback((fieldName) => {
    setTouched(prev => ({ ...prev, [fieldName]: true }));
    
    // Validate on touch
    const validation = validateField(fieldName, data[fieldName]);
    setErrors(prev => ({
      ...prev,
      [fieldName]: validation.errors
    }));
  }, [data, validateField]);
  
  const validateAll = useCallback(() => {
    const result = formValidation.validateForm(data, validationRules);
    setErrors(result.fieldErrors);
    setTouched(Object.keys(validationRules).reduce((acc, key) => {
      acc[key] = true;
      return acc;
    }, {}));
    return result;
  }, [data, validationRules]);
  
  const reset = useCallback(() => {
    setData(initialData);
    setErrors({});
    setTouched({});
  }, [initialData]);
  
  return {
    data,
    errors,
    touched,
    updateField,
    touchField,
    validateAll,
    reset,
    isValid: Object.keys(errors).length === 0,
    hasErrors: Object.values(errors).some(fieldErrors => fieldErrors.length > 0)
  };
};

/**
 * Sanitization utilities
 */
export const sanitization = {
  // Sanitize HTML input
  html: (input) => {
    if (typeof input !== 'string') return input;
    
    return input
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;');
  },

  // Sanitize for SQL (basic - use parameterized queries in production)
  sql: (input) => {
    if (typeof input !== 'string') return input;
    
    return input.replace(/['";\\]/g, '');
  },

  // Trim whitespace
  trim: (input) => {
    if (typeof input !== 'string') return input;
    return input.trim();
  },

  // Remove special characters
  alphanumeric: (input) => {
    if (typeof input !== 'string') return input;
    return input.replace(/[^a-zA-Z0-9\s]/g, '');
  },

  // Sanitize filename
  filename: (input) => {
    if (typeof input !== 'string') return input;
    return input.replace(/[^a-zA-Z0-9._-]/g, '');
  }
};

/**
 * Common validation rule presets
 */
export const validationRules = {
  taskTitle: [
    inputValidation.required,
    (value) => inputValidation.minLength(value, 3, 'Title'),
    (value) => inputValidation.maxLength(value, 200, 'Title')
  ],
  
  taskDescription: [
    inputValidation.required,
    (value) => inputValidation.minLength(value, 10, 'Description'),
    (value) => inputValidation.maxLength(value, 5000, 'Description')
  ],
  
  projectName: [
    inputValidation.required,
    (value) => inputValidation.minLength(value, 2, 'Project name'),
    (value) => inputValidation.maxLength(value, 100, 'Project name')
  ],
  
  email: [
    inputValidation.required,
    inputValidation.email
  ],
  
  url: [
    inputValidation.url
  ]
};

// Export all validation utilities
export default {
  taskValidation,
  projectValidation,
  inputValidation,
  apiValidation,
  formValidation,
  useValidation,
  sanitization,
  validationRules
};
