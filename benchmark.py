#!/usr/bin/env python3
"""
MCP Web Search Server 性能基准测试
"""

import asyncio
import time
import statistics
import psutil
import json
import sys
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from server import WebSearcher, handle_call_tool

class BenchmarkResults:
    """基准测试结果类"""
    
    def __init__(self):
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        self.memory_usage = []
        self.cpu_usage = []
        self.start_time = None
        self.end_time = None
    
    def add_response_time(self, time_ms: float):
        self.response_times.append(time_ms)
    
    def add_success(self):
        self.success_count += 1
    
    def add_error(self):
        self.error_count += 1
    
    def add_system_metrics(self, memory_mb: float, cpu_percent: float):
        self.memory_usage.append(memory_mb)
        self.cpu_usage.append(cpu_percent)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.response_times:
            return {"error": "没有响应时间数据"}
        
        total_time = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        
        return {
            "总请求数": self.success_count + self.error_count,
            "成功请求数": self.success_count,
            "失败请求数": self.error_count,
            "成功率": f"{(self.success_count / (self.success_count + self.error_count) * 100):.2f}%" if (self.success_count + self.error_count) > 0 else "0%",
            "总耗时": f"{total_time:.2f}秒",
            "平均响应时间": f"{statistics.mean(self.response_times):.2f}ms",
            "中位数响应时间": f"{statistics.median(self.response_times):.2f}ms",
            "最小响应时间": f"{min(self.response_times):.2f}ms",
            "最大响应时间": f"{max(self.response_times):.2f}ms",
            "95百分位响应时间": f"{statistics.quantiles(self.response_times, n=20)[18]:.2f}ms" if len(self.response_times) >= 20 else "N/A",
            "99百分位响应时间": f"{statistics.quantiles(self.response_times, n=100)[98]:.2f}ms" if len(self.response_times) >= 100 else "N/A",
            "QPS": f"{self.success_count / total_time:.2f}" if total_time > 0 else "N/A",
            "平均内存使用": f"{statistics.mean(self.memory_usage):.2f}MB" if self.memory_usage else "N/A",
            "峰值内存使用": f"{max(self.memory_usage):.2f}MB" if self.memory_usage else "N/A",
            "平均CPU使用率": f"{statistics.mean(self.cpu_usage):.2f}%" if self.cpu_usage else "N/A",
            "峰值CPU使用率": f"{max(self.cpu_usage):.2f}%" if self.cpu_usage else "N/A"
        }

