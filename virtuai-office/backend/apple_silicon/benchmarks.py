# VirtuAI Office - Apple Silicon Benchmarking System
# Comprehensive performance benchmarking for M1/M2/M3 Macs

import asyncio
import json
import time
import psutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
import statistics
from concurrent.futures import ThreadPoolExecutor
import ollama

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Single benchmark test result"""
    test_name: str
    duration: float
    tokens_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float
    thermal_state: str
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class SystemSnapshot:
    """System state at time of benchmark"""
    timestamp: datetime
    cpu_usage: float
    memory_usage_mb: float
    memory_pressure: str
    thermal_state: str
    battery_level: Optional[float]
    power_mode: str
    available_memory_mb: float

@dataclass
class ModelBenchmark:
    """Complete benchmark results for a model"""
    model_name: str
    system_snapshot: SystemSnapshot
    inference_tests: List[BenchmarkResult]
    load_time: float
    memory_footprint_mb: float
    avg_tokens_per_second: float
    stability_score: float
    efficiency_score: float
    total_duration: float

class AppleSiliconBenchmark:
    """Comprehensive benchmarking system for Apple Silicon Macs"""
    
    def __init__(self, chip_type: str, memory_gb: int):
        self.chip_type = chip_type
        self.memory_gb = memory_gb
        self.test_prompts = self._get_test_prompts()
        self.benchmark_history = []
        
    def _get_test_prompts(self) -> List[Dict[str, str]]:
        """Get standardized test prompts for consistent benchmarking"""
        return [
            {
                "name": "code_generation",
                "prompt": "Write a Python function to calculate the nth Fibonacci number using dynamic programming. Include error handling and documentation.",
                "expected_tokens": 100,
                "complexity": "medium"
            },
            {
                "name": "explanation",
                "prompt": "Explain the concept of machine learning in simple terms that a beginner could understand. Include examples.",
                "expected_tokens": 150,
                "complexity": "low"
            },
            {
                "name": "react_component",
                "prompt": "Create a React component for a user profile card with avatar, name, email, and edit button. Include TypeScript types and CSS styling.",
                "expected_tokens": 200,
                "complexity": "high"
            },
            {
                "name": "api_design",
                "prompt": "Design a REST API for a blog system with posts, comments, and users. Include endpoints, request/response schemas, and authentication.",
                "expected_tokens": 250,
                "complexity": "high"
            },
            {
                "name": "simple_query",
                "prompt": "What is the capital of France?",
                "expected_tokens": 5,
                "complexity": "trivial"
            },
            {
                "name": "complex_analysis",
                "prompt": "Analyze the pros and cons of microservices architecture vs monolithic architecture for a startup with 10 developers building an e-commerce platform. Consider scalability, development speed, deployment complexity, and team coordination.",
                "expected_tokens": 400,
                "complexity": "very_high"
            }
        ]
    
    async def benchmark_model(self, model_name: str, warmup_runs: int = 2, test_runs: int = 5) -> ModelBenchmark:
        """Comprehensive benchmark of a specific model"""
        logger.info(f"Starting benchmark for model: {model_name}")
        
        # Take system snapshot
        system_snapshot = await self._take_system_snapshot()
        
        # Measure model load time
        load_time = await self._measure_model_load_time(model_name)
        
        # Warmup runs
        logger.info(f"Running {warmup_runs} warmup iterations...")
        for _ in range(warmup_runs):
            await self._run_single_inference(model_name, self.test_prompts[0])
        
        # Actual benchmark runs
        logger.info(f"Running {test_runs} benchmark iterations...")
        all_results = []
        
        for run in range(test_runs):
            logger.info(f"Benchmark run {run + 1}/{test_runs}")
            run_results = []
            
            for prompt_data in self.test_prompts:
                result = await self._run_benchmark_test(model_name, prompt_data)
                run_results.append(result)
                all_results.append(result)
                
                # Brief pause between tests
                await asyncio.sleep(1)
            
            # Longer pause between runs
            if run < test_runs - 1:
                await asyncio.sleep(5)
        
        # Calculate aggregate metrics
        memory_footprint = await self._measure_memory_footprint(model_name)
        avg_tokens_per_second = statistics.mean([r.tokens_per_second for r in all_results if r.success])
        stability_score = self._calculate_stability_score(all_results)
        efficiency_score = self._calculate_efficiency_score(all_results)
        total_duration = sum([r.duration for r in all_results])
        
        benchmark = ModelBenchmark(
            model_name=model_name,
            system_snapshot=system_snapshot,
            inference_tests=all_results,
            load_time=load_time,
            memory_footprint_mb=memory_footprint,
            avg_tokens_per_second=avg_tokens_per_second,
            stability_score=stability_score,
            efficiency_score=efficiency_score,
            total_duration=total_duration
        )
        
        self.benchmark_history.append(benchmark)
        logger.info(f"Benchmark completed for {model_name}: {avg_tokens_per_second:.2f} tokens/sec")
        
        return benchmark
    
    async def _run_benchmark_test(self, model_name: str, prompt_data: Dict[str, str]) -> BenchmarkResult:
        """Run a single benchmark test"""
        test_name = prompt_data["name"]
        prompt = prompt_data["prompt"]
        
        # Take system metrics before test
        cpu_before = psutil.cpu_percent()
        memory_before = psutil.virtual_memory()
        thermal_before = await self._get_thermal_state()
        
        start_time = time.time()
        success = True
        error_message = None
        tokens_generated = 0
        
        try:
            # Run inference
            response = await asyncio.to_thread(
                ollama.generate,
                model=model_name,
                prompt=prompt,
                stream=False
            )
            
            tokens_generated = len(response.get('response', '').split())
            
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Benchmark test {test_name} failed: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Take system metrics after test
        cpu_after = psutil.cpu_percent()
        memory_after = psutil.virtual_memory()
        thermal_after = await self._get_thermal_state()
        
        # Calculate metrics
        tokens_per_second = tokens_generated / duration if duration > 0 and success else 0
        memory_usage_mb = (memory_after.used - memory_before.used) / (1024 * 1024)
        cpu_usage = max(cpu_after - cpu_before, 0)
        
        return BenchmarkResult(
            test_name=test_name,
            duration=duration,
            tokens_per_second=tokens_per_second,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage,
            thermal_state=thermal_after,
            success=success,
            error_message=error_message,
            metadata={
                "prompt_complexity": prompt_data["complexity"],
                "expected_tokens": prompt_data["expected_tokens"],
                "actual_tokens": tokens_generated,
                "model_name": model_name
            }
        )
    
    async def _run_single_inference(self, model_name: str, prompt_data: Dict[str, str]) -> None:
        """Run a single inference for warmup"""
        try:
            await asyncio.to_thread(
                ollama.generate,
                model=model_name,
                prompt=prompt_data["prompt"],
                stream=False
            )
        except Exception as e:
            logger.warning(f"Warmup inference failed: {e}")
    
    async def _measure_model_load_time(self, model_name: str) -> float:
        """Measure time to load/verify model"""
        start_time = time.time()
        
        try:
            # This triggers model loading if not already loaded
            await asyncio.to_thread(ollama.list)
            
            # Small test to ensure model is ready
            await asyncio.to_thread(
                ollama.generate,
                model=model_name,
                prompt="test",
                stream=False
            )
            
        except Exception as e:
            logger.warning(f"Model load time measurement failed: {e}")
        
        return time.time() - start_time
    
    async def _measure_memory_footprint(self, model_name: str) -> float:
        """Measure memory footprint of loaded model"""
        try:
            # This is an approximation - actual measurement would require deeper integration
            memory_info = psutil.virtual_memory()
            
            # Rough estimation based on model size
            model_size_estimates = {
                "llama2:7b": 3800,      # ~3.8GB
                "llama2:13b": 7300,     # ~7.3GB
                "llama2:70b": 39000,    # ~39GB
                "codellama:7b": 3800,   # ~3.8GB
                "codellama:13b": 7300,  # ~7.3GB
                "codellama:34b": 19000, # ~19GB
            }
            
            return model_size_estimates.get(model_name, 4000)  # Default 4GB
            
        except Exception as e:
            logger.warning(f"Memory footprint measurement failed: {e}")
            return 0.0
    
    async def _take_system_snapshot(self) -> SystemSnapshot:
        """Take comprehensive system state snapshot"""
        memory = psutil.virtual_memory()
        
        return SystemSnapshot(
            timestamp=datetime.utcnow(),
            cpu_usage=psutil.cpu_percent(interval=1),
            memory_usage_mb=memory.used / (1024 * 1024),
            memory_pressure=await self._get_memory_pressure(),
            thermal_state=await self._get_thermal_state(),
            battery_level=await self._get_battery_level(),
            power_mode=await self._get_power_mode(),
            available_memory_mb=memory.available / (1024 * 1024)
        )
    
    async def _get_memory_pressure(self) -> str:
        """Get macOS memory pressure state"""
        try:
            result = subprocess.run(
                ["memory_pressure"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout.lower()
            if "critical" in output:
                return "critical"
            elif "warn" in output:
                return "warning"
            else:
                return "normal"
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return "unknown"
    
    async def _get_thermal_state(self) -> str:
        """Get thermal state information"""
        try:
            result = subprocess.run(
                ["pmset", "-g", "therm"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout.lower()
            if "cpu_speed_limit" in output:
                return "throttling"
            elif "thermal_state" in output and "0" not in output:
                return "elevated"
            else:
                return "normal"
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return "unknown"
    
    async def _get_power_mode(self) -> str:
        """Get current power mode"""
        try:
            result = subprocess.run(
                ["pmset", "-g", "custom"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout.lower()
            if "automaticrestartonimp" in output:
                return "automatic"
            elif "powernap" in output and "1" in output:
                return "power_nap"
            else:
                return "standard"
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return "standard"
    
    async def _get_battery_level(self) -> Optional[float]:
        """Get battery level if on laptop"""
        try:
            battery = psutil.sensors_battery()
            return battery.percent if battery else None
        except:
            return None
    
    def _calculate_stability_score(self, results: List[BenchmarkResult]) -> float:
        """Calculate stability score based on result consistency"""
        if not results:
            return 0.0
        
        successful_results = [r for r in results if r.success]
        if len(successful_results) < 2:
            return 0.5 if successful_results else 0.0
        
        # Calculate coefficient of variation for tokens per second
        tokens_per_sec = [r.tokens_per_second for r in successful_results]
        mean_tps = statistics.mean(tokens_per_sec)
        std_tps = statistics.stdev(tokens_per_sec) if len(tokens_per_sec) > 1 else 0
        
        if mean_tps == 0:
            return 0.0
        
        cv = std_tps / mean_tps  # Coefficient of variation
        stability = max(0.0, 1.0 - cv)  # Lower CV = higher stability
        
        # Factor in success rate
        success_rate = len(successful_results) / len(results)
        
        return stability * success_rate
    
    def _calculate_efficiency_score(self, results: List[BenchmarkResult]) -> float:
        """Calculate efficiency score based on performance vs resource usage"""
        if not results:
            return 0.0
        
        successful_results = [r for r in results if r.success]
        if not successful_results:
            return 0.0
        
        # Calculate average efficiency metrics
        avg_tps = statistics.mean([r.tokens_per_second for r in successful_results])
        avg_memory = statistics.mean([r.memory_usage_mb for r in successful_results])
        avg_cpu = statistics.mean([r.cpu_usage_percent for r in successful_results])
        
        # Normalize scores (higher is better for TPS, lower is better for resource usage)
        tps_score = min(avg_tps / 50.0, 1.0)  # Normalize to max 50 TPS
        memory_score = max(0.0, 1.0 - (avg_memory / 1000.0))  # Penalize high memory usage
        cpu_score = max(0.0, 1.0 - (avg_cpu / 100.0))  # Penalize high CPU usage
        
        # Weighted average (performance is most important)
        efficiency = (tps_score * 0.6) + (memory_score * 0.2) + (cpu_score * 0.2)
        
        return min(1.0, max(0.0, efficiency))
    
    async def run_comprehensive_benchmark(self, models: List[str], test_runs: int = 3) -> Dict[str, ModelBenchmark]:
        """Run comprehensive benchmark across multiple models"""
        logger.info(f"Starting comprehensive benchmark for {len(models)} models")
        
        results = {}
        
        for i, model in enumerate(models):
            logger.info(f"Benchmarking model {i + 1}/{len(models)}: {model}")
            
            try:
                # Ensure model is available
                available_models = ollama.list()
                model_names = [m['name'] for m in available_models.get('models', [])]
                
                if model not in model_names:
                    logger.warning(f"Model {model} not found, skipping")
                    continue
                
                # Run benchmark
                benchmark = await self.benchmark_model(model, test_runs=test_runs)
                results[model] = benchmark
                
                # Cool-down period between models
                if i < len(models) - 1:
                    logger.info("Cooling down between models...")
                    await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Failed to benchmark model {model}: {e}")
                continue
        
        return results
    
    def generate_benchmark_report(self, benchmarks: Dict[str, ModelBenchmark]) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        if not benchmarks:
            return {"error": "No benchmark data available"}
        
        report = {
            "metadata": {
                "chip_type": self.chip_type,
                "memory_gb": self.memory_gb,
                "benchmark_date": datetime.utcnow().isoformat(),
                "models_tested": len(benchmarks)
            },
            "summary": {},
            "detailed_results": {},
            "recommendations": []
        }
        
        # Calculate summary statistics
        all_avg_tps = []
        all_stability = []
        all_efficiency = []
        
        for model_name, benchmark in benchmarks.items():
            all_avg_tps.append(benchmark.avg_tokens_per_second)
            all_stability.append(benchmark.stability_score)
            all_efficiency.append(benchmark.efficiency_score)
            
            # Detailed results
            report["detailed_results"][model_name] = {
                "avg_tokens_per_second": round(benchmark.avg_tokens_per_second, 2),
                "stability_score": round(benchmark.stability_score, 3),
                "efficiency_score": round(benchmark.efficiency_score, 3),
                "load_time": round(benchmark.load_time, 2),
                "memory_footprint_mb": benchmark.memory_footprint_mb,
                "total_duration": round(benchmark.total_duration, 2),
                "successful_tests": len([r for r in benchmark.inference_tests if r.success]),
                "total_tests": len(benchmark.inference_tests),
                "test_breakdown": self._analyze_test_breakdown(benchmark.inference_tests)
            }
        
        # Summary statistics
        report["summary"] = {
            "avg_tokens_per_second": {
                "mean": round(statistics.mean(all_avg_tps), 2),
                "max": round(max(all_avg_tps), 2),
                "min": round(min(all_avg_tps), 2),
                "best_model": max(benchmarks.keys(), key=lambda k: benchmarks[k].avg_tokens_per_second)
            },
            "stability": {
                "mean": round(statistics.mean(all_stability), 3),
                "best_model": max(benchmarks.keys(), key=lambda k: benchmarks[k].stability_score)
            },
            "efficiency": {
                "mean": round(statistics.mean(all_efficiency), 3),
                "best_model": max(benchmarks.keys(), key=lambda k: benchmarks[k].efficiency_score)
            }
        }
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(benchmarks)
        
        return report
    
    def _analyze_test_breakdown(self, test_results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Analyze breakdown of test results by complexity"""
        breakdown = {}
        
        for result in test_results:
            complexity = result.metadata.get("prompt_complexity", "unknown")
            
            if complexity not in breakdown:
                breakdown[complexity] = {
                    "count": 0,
                    "successes": 0,
                    "avg_tps": 0,
                    "avg_duration": 0
                }
            
            breakdown[complexity]["count"] += 1
            if result.success:
                breakdown[complexity]["successes"] += 1
                breakdown[complexity]["avg_tps"] += result.tokens_per_second
                breakdown[complexity]["avg_duration"] += result.duration
        
        # Calculate averages
        for complexity_data in breakdown.values():
            if complexity_data["successes"] > 0:
                complexity_data["avg_tps"] /= complexity_data["successes"]
                complexity_data["avg_duration"] /= complexity_data["successes"]
                complexity_data["avg_tps"] = round(complexity_data["avg_tps"], 2)
                complexity_data["avg_duration"] = round(complexity_data["avg_duration"], 2)
        
        return breakdown
    
    def _generate_recommendations(self, benchmarks: Dict[str, ModelBenchmark]) -> List[str]:
        """Generate recommendations based on benchmark results"""
        recommendations = []
        
        if not benchmarks:
            return ["No benchmark data available for recommendations"]
        
        # Find best performing models
        best_speed = max(benchmarks.keys(), key=lambda k: benchmarks[k].avg_tokens_per_second)
        best_stable = max(benchmarks.keys(), key=lambda k: benchmarks[k].stability_score)
        best_efficient = max(benchmarks.keys(), key=lambda k: benchmarks[k].efficiency_score)
        
        recommendations.append(f"🚀 Fastest model: {best_speed} ({benchmarks[best_speed].avg_tokens_per_second:.1f} tokens/sec)")
        recommendations.append(f"📊 Most stable: {best_stable} (stability: {benchmarks[best_stable].stability_score:.2f})")
        recommendations.append(f"⚡ Most efficient: {best_efficient} (efficiency: {benchmarks[best_efficient].efficiency_score:.2f})")
        
        # Memory recommendations
        if self.memory_gb >= 32:
            large_models = [k for k in benchmarks.keys() if "13b" in k or "70b" in k]
            if large_models:
                recommendations.append(f"💾 With {self.memory_gb}GB RAM, consider using larger models: {', '.join(large_models)}")
        elif self.memory_gb < 16:
            recommendations.append("💾 Consider using quantized models (q4_0) for better memory efficiency")
        
        # Performance recommendations
        avg_tps = statistics.mean([b.avg_tokens_per_second for b in benchmarks.values()])
        if avg_tps < 10:
            recommendations.append("⚠️ Low performance detected - check system resources and thermal state")
        elif avg_tps > 30:
            recommendations.append("🎉 Excellent performance! Your system is well-optimized for AI workloads")
        
        # Stability recommendations
        avg_stability = statistics.mean([b.stability_score for b in benchmarks.values()])
        if avg_stability < 0.8:
            recommendations.append("📈 Consider reducing concurrent tasks to improve stability")
        
        return recommendations
    
    def export_results(self, benchmarks: Dict[str, ModelBenchmark], format: str = "json") -> str:
        """Export benchmark results in specified format"""
        
        if format.lower() == "json":
            # Convert to serializable format
            export_data = {}
            for model_name, benchmark in benchmarks.items():
                export_data[model_name] = {
                    "model_name": benchmark.model_name,
                    "system_snapshot": asdict(benchmark.system_snapshot),
                    "inference_tests": [asdict(test) for test in benchmark.inference_tests],
                    "load_time": benchmark.load_time,
                    "memory_footprint_mb": benchmark.memory_footprint_mb,
                    "avg_tokens_per_second": benchmark.avg_tokens_per_second,
                    "stability_score": benchmark.stability_score,
                    "efficiency_score": benchmark.efficiency_score,
                    "total_duration": benchmark.total_duration
                }
            
            # Convert datetime objects to ISO strings
            def serialize_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            return json.dumps(export_data, indent=2, default=serialize_datetime)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")


