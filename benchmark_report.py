#!/usr/bin/env python3
"""
MCP Web Search Server 基准测试报告生成器
"""

import datetime
import json
import os
from typing import Any, Dict, List


class BenchmarkReportGenerator:
    """基准测试报告生成器"""

    def __init__(self, config_file: str = "benchmark_config.json"):
        self.config = self.load_config(config_file)
        self.thresholds = self.config.get("performance_thresholds", {})

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_file, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"配置文件 {config_file} 未找到，使用默认配置")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "performance_thresholds": {
                "search_response_time": {
                    "excellent": 1500,
                    "good": 3000,
                    "acceptable": 5000,
                },
                "content_response_time": {
                    "excellent": 2000,
                    "good": 5000,
                    "acceptable": 10000,
                },
                "success_rate": {"excellent": 90, "good": 75, "acceptable": 60},
            }
        }

    def evaluate_performance(
        self, metric_value: float, metric_type: str
    ) -> tuple[str, str]:
        """评估性能指标"""
        thresholds = self.thresholds.get(metric_type, {})

        if metric_type.endswith("_rate"):
            # 成功率类指标，值越高越好
            if metric_value >= thresholds.get("excellent", 90):
                return "优秀", "🟢"
            elif metric_value >= thresholds.get("good", 75):
                return "良好", "🟡"
            elif metric_value >= thresholds.get("acceptable", 60):
                return "可接受", "🟠"
            else:
                return "需要改进", "🔴"
        else:
            # 响应时间类指标，值越低越好
            if metric_value <= thresholds.get("excellent", 2000):
                return "优秀", "🟢"
            elif metric_value <= thresholds.get("good", 5000):
                return "良好", "🟡"
            elif metric_value <= thresholds.get("acceptable", 10000):
                return "可接受", "🟠"
            else:
                return "需要改进", "🔴"

    def generate_markdown_report(
        self, results: List[Dict[str, Any]], output_file: str = "benchmark_report.md"
    ):
        """生成Markdown格式的报告"""

        report_lines = []

        # 报告头部
        report_lines.extend(
            [
                "# MCP Web Search Server 性能基准测试报告",
                "",
                f"**生成时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**测试环境**: {os.uname().sysname} {os.uname().release}",
                "",
                "## 📊 测试概览",
                "",
            ]
        )

        # 测试结果概览表格
        report_lines.extend(
            [
                "| 测试类型 | 总请求数 | 成功请求数 | 成功率 | 平均响应时间 | 性能评级 |",
                "|----------|----------|------------|--------|--------------|----------|",
            ]
        )

        for result in results:
            test_type = result.get("type", "Unknown")
            total_requests = result.get(
                "total_requests", result.get("concurrent_requests", "N/A")
            )
            successful_requests = result.get("successful_requests", "N/A")
            success_rate = result.get("success_rate", "N/A")
            avg_response_time = result.get("avg_response_time", "N/A")

            # 评估性能
            if success_rate != "N/A":
                success_rate_value = float(success_rate.replace("%", ""))
                _, success_icon = self.evaluate_performance(
                    success_rate_value, "success_rate"
                )
            else:
                success_icon = "❓"

            if avg_response_time != "N/A":
                response_time_value = float(avg_response_time.replace("ms", ""))
                if "search" in test_type.lower() or "搜索" in test_type:
                    _, time_icon = self.evaluate_performance(
                        response_time_value, "search_response_time"
                    )
                else:
                    _, time_icon = self.evaluate_performance(
                        response_time_value, "content_response_time"
                    )
            else:
                time_icon = "❓"

            performance_rating = f"{success_icon}{time_icon}"

            report_lines.append(
                f"| {test_type} | {total_requests} | {successful_requests} | {success_rate} | {avg_response_time} | {performance_rating} |"
            )

        report_lines.extend(["", "## 📈 详细分析", ""])

        # 详细分析每个测试类型
        for result in results:
            test_type = result.get("type", "Unknown")
            report_lines.extend([f"### {test_type}", ""])

            # 基本指标
            report_lines.append("**基本指标:**")
            report_lines.append("")

            for key, value in result.items():
                if key != "type":
                    # 格式化键名
                    key_cn = {
                        "total_requests": "总请求数",
                        "successful_requests": "成功请求数",
                        "success_rate": "成功率",
                        "avg_response_time": "平均响应时间",
                        "min_response_time": "最小响应时间",
                        "max_response_time": "最大响应时间",
                        "median_response_time": "中位数响应时间",
                        "concurrent_requests": "并发请求数",
                        "total_time": "总耗时",
                        "throughput": "吞吐量",
                    }.get(key, key)

                    report_lines.append(f"- **{key_cn}**: {value}")

            report_lines.append("")

            # 性能评估
            if "success_rate" in result and "avg_response_time" in result:
                success_rate_value = float(result["success_rate"].replace("%", ""))
                response_time_value = float(
                    result["avg_response_time"].replace("ms", "")
                )

                success_eval, success_icon = self.evaluate_performance(
                    success_rate_value, "success_rate"
                )

                if "search" in test_type.lower() or "搜索" in test_type:
                    time_eval, time_icon = self.evaluate_performance(
                        response_time_value, "search_response_time"
                    )
                else:
                    time_eval, time_icon = self.evaluate_performance(
                        response_time_value, "content_response_time"
                    )

                report_lines.extend(
                    [
                        "**性能评估:**",
                        "",
                        f"- 成功率: {success_icon} {success_eval}",
                        f"- 响应时间: {time_icon} {time_eval}",
                        "",
                    ]
                )

        # 总体建议
        report_lines.extend(
            [
                "## 💡 优化建议",
                "",
                self.generate_recommendations(results),
                "",
                "## 🔧 性能调优指南",
                "",
                "### 网络优化",
                "- 使用CDN加速静态资源",
                "- 启用HTTP/2协议",
                "- 优化DNS解析",
                "- 使用连接池复用连接",
                "",
                "### 应用优化",
                "- 实现智能缓存策略",
                "- 优化搜索算法",
                "- 使用异步处理",
                "- 限制并发请求数量",
                "",
                "### 监控建议",
                "- 设置性能监控告警",
                "- 定期运行基准测试",
                "- 监控系统资源使用",
                "- 记录详细的性能日志",
                "",
                "---",
                f"*报告生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ]
        )

        # 写入文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        print(f"📄 Markdown报告已生成: {output_file}")

    def generate_recommendations(self, results: List[Dict[str, Any]]) -> str:
        """生成优化建议"""
        recommendations = []

        for result in results:
            test_type = result.get("type", "")

            if "success_rate" in result:
                success_rate = float(result["success_rate"].replace("%", ""))
                if success_rate < 80:
                    recommendations.append(
                        f"- **{test_type}**: 成功率较低({result['success_rate']})，建议检查网络连接和目标网站可用性"
                    )

            if "avg_response_time" in result:
                response_time = float(result["avg_response_time"].replace("ms", ""))
                if response_time > 5000:
                    recommendations.append(
                        f"- **{test_type}**: 响应时间较长({result['avg_response_time']})，建议优化网络配置或增加缓存"
                    )
                elif response_time > 3000:
                    recommendations.append(
                        f"- **{test_type}**: 响应时间偏高({result['avg_response_time']})，可考虑性能优化"
                    )

            if "throughput" in result:
                throughput = float(result["throughput"].split()[0])
                if throughput < 1:
                    recommendations.append(
                        f"- **{test_type}**: 吞吐量较低({result['throughput']})，建议优化并发处理能力"
                    )

        if not recommendations:
            recommendations.append("- 🎉 所有测试指标表现良好，继续保持！")
            recommendations.append("- 建议定期运行基准测试以监控性能变化")
            recommendations.append("- 可以考虑在更高负载下进行压力测试")

        return "\n".join(recommendations)

    def generate_csv_report(
        self, results: List[Dict[str, Any]], output_file: str = "benchmark_results.csv"
    ):
        """生成CSV格式的报告"""
        import csv

        if not results:
            print("没有测试结果数据")
            return

        # 获取所有可能的字段
        all_fields = set()
        for result in results:
            all_fields.update(result.keys())

        all_fields = sorted(list(all_fields))

        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_fields)
            writer.writeheader()

            for result in results:
                writer.writerow(result)

        print(f"📊 CSV报告已生成: {output_file}")


