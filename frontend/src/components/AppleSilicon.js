import React, { useState, useEffect } from 'react';

const AppleSiliconDashboard = () => {
  const [systemInfo, setSystemInfo] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [optimizationStatus, setOptimizationStatus] = useState(null);
  const [modelRecommendations, setModelRecommendations] = useState(null);
  const [downloadProgress, setDownloadProgress] = useState({});
  const [benchmarkResults, setBenchmarkResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [benchmarking, setBenchmarking] = useState(false);

  useEffect(() => {
    loadAppleSiliconData();
    const interval = setInterval(loadPerformanceData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadAppleSiliconData = async () => {
    try {
      const [systemRes, perfRes, modelRes] = await Promise.all([
        fetch('/api/apple-silicon/detect'),
        fetch('/api/apple-silicon/performance'),
        fetch('/api/apple-silicon/models/recommend')
      ]);

      const systemData = await systemRes.json();
      setSystemInfo(systemData);

      if (systemData.is_apple_silicon) {
        const perfData = await perfRes.json();
        const modelData = await modelRes.json();
        setPerformance(perfData);
        setModelRecommendations(modelData);
      }
    } catch (error) {
      console.error('Failed to load Apple Silicon data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPerformanceData = async () => {
    if (!systemInfo?.is_apple_silicon) return;

    try {
      const response = await fetch('/api/apple-silicon/performance');
      const data = await response.json();
      setPerformance(data);
    } catch (error) {
      console.error('Failed to load performance data:', error);
    }
  };

  const optimizeSystem = async () => {
    setOptimizing(true);
    try {
      const response = await fetch('/api/apple-silicon/optimize', {
        method: 'POST'
      });
      const result = await response.json();
      setOptimizationStatus(result);
      
      if (result.optimized) {
        alert('🍎 Apple Silicon optimizations applied successfully!');
        loadAppleSiliconData();
      } else {
        alert('❌ Optimization failed: ' + result.error);
      }
    } catch (error) {
      alert('❌ Optimization failed: ' + error.message);
    } finally {
      setOptimizing(false);
    }
  };

  const downloadRecommendedModels = async () => {
    try {
      const response = await fetch('/api/apple-silicon/models/download', {
        method: 'POST'
      });
      const result = await response.json();
      
      if (result.download_initiated) {
        alert('📥 Model downloads started in background!');
        // Start polling for download progress
        const progressInterval = setInterval(async () => {
          try {
            const progressRes = await fetch('/api/apple-silicon/models/download-progress');
            const progressData = await progressRes.json();
            setDownloadProgress(progressData.downloads);
            
            // Stop polling when all downloads complete
            if (progressData.active_downloads === 0) {
              clearInterval(progressInterval);
              if (progressData.completed_downloads > 0) {
                alert(`✅ ${progressData.completed_downloads} models downloaded successfully!`);
                loadAppleSiliconData();
              }
            }
          } catch (error) {
            clearInterval(progressInterval);
          }
        }, 2000);
      }
    } catch (error) {
      alert('❌ Model download failed: ' + error.message);
    }
  };

  const runBenchmark = async () => {
    setBenchmarking(true);
    try {
      const response = await fetch('/api/apple-silicon/benchmark', {
        method: 'POST'
      });
      const result = await response.json();
      
      if (result.benchmark_completed) {
        setBenchmarkResults(result.results);
        alert('🏆 Benchmark completed successfully!');
      } else {
        alert('❌ Benchmark failed');
      }
    } catch (error) {
      alert('❌ Benchmark failed: ' + error.message);
    } finally {
      setBenchmarking(false);
    }
  };

  const getPerformanceColor = (value, thresholds) => {
    if (value >= thresholds.excellent) return 'text-green-600';
    if (value >= thresholds.good) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPerformanceLabel = (value, thresholds) => {
    if (value >= thresholds.excellent) return 'Excellent';
    if (value >= thresholds.good) return 'Good';
    return 'Needs Attention';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading Apple Silicon status...</span>
      </div>
    );
  }

  if (!systemInfo?.is_apple_silicon) {
    return (
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <div className="text-center py-8">
          <div className="text-4xl mb-4">💻</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Apple Silicon Not Detected
          </h3>
          <p className="text-gray-600 mb-4">
            {systemInfo?.chip_type === 'intel'
              ? 'Intel Mac detected - Apple Silicon optimizations not available'
              : 'Non-Apple system detected'
            }
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-800 text-sm">
              💡 Your system will work great with VirtuAI Office! For optimal performance,
              ensure you have 8GB+ RAM and close unnecessary applications during AI processing.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Apple Silicon Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center">
              🍎 Apple Silicon Optimization
            </h2>
            <p className="text-purple-100 mt-1">
              {systemInfo.chip_type.toUpperCase()} with {systemInfo.specifications?.unified_memory_gb}GB unified memory
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={optimizeSystem}
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
              {benchmarking ? 'Running...' : '🏆 Run Benchmark'}
            </button>
          </div>
        </div>
      </div>

      {/* System Information */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-bold mb-4">🔧 System Specifications</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {systemInfo.specifications?.cpu_cores}
            </div>
            <div className="text-sm text-gray-600">CPU Cores</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {systemInfo.specifications?.gpu_cores}
            </div>
            <div className="text-sm text-gray-600">GPU Cores</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {systemInfo.specifications?.unified_memory_gb}GB
            </div>
            <div className="text-sm text-gray-600">Unified Memory</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {systemInfo.specifications?.max_concurrent_agents}
            </div>
            <div className="text-sm text-gray-600">Max Agents</div>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Neural Engine:</span>
            <span className="font-medium">
              {systemInfo.specifications?.neural_engine ? '✅ Yes' : '❌ No'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Memory Bandwidth:</span>
            <span className="font-medium">{systemInfo.specifications?.memory_bandwidth_gbps} GB/s</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Max Power:</span>
            <span className="font-medium">{systemInfo.specifications?.max_power_watts}W</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Chip Generation:</span>
            <span className="font-medium">{systemInfo.chip_type.toUpperCase()}</span>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      {performance && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="text-lg font-bold mb-4">📊 Real-Time Performance</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
            <div className="text-center">
              <div className={`text-2xl font-bold ${getPerformanceColor(100 - performance.performance.cpu_usage, {excellent: 70, good: 50})}`}>
                {Math.round(performance.performance.cpu_usage)}%
              </div>
              <div className="text-sm text-gray-600">CPU Usage</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${getPerformanceColor(100 - performance.performance.memory_usage, {excellent: 70, good: 50})}`}>
                {Math.round(performance.performance.memory_usage)}%
              </div>
              <div className="text-sm text-gray-600">Memory Usage</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${getPerformanceColor(performance.performance.inference_speed, {excellent: 15, good: 8})}`}>
                {Math.round(performance.performance.inference_speed)}
              </div>
              <div className="text-sm text-gray-600">Tokens/Second</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${getPerformanceColor(5 - performance.performance.model_load_time, {excellent: 3, good: 1})}`}>
                {performance.performance.model_load_time.toFixed(1)}s
              </div>
              <div className="text-sm text-gray-600">Model Load Time</div>
            </div>
          </div>

          {/* Status Indicators */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className={`p-4 rounded-lg ${
              performance.performance.memory_pressure === 'normal' ? 'bg-green-50 border-green-200' :
              performance.performance.memory_pressure === 'warning' ? 'bg-yellow-50 border-yellow-200' :
              'bg-red-50 border-red-200'
            } border`}>
              <div className="flex items-center">
                <span className="text-lg mr-2">💾</span>
                <div>
                  <div className="font-medium">Memory Pressure</div>
                  <div className="text-sm capitalize">{performance.performance.memory_pressure}</div>
                </div>
              </div>
            </div>
            
            <div className={`p-4 rounded-lg ${
              performance.performance.thermal_state === 'normal' ? 'bg-green-50 border-green-200' :
              performance.performance.thermal_state === 'elevated' ? 'bg-yellow-50 border-yellow-200' :
              'bg-red-50 border-red-200'
            } border`}>
              <div className="flex items-center">
                <span className="text-lg mr-2">🌡️</span>
                <div>
                  <div className="font-medium">Thermal State</div>
                  <div className="text-sm capitalize">{performance.performance.thermal_state}</div>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-blue-50 border-blue-200 border">
              <div className="flex items-center">
                <span className="text-lg mr-2">🔋</span>
                <div>
                  <div className="font-medium">Power Mode</div>
                  <div className="text-sm">{performance.performance.power_mode || 'Automatic'}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Model Recommendations */}
      {modelRecommendations && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold">🤖 AI Model Recommendations</h3>
            <button
              onClick={downloadRecommendedModels}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 font-medium"
            >
              📥 Download Recommended
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <h4 className="font-medium text-green-800 mb-2">✅ Recommended Models</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {modelRecommendations.recommended_models?.map(model => (
                  <div key={model.name} className="border border-green-200 rounded-lg p-3 bg-green-50">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium text-green-900">{model.name}</div>
                        <div className="text-sm text-green-700">
                          {model.complexity} complexity • {model.speed} speed
                        </div>
                      </div>
                      <div className="text-sm text-green-600">{model.size_gb}GB</div>
                    </div>
                    {downloadProgress[model.name] !== undefined && (
                      <div className="mt-2">
                        <div className="text-xs text-green-600 mb-1">
                          {downloadProgress[model.name] === 1 ? 'Downloaded' :
                           downloadProgress[model.name] === -1 ? 'Failed' :
                           `Downloading... ${Math.round(downloadProgress[model.name] * 100)}%`}
                        </div>
                        <div className="w-full bg-green-200 rounded-full h-1">
                          <div
                            className="bg-green-600 h-1 rounded-full transition-all"
                            style={{ width: `${Math.max(downloadProgress[model.name] * 100, 10)}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {modelRecommendations.optional_models?.length > 0 && (
              <div>
                <h4 className="font-medium text-blue-800 mb-2">💡 Optional Models</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {modelRecommendations.optional_models.map(model => (
                    <div key={model.name} className="border border-blue-200 rounded-lg p-3 bg-blue-50">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium text-blue-900">{model.name}</div>
                          <div className="text-sm text-blue-700">
                            {model.complexity} complexity • {model.speed} speed
                          </div>
                        </div>
                        <div className="text-sm text-blue-600">{model.size_gb}GB</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-800 mb-2">📋 Currently Installed</h4>
              <div className="flex flex-wrap gap-2">
                {modelRecommendations.currently_installed?.length > 0 ? (
                  modelRecommendations.currently_installed.map(model => (
                    <span key={model} className="px-2 py-1 bg-gray-200 text-gray-800 rounded text-sm">
                      {model}
                    </span>
                  ))
                ) : (
                  <span className="text-gray-600 text-sm">No models installed</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Benchmark Results */}
      {benchmarkResults && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="text-lg font-bold mb-4">🏆 Performance Benchmark Results</h3>
          
          <div className="mb-4">
            <div className="text-sm text-gray-600">
              Chip: {benchmarkResults.chip_type.toUpperCase()} •
              Memory: {benchmarkResults.memory_gb}GB •
              CPU: {benchmarkResults.cpu_cores} cores •
              GPU: {benchmarkResults.gpu_cores} cores
            </div>
          </div>

          <div className="space-y-4">
            {Object.entries(benchmarkResults.benchmarks).map(([model, results]) => (
              <div key={model} className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-3">{model}</h4>
                
                {results.error ? (
                  <div className="text-red-600 text-sm">Error: {results.error}</div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">Inference Speed</div>
                      <div className="font-medium">{results.tokens_per_second?.toFixed(1)} tokens/sec</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Load Time</div>
                      <div className="font-medium">{results.load_time?.toFixed(1)}s</div>
                    </div>
                    <div>
                      <div className="text-gray-600">CPU Usage</div>
                      <div className="font-medium">{results.cpu_usage?.toFixed(1)}%</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Memory Usage</div>
                      <div className="font-medium">{results.memory_usage?.toFixed(1)}%</div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Optimization Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-medium text-blue-800 mb-3">💡 Apple Silicon Optimization Tips</h3>
        <div className="space-y-2 text-sm text-blue-700">
          <div>• Keep your Mac plugged in during heavy AI processing for maximum performance</div>
          <div>• Close unnecessary applications to free up memory for AI models</div>
          <div>• Use the latest macOS version for optimal Apple Silicon performance</div>
          <div>• Monitor memory pressure - switch to smaller models if it gets critical</div>
          <div>• The unified memory architecture allows larger models than traditional systems</div>
          <div>• Neural Engine acceleration provides additional performance boost</div>
        </div>
      </div>
    </div>
  );
};

export default AppleSiliconDashboard;
