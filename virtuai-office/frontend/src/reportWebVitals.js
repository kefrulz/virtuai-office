// VirtuAI Office - Web Vitals Performance Monitoring
// Report web vitals to analytics or monitoring services

const reportWebVitals = (onPerfEntry) => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(onPerfEntry);
      getFID(onPerfEntry);
      getFCP(onPerfEntry);
      getLCP(onPerfEntry);
      getTTFB(onPerfEntry);
    });
  }
};

// Enhanced performance monitoring for VirtuAI Office
export const initPerformanceMonitoring = () => {
  // Monitor Core Web Vitals
  reportWebVitals((metric) => {
    // Log performance metrics in development
    if (process.env.NODE_ENV === 'development') {
      console.group(`📊 Performance Metric: ${metric.name}`);
      console.log(`Value: ${metric.value}`);
      console.log(`Rating: ${metric.rating}`);
      console.log(`Delta: ${metric.delta}`);
      console.groupEnd();
    }

    // Send to analytics in production
    if (process.env.NODE_ENV === 'production') {
      // You can integrate with analytics services here
      // Example: gtag('event', metric.name, { value: metric.value });
      
      // Store locally for dashboard display
      const perfData = JSON.parse(localStorage.getItem('virtuai-performance') || '[]');
      perfData.push({
        ...metric,
        timestamp: Date.now(),
        url: window.location.pathname
      });
      
      // Keep only last 100 entries
      if (perfData.length > 100) {
        perfData.splice(0, perfData.length - 100);
      }
      
      localStorage.setItem('virtuai-performance', JSON.stringify(perfData));
    }

    // Performance warnings for poor metrics
    if (metric.rating === 'poor') {
      console.warn(`⚠️ Poor performance detected for ${metric.name}: ${metric.value}`);
      
      // Show user-friendly performance tips
      if (metric.name === 'LCP' && metric.value > 4000) {
        console.info('💡 Try closing unnecessary browser tabs or applications for better performance');
      }
      
      if (metric.name === 'FID' && metric.value > 300) {
        console.info('💡 Consider reducing the number of active tasks for better responsiveness');
      }
    }
  });

  // Monitor memory usage (Chrome only)
  if ('memory' in performance) {
    const logMemoryUsage = () => {
      const memory = performance.memory;
      const memoryInfo = {
        usedJSHeapSize: Math.round(memory.usedJSHeapSize / 1048576), // MB
        totalJSHeapSize: Math.round(memory.totalJSHeapSize / 1048576), // MB
        jsHeapSizeLimit: Math.round(memory.jsHeapSizeLimit / 1048576) // MB
      };

      // Warn if memory usage is high
      if (memoryInfo.usedJSHeapSize > 50) {
        console.warn('⚠️ High memory usage detected:', memoryInfo);
      }

      if (process.env.NODE_ENV === 'development') {
        console.log('🧠 Memory Usage:', memoryInfo);
      }
    };

    // Log memory usage every 30 seconds in development
    if (process.env.NODE_ENV === 'development') {
      setInterval(logMemoryUsage, 30000);
    }
  }

  // Monitor long tasks (tasks > 50ms)
  if ('PerformanceObserver' in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.duration > 50) {
            console.warn(`⏱️ Long task detected: ${entry.duration}ms`);
            
            if (entry.duration > 100) {
              console.info('💡 Consider breaking up large operations or using web workers');
            }
          }
        });
      });

      observer.observe({ entryTypes: ['longtask'] });
    } catch (e) {
      // Long task observer not supported
    }
  }

  // Monitor resource loading
  if ('PerformanceObserver' in window) {
    try {
      const resourceObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          // Warn about slow resource loading
          if (entry.duration > 1000) {
            console.warn(`🐌 Slow resource: ${entry.name} took ${entry.duration}ms`);
          }
          
          // Track AI model loading specifically
          if (entry.name.includes('ollama') || entry.name.includes('api/')) {
            if (process.env.NODE_ENV === 'development') {
              console.log(`🤖 AI API call: ${entry.name} - ${entry.duration}ms`);
            }
          }
        });
      });

      resourceObserver.observe({ entryTypes: ['resource'] });
    } catch (e) {
      // Resource observer not supported
    }
  }
};

// Get performance summary for dashboard
export const getPerformanceSummary = () => {
  const perfData = JSON.parse(localStorage.getItem('virtuai-performance') || '[]');
  
  if (perfData.length === 0) {
    return null;
  }

  // Calculate averages for each metric
  const metrics = {};
  perfData.forEach(entry => {
    if (!metrics[entry.name]) {
      metrics[entry.name] = {
        values: [],
        ratings: { good: 0, 'needs-improvement': 0, poor: 0 }
      };
    }
    metrics[entry.name].values.push(entry.value);
    metrics[entry.name].ratings[entry.rating]++;
  });

  // Calculate averages and performance scores
  const summary = {};
  Object.keys(metrics).forEach(metricName => {
    const values = metrics[metricName].values;
    const ratings = metrics[metricName].ratings;
    const total = ratings.good + ratings['needs-improvement'] + ratings.poor;
    
    summary[metricName] = {
      average: values.reduce((a, b) => a + b, 0) / values.length,
      latest: values[values.length - 1],
      goodPercentage: (ratings.good / total) * 100,
      needsImprovementPercentage: (ratings['needs-improvement'] / total) * 100,
      poorPercentage: (ratings.poor / total) * 100
    };
  });

  return summary;
};

// Clear performance data
export const clearPerformanceData = () => {
  localStorage.removeItem('virtuai-performance');
};

export default reportWebVitals;
