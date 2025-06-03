import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

const AppleSiliconDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [optimizing, setOptimizing] = useState(false);
  const [benchmarking, setBenchmarking] = useState(false);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/apple-silicon/dashboard`);
      if (!response.ok) {
        throw new Error('Failed to load dashboard data');
      }
      const data = await response.json();
      setDashboardData(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const runOptimization = async () => {
    setOptimizing(true);
    try {
      const response = await fetch(`${API_BASE}/api/apple-silicon/optimize`, {
        method: 'POST'
      });
      const result = await response.json();
      
      if (result.optimized) {
        alert('Apple Silicon optimizations applied successfully!');
        loadDashboardData();
      } else {
        alert(`Optimization failed: ${result.error}`);
      }
    } catch (err) {
      alert(`Optimization failed: ${err.message}`);
    } finally {
      setOptimizing(false);
    }
  };

  const runBenchmark = async () => {
    setBenchmarking(true);
    try {
      const response = await fetch(`${API_BASE}/api/apple-silicon/benchmark`, {
        method: 'POST'
      });
      const result = await response.json();
      
      if (result.benchmark_completed) {
        alert('Benchmark completed! Check the performance history section.');
        loadDashboardData();
      } else {
        alert('Benchmark failed');
      }
    } catch (err) {
      alert(`Benchmark failed: ${err.message}`);
    } finally {
      setBenchmarking(false);
    }
  };

  const getChipEmoji = (chipType) => {
    if (chipType.includes('m3')) return '🔥';
    if (chipType.includes('m2')) return '⚡';
    if (chipType.includes('m1')) return '🍎';
    return '💻';
  };

  const getPerformanceColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getOptimizationBadge = (level) => {
    const badges = {
      'optimized': { text: 'Optimized', color: 'bg-green-100 text-green-800' },
      'default': { text: 'Default', color: 'bg-yellow-100 text-yellow-800' }
    };
    return badges[level] || badges.default;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3">Loading Apple Silicon dashboard...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <div className="text-red-500 text-xl mr-3">⚠️</div>
          <div>
            <h3 className="font-medium text-red-800">Dashboard Error</h3>
            <p className="text-red-600 text-sm mt-1">{error}</p>
          </div>
        </div>
        <button
          onClick={loadDashboardData}
          className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!dashboardData?.system_info?.is_apple_silicon) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-center">
          <div className="text-blue-500 text-2xl mr-4">💻</div>
          <div>
            <h3 className="font-medium text-blue-800">Apple Silicon Not Detected</h3>
            <p className="text-blue-600 text-sm mt-1">
              This dashboard is optimized for Apple Silicon Macs (M1, M2, M3).
              Your system will work great with VirtuAI Office using standard optimizations.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const { system_info, current_performance, optimization, performance_history, model_performance } = dashboardData;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center mb-2">
              <span className="text-3xl mr-3">{getChipEmoji(system_info.chip_type)}</span>
              <h2 className="text-2xl font-bold">
                Apple Silicon Dashboard
              </h2>
            </div>
            <p className="text-purple-100">
              {system_info.chip_type.toUpperCase()} with {system_info.memory_gb}GB unified memory
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={runOptimization}
              disabled={optimizing}
              className="bg-white text-purple-600 px-4 py-2 rounded-md hover:bg-gray-100 font-medium disabled:opacity-50"
            >
              {optimizing ? 'Optimizing...' : '⚡ Optimize System'}
            </button>
            <button
              onClick={runBenchmark}
              disabled={benchmarking}
              className="bg-yellow-500 text-white px-4 py-2 rounded-md hover:bg-yellow-600 font-medium disabled:opacity-50"
            >
              {benchmarking ? 'Benchmarking...' : '🏁 Run Benchmark'}
            </button>
          </div>
        </div>
      </div>

      {/* System Information */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-bold mb-4">🖥️ System Information</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{system_info.cpu_cores}</div>
            <div className="text-sm text-gray-600">CPU Cores</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{system_info.gpu_cores}</div>
            <div className="text-sm text-gray-600">GPU Cores</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">{system_info.memory_gb}GB</div>
            <div className="text-sm text-gray-600">Unified Memory</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl">{system_info.neural_engine ? '✅' : '❌'}</div>
            <div className="text-sm text-gray-600">Neural Engine</div>
          </div>
        </div>
      </div>

      {/* Current Performance */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-bold mb-4">📊 Current Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Performance Metrics */}
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-600">CPU Usage</span>
                <span className="text-sm font-medium">{current_performance.cpu_usage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full ${
                    current_performance.cpu_usage > 80 ? 'bg-red-500' :
                    current_performance.cpu_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(current_performance.cpu_usage, 100)}%` }}
                ></div>
              </div>
            </div>
            
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-600">Memory Usage</span>
                <span className="text-sm font-medium">{current_performance.memory_usage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full ${
                    current_performance.memory_usage > 80 ? 'bg-red-500' :
                    current_performance.memory_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(current_performance.memory_usage, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Status Indicators */}
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Memory Pressure</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                current_performance.memory_pressure === 'normal' ? 'bg-green-100 text-green-800' :
                current_performance.memory_pressure === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {current_performance.memory_pressure}
              </span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Thermal State</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                current_performance.thermal_state === 'normal' ? 'bg-green-100 text-green-800' :
                current_performance.thermal_state === 'elevated' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {current_performance.thermal_state}
              </span>
            </div>
            
            {current_performance.battery_level && (
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Battery</span>
                <span className="text-sm font-medium">{current_performance.battery_level.toFixed(0)}%</span>
              </div>
            )}
          </div>

          {/* AI Performance */}
          <div className="space-y-3">
            <div className="p-3 bg-blue-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Inference Speed</div>
              <div className="text-lg font-bold text-blue-600">
                {current_performance.inference_speed.toFixed(1)} tokens/sec
              </div>
            </div>
            
            <div className="p-3 bg-purple-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Model Load Time</div>
              <div className="text-lg font-bold text-purple-600">
                {current_performance.model_load_time.toFixed(2)}s
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Optimization Status */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-bold mb-4">⚙️ Optimization Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className={`text-4xl font-bold mb-2 ${getPerformanceColor(optimization.score)}`}>
              {optimization.score.toFixed(0)}
            </div>
            <div className="text-sm text-gray-600">Optimization Score</div>
          </div>
          
          <div className="text-center">
            <div className="mb-2">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getOptimizationBadge(optimization.level).color}`}>
                {getOptimizationBadge(optimization.level).text}
              </span>
            </div>
            <div className="text-sm text-gray-600">Current Level</div>
          </div>
          
          <div className="text-center">
            <div className="text-sm text-gray-600 mb-2">Last Optimized</div>
            <div className="text-sm font-medium">
              {optimization.last_optimized
                ? new Date(optimization.last_optimized).toLocaleDateString()
                : 'Never'
              }
            </div>
          </div>
        </div>

        {/* Recommendations */}
        {optimization.recommendations && optimization.recommendations.length > 0 && (
          <div className="mt-6">
            <h4 className="font-medium text-gray-900 mb-3">💡 Recommendations</h4>
            <div className="space-y-2">
              {optimization.recommendations.map((rec, index) => (
                <div key={index} className="flex items-start p-3 bg-blue-50 rounded-lg">
                  <div className="text-blue-600 mr-2">•</div>
                  <div className="text-blue-800 text-sm">{rec}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Model Performance */}
      {model_performance && Object.keys(model_performance).length > 0 && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="text-lg font-bold mb-4">🤖 Model Performance</h3>
          <div className="space-y-4">
            {Object.entries(model_performance).map(([model, stats]) => (
              <div key={model} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium text-gray-900">{model}</div>
                  <div className="text-sm text-gray-600">{stats.usage_count} uses</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-blue-600">
                    {stats.avg_inference_speed.toFixed(1)} tokens/sec
                  </div>
                  <div className="text-xs text-gray-500">
                    {stats.avg_load_time.toFixed(2)}s load time
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Performance History Chart Placeholder */}
      {performance_history && performance_history.length > 0 && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="text-lg font-bold mb-4">📈 Performance History</h3>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
            <div className="text-center text-gray-500">
              <div className="text-2xl mb-2">📊</div>
              <div>Performance chart would be rendered here</div>
              <div className="text-sm">({performance_history.length} data points available)</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AppleSiliconDashboard;