class BenchmarkScheduler:
    """Scheduler for running regular benchmarks"""
    
    def __init__(self, benchmark_system: AppleSiliconBenchmark):
        self.benchmark_system = benchmark_system
        self.scheduled_benchmarks = []
        self.running = False
    
    async def schedule_daily_benchmark(self, models: List[str], hour: int = 2):
        """Schedule daily benchmark runs"""
        # Implementation would depend on your scheduling needs
        pass
    
    async def run_quick_benchmark(self, model: str) -> ModelBenchmark:
        """Run a quick benchmark with fewer iterations"""
        return await self.benchmark_system.benchmark_model(model, warmup_runs=1, test_runs=2)
    
    async def run_stress_test(self, model: str, duration_minutes: int = 30) -> Dict[str, Any]:
        """Run extended stress test"""
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        results = []
        test_count = 0
        
        while time.time() < end_time:
            test_count += 1
            logger.info(f"Stress test iteration {test_count}")
            
            # Run single benchmark
            result = await self.benchmark_system._run_benchmark_test(
                model,
                self.benchmark_system.test_prompts[test_count % len(self.benchmark_system.test_prompts)]
            )
            results.append(result)
            
            # Brief pause
            await asyncio.sleep(5)
        
        # Analyze stress test results
        successful_results = [r for r in results if r.success]
        
        return {
            "model": model,
            "duration_minutes": duration_minutes,
            "total_tests": len(results),
            "successful_tests": len(successful_results),
            "success_rate": len(successful_results) / len(results) if results else 0,
            "avg_tokens_per_second": statistics.mean([r.tokens_per_second for r in successful_results]) if successful_results else 0,
            "performance_degradation": self._analyze_performance_degradation(successful_results),
            "thermal_behavior": self._analyze_thermal_behavior(results)
        }
    
    def _analyze_performance_degradation(self, results: List[BenchmarkResult]) -> Dict[str, float]:
        """Analyze if performance degrades over time"""
        if len(results) < 10:
            return {"insufficient_data": True}
        
        # Split into first and last half
        mid_point = len(results) // 2
        first_half = results[:mid_point]
        second_half = results[mid_point:]
        
        first_avg = statistics.mean([r.tokens_per_second for r in first_half])
        second_avg = statistics.mean([r.tokens_per_second for r in second_half])
        
        degradation_percent = ((first_avg - second_avg) / first_avg) * 100 if first_avg > 0 else 0
        
        return {
            "first_half_avg_tps": round(first_avg, 2),
            "second_half_avg_tps": round(second_avg, 2),
            "degradation_percent": round(degradation_percent, 2),
            "significant_degradation": degradation_percent > 10
        }
    
    def _analyze_thermal_behavior(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Analyze thermal behavior during stress test"""
        thermal_states = [r.thermal_state for r in results]
        
        return {
            "thermal_states": list(set(thermal_states)),
            "throttling_events": thermal_states.count("throttling"),
            "elevated_temp_events": thermal_states.count("elevated"),
            "normal_temp_events": thermal_states.count("normal"),
            "thermal_issues": "throttling" in thermal_states or thermal_states.count("elevated") > len(results) * 0.3
        }