class MCPBenchmark:
    """MCP性能基准测试类"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.test_queries = [
            "Python编程教程",
            "机器学习算法",
            "人工智能发展",
            "Web开发框架",
            "数据库设计",
            "云计算技术",
            "网络安全",
            "移动应用开发",
            "区块链技术",
            "大数据分析"
        ]
        self.test_urls = [
            "https://www.python.org",
            "https://github.com",
            "https://stackoverflow.com",
            "https://docs.python.org",
            "https://www.w3schools.com"
        ]
    
    async def benchmark_single_search(self, query: str) -> tuple[float, bool]:
        """单次搜索基准测试"""
        start_time = time.time()
        try:
            result = await handle_call_tool("web_search", {"query": query, "max_results": 5})
            end_time = time.time()
            
            # 检查结果是否有效
            if result and len(result) > 0 and "错误" not in result[0].text:
                return (end_time - start_time) * 1000, True
            else:
                return (end_time - start_time) * 1000, False
        except Exception as e:
            end_time = time.time()
            print(f"搜索错误: {e}")
            return (end_time - start_time) * 1000, False
    
    async def benchmark_single_content_fetch(self, url: str) -> tuple[float, bool]:
        """单次内容获取基准测试"""
        start_time = time.time()
        try:
            result = await handle_call_tool("get_webpage_content", {"url": url})
            end_time = time.time()
            
            # 检查结果是否有效
            if result and len(result) > 0 and "错误" not in result[0].text and "无法获取" not in result[0].text:
                return (end_time - start_time) * 1000, True
            else:
                return (end_time - start_time) * 1000, False
        except Exception as e:
            end_time = time.time()
            print(f"内容获取错误: {e}")
            return (end_time - start_time) * 1000, False
    
    def get_system_metrics(self) -> tuple[float, float]:
        """获取系统指标"""
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024  # 转换为MB
        cpu_percent = self.process.cpu_percent()
        return memory_mb, cpu_percent
    
    async def run_sequential_benchmark(self, test_count: int = 50) -> BenchmarkResults:
        """运行顺序基准测试"""
        print(f"开始顺序基准测试 ({test_count} 次请求)...")
        results = BenchmarkResults()
        results.start_time = time.time()
        
        for i in range(test_count):
            # 交替测试搜索和内容获取
            if i % 2 == 0:
                query = self.test_queries[i % len(self.test_queries)]
                response_time, success = await self.benchmark_single_search(query)
                print(f"搜索测试 {i+1}/{test_count}: {query[:20]}... - {response_time:.2f}ms - {'成功' if success else '失败'}")
            else:
                url = self.test_urls[i % len(self.test_urls)]
                response_time, success = await self.benchmark_single_content_fetch(url)
                print(f"内容测试 {i+1}/{test_count}: {url} - {response_time:.2f}ms - {'成功' if success else '失败'}")
            
            results.add_response_time(response_time)
            if success:
                results.add_success()
            else:
                results.add_error()
            
            # 记录系统指标
            memory_mb, cpu_percent = self.get_system_metrics()
            results.add_system_metrics(memory_mb, cpu_percent)
            
            # 避免请求过于频繁
            await asyncio.sleep(0.1)
        
        results.end_time = time.time()
        return results
    
    async def run_concurrent_benchmark(self, concurrent_count: int = 10, requests_per_worker: int = 5) -> BenchmarkResults:
        """运行并发基准测试"""
        print(f"开始并发基准测试 ({concurrent_count} 并发, 每个worker {requests_per_worker} 请求)...")
        results = BenchmarkResults()
        results.start_time = time.time()
        
        async def worker(worker_id: int):
            worker_results = []
            for i in range(requests_per_worker):
                # 交替测试搜索和内容获取
                if (worker_id * requests_per_worker + i) % 2 == 0:
                    query = self.test_queries[(worker_id * requests_per_worker + i) % len(self.test_queries)]
                    response_time, success = await self.benchmark_single_search(query)
                    print(f"Worker {worker_id} 搜索 {i+1}: {response_time:.2f}ms - {'成功' if success else '失败'}")
                else:
                    url = self.test_urls[(worker_id * requests_per_worker + i) % len(self.test_urls)]
                    response_time, success = await self.benchmark_single_content_fetch(url)
                    print(f"Worker {worker_id} 内容 {i+1}: {response_time:.2f}ms - {'成功' if success else '失败'}")
                
                worker_results.append((response_time, success))
                await asyncio.sleep(0.05)  # 短暂延迟
            
            return worker_results
        
        # 创建并发任务
        tasks = [worker(i) for i in range(concurrent_count)]
        
        # 监控系统指标
        async def monitor_system():
            while not all(task.done() for task in tasks):
                memory_mb, cpu_percent = self.get_system_metrics()
                results.add_system_metrics(memory_mb, cpu_percent)
                await asyncio.sleep(0.5)
        
        monitor_task = asyncio.create_task(monitor_system())
        
        # 等待所有任务完成
        worker_results = await asyncio.gather(*tasks)
        monitor_task.cancel()
        
        # 汇总结果
        for worker_result in worker_results:
            for response_time, success in worker_result:
                results.add_response_time(response_time)
                if success:
                    results.add_success()
                else:
                    results.add_error()
        
        results.end_time = time.time()
        return results
    
    async def run_stress_test(self, duration_seconds: int = 60) -> BenchmarkResults:
        """运行压力测试"""
        print(f"开始压力测试 (持续 {duration_seconds} 秒)...")
        results = BenchmarkResults()
        results.start_time = time.time()
        end_time = results.start_time + duration_seconds
        
        request_count = 0
        
        # 监控系统指标
        async def monitor_system():
            while time.time() < end_time:
                memory_mb, cpu_percent = self.get_system_metrics()
                results.add_system_metrics(memory_mb, cpu_percent)
                await asyncio.sleep(1)
        
        monitor_task = asyncio.create_task(monitor_system())
        
        # 持续发送请求
        while time.time() < end_time:
            # 交替测试搜索和内容获取
            if request_count % 2 == 0:
                query = self.test_queries[request_count % len(self.test_queries)]
                response_time, success = await self.benchmark_single_search(query)
            else:
                url = self.test_urls[request_count % len(self.test_urls)]
                response_time, success = await self.benchmark_single_content_fetch(url)
            
            results.add_response_time(response_time)
            if success:
                results.add_success()
            else:
                results.add_error()
            
            request_count += 1
            
            if request_count % 10 == 0:
                print(f"压力测试进行中... 已完成 {request_count} 请求")
            
            await asyncio.sleep(0.1)  # 控制请求频率
        
        monitor_task.cancel()
        results.end_time = time.time()
        return results
    
    def print_results(self, test_name: str, results: BenchmarkResults):
        """打印测试结果"""
        print(f"\n{'='*60}")
        print(f"{test_name} - 测试结果")
        print(f"{'='*60}")
        
        stats = results.get_statistics()
        for key, value in stats.items():
            print(f"{key:20}: {value}")
        
        print(f"{'='*60}\n")
    
    def save_results_to_file(self, results_data: Dict[str, Any], filename: str = "benchmark_results.json"):
        """保存结果到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        print(f"测试结果已保存到: {filename}")