def main():
    """主函数"""
    print("📋 MCP Web Search Server 基准测试报告生成器")
    print("=" * 50)

    # 检查是否存在测试结果文件
    result_files = ["quick_benchmark_results.json", "benchmark_results.json"]

    results_data = None
    used_file = None

    for file_name in result_files:
        if os.path.exists(file_name):
            try:
                with open(file_name, encoding="utf-8") as f:
                    results_data = json.load(f)
                used_file = file_name
                print(f"✅ 找到测试结果文件: {file_name}")
                break
            except Exception as e:
                print(f"❌ 读取文件 {file_name} 失败: {e}")

    if not results_data:
        print("❌ 未找到有效的测试结果文件")
        print("请先运行基准测试:")
        print("  python quick_benchmark.py")
        print("  或")
        print("  python benchmark.py")
        return

    # 生成报告
    generator = BenchmarkReportGenerator()

    print(f"\n📊 基于 {used_file} 生成报告...")

    # 生成Markdown报告
    generator.generate_markdown_report(results_data, "benchmark_report.md")

    # 生成CSV报告
    generator.generate_csv_report(results_data, "benchmark_results.csv")

    print("\n✅ 报告生成完成！")
    print("\n生成的文件:")
    print("  📄 benchmark_report.md - 详细的Markdown报告")
    print("  📊 benchmark_results.csv - CSV格式的数据")


if __name__ == "__main__":
    main()
