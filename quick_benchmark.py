#!/usr/bin/env python3
"""
MCP Web Search Server 快速基准测试
简化版本，用于快速性能评估
"""

import asyncio
import time
import statistics
import json
from server import handle_call_tool

class QuickBenchmark:
    """快速基准测试类"""
    
    def __init__(self):
        self.test_queries = [
            "Python",
            "JavaScript",
            "机器学习",
            "Web开发",
            "数据库"
        ]
        self.test_urls = [
            "https://www.python.org",
            "https://github.com",
            "https://stackoverflow.com"
        ]
    
    async def test_search_performance(self, iterations: int = 10):
        """测试搜索性能"""
        print(f"\n🔍 测试搜索功能性能 ({iterations} 次)...")
        
        response_times = []
        success_count = 0
        
        for i in range(iterations):
            query = self.test_queries[i % len(self.test_queries)]
            
            start_time = time.time()
            try:
                result = await handle_call_tool("web_search", {
                    "query": query,
                    "max_results": 3
                })
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000
                response_times.append(response_time)
                
                if result and len(result) > 0 and "错误" not in result[0].text:
                    success_count += 1
                    status = "✅"
                else:
                    status = "❌"
                
                print(f"  {i+1:2d}. {query:12} - {response_time:6.0f}ms {status}")
                
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                response_times.append(response_time)
                print(f"  {i+1:2d}. {query:12} - {response_time:6.0f}ms ❌ 错误: {str(e)[:30]}")
            
            await asyncio.sleep(0.2)  # 避免请求过于频繁
        
        return {
            "type": "搜索功能",
            "total_requests": iterations,
            "successful_requests": success_count,
            "success_rate": f"{(success_count/iterations*100):.1f}%",
            "avg_response_time": f"{statistics.mean(response_times):.0f}ms",
            "min_response_time": f"{min(response_times):.0f}ms",
            "max_response_time": f"{max(response_times):.0f}ms",
            "median_response_time": f"{statistics.median(response_times):.0f}ms"
        }
    
    async def test_content_performance(self, iterations: int = 5):
        """测试内容获取性能"""
        print(f"\n📄 测试内容获取性能 ({iterations} 次)...")
        
        response_times = []
        success_count = 0
        
        for i in range(iterations):
            url = self.test_urls[i % len(self.test_urls)]
            
            start_time = time.time()
            try:
                result = await handle_call_tool("get_webpage_content", {
                    "url": url
                })
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000
                response_times.append(response_time)
                
                if result and len(result) > 0 and "错误" not in result[0].text and "无法获取" not in result[0].text:
                    success_count += 1
                    status = "✅"
                    content_length = len(result[0].text)
                    print(f"  {i+1}. {url:25} - {response_time:6.0f}ms {status} ({content_length} 字符)")
                else:
                    status = "❌"
                    print(f"  {i+1}. {url:25} - {response_time:6.0f}ms {status}")
                
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                response_times.append(response_time)
                print(f"  {i+1}. {url:25} - {response_time:6.0f}ms ❌ 错误: {str(e)[:30]}")
            
            await asyncio.sleep(0.5)  # 内容获取间隔稍长
        
        return {
            "type": "内容获取",
            "total_requests": iterations,
            "successful_requests": success_count,
            "success_rate": f"{(success_count/iterations*100):.1f}%",
            "avg_response_time": f"{statistics.mean(response_times):.0f}ms" if response_times else "N/A",
            "min_response_time": f"{min(response_times):.0f}ms" if response_times else "N/A",
            "max_response_time": f"{max(response_times):.0f}ms" if response_times else "N/A",
            "median_response_time": f"{statistics.median(response_times):.0f}ms" if response_times else "N/A"
        }
    
    async def test_concurrent_performance(self, concurrent_requests: int = 3):
        """测试并发性能"""
        print(f"\n⚡ 测试并发性能 ({concurrent_requests} 个并发请求)...")
        
        async def single_request(request_id: int):
            query = self.test_queries[request_id % len(self.test_queries)]
            start_time = time.time()
            
            try:
                result = await handle_call_tool("web_search", {
                    "query": query,
                    "max_results": 2
                })
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000
                success = result and len(result) > 0 and "错误" not in result[0].text
                
                print(f"  并发请求 {request_id+1}: {query} - {response_time:.0f}ms {'✅' if success else '❌'}")
                return response_time, success
                
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                print(f"  并发请求 {request_id+1}: {query} - {response_time:.0f}ms ❌ {str(e)[:20]}")
                return response_time, False
        
        start_time = time.time()
        tasks = [single_request(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000
        
        response_times = [r[0] for r in results]
        success_count = sum(1 for r in results if r[1])
        
        return {
            "type": "并发测试",
            "concurrent_requests": concurrent_requests,
            "total_time": f"{total_time:.0f}ms",
            "successful_requests": success_count,
            "success_rate": f"{(success_count/concurrent_requests*100):.1f}%",
            "avg_response_time": f"{statistics.mean(response_times):.0f}ms",
            "max_response_time": f"{max(response_times):.0f}ms",
            "throughput": f"{concurrent_requests / (total_time/1000):.1f} 请求/秒"
        }
    
    def print_summary(self, results: list):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📊 快速基准测试总结")
        print("="*60)
        
        for result in results:
            print(f"\n🔸 {result['type']}:")
            for key, value in result.items():
                if key != 'type':
                    print(f"   {key:20}: {value}")
        
        # 性能评估
        print("\n🎯 性能评估:")
        
        search_result = next((r for r in results if r['type'] == '搜索功能'), None)
        if search_result:
            avg_time = float(search_result['avg_response_time'].replace('ms', ''))
            success_rate = float(search_result['success_rate'].replace('%', ''))
            
            if avg_time < 2000 and success_rate > 80:
                print("   搜索性能: ✅ 优秀")
            elif avg_time < 5000 and success_rate > 60:
                print("   搜索性能: ⚠️  良好")
            else:
                print("   搜索性能: ❌ 需要改进")
        
        content_result = next((r for r in results if r['type'] == '内容获取'), None)
        if content_result:
            success_rate = float(content_result['success_rate'].replace('%', ''))
            
            if success_rate > 80:
                print("   内容获取: ✅ 优秀")
            elif success_rate > 60:
                print("   内容获取: ⚠️  良好")
            else:
                print("   内容获取: ❌ 需要改进")
        
        concurrent_result = next((r for r in results if r['type'] == '并发测试'), None)
        if concurrent_result:
            success_rate = float(concurrent_result['success_rate'].replace('%', ''))
            
            if success_rate > 80:
                print("   并发处理: ✅ 优秀")
            elif success_rate > 60:
                print("   并发处理: ⚠️  良好")
            else:
                print("   并发处理: ❌ 需要改进")
        
        print("\n💡 建议:")
        print("   - 如果响应时间过长，检查网络连接")
        print("   - 如果成功率较低，可能是目标网站限制访问")
        print("   - 建议在生产环境中限制并发请求数量")
        print("   - 定期运行基准测试以监控性能变化")

async def main():
    """主函数"""
    print("🚀 MCP Web Search Server - 快速基准测试")
    print("=" * 50)
    
    benchmark = QuickBenchmark()
    results = []
    
    try:
        # 测试搜索性能
        search_result = await benchmark.test_search_performance(8)
        results.append(search_result)
        
        # 测试内容获取性能
        content_result = await benchmark.test_content_performance(3)
        results.append(content_result)
        
        # 测试并发性能
        concurrent_result = await benchmark.test_concurrent_performance(3)
        results.append(concurrent_result)
        
        # 打印总结
        benchmark.print_summary(results)
        
        # 保存结果
        with open('/root/mcp_dev/quick_benchmark_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 测试结果已保存到: quick_benchmark_results.json")
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())