async def main():
    """主函数"""
    print("MCP Web Search Server 性能基准测试")
    print("=" * 50)
    
    benchmark = MCPBenchmark()
    all_results = {}
    
    try:
        # 1. 顺序基准测试
        sequential_results = await benchmark.run_sequential_benchmark(30)
        benchmark.print_results("顺序基准测试", sequential_results)
        all_results["sequential"] = sequential_results.get_statistics()
        
        # 等待一段时间让系统恢复
        print("等待系统恢复...")
        await asyncio.sleep(5)
        
        # 2. 并发基准测试
        concurrent_results = await benchmark.run_concurrent_benchmark(5, 4)
        benchmark.print_results("并发基准测试", concurrent_results)
        all_results["concurrent"] = concurrent_results.get_statistics()
        
        # 等待一段时间让系统恢复
        print("等待系统恢复...")
        await asyncio.sleep(5)
        
        # 3. 压力测试
        stress_results = await benchmark.run_stress_test(30)
        benchmark.print_results("压力测试", stress_results)
        all_results["stress"] = stress_results.get_statistics()
        
        # 保存所有结果
        benchmark.save_results_to_file(all_results)
        
        # 生成总结报告
        print("\n" + "=" * 60)
        print("基准测试总结")
        print("=" * 60)
        
        print("\n推荐配置:")
        if float(all_results["sequential"]["平均响应时间"].replace("ms", "")) < 2000:
            print("✅ 响应时间表现良好")
        else:
            print("⚠️  响应时间较慢，建议优化网络连接")
        
        if float(all_results["concurrent"]["成功率"].replace("%", "")) > 90:
            print("✅ 并发处理能力良好")
        else:
            print("⚠️  并发处理能力需要改进")
        
        peak_memory = max(
            float(all_results["sequential"]["峰值内存使用"].replace("MB", "")),
            float(all_results["concurrent"]["峰值内存使用"].replace("MB", "")),
            float(all_results["stress"]["峰值内存使用"].replace("MB", ""))
        )
        
        if peak_memory < 200:
            print("✅ 内存使用效率良好")
        else:
            print("⚠️  内存使用较高，建议监控")
        
        print(f"\n建议生产环境配置:")
        print(f"- 最小内存: {peak_memory * 1.5:.0f}MB")
        print(f"- 推荐内存: {peak_memory * 2:.0f}MB")
        print(f"- 建议并发限制: 5-10个并发请求")
        print(f"- 建议请求频率: 每秒不超过10个请求")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())