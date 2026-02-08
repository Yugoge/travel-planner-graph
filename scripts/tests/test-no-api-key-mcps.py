#!/usr/bin/env python3
"""
完整测试不需要 API key 的 MCP 技能
"""

import subprocess
import json
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).parent.parent.parent)

def run_test(skill_name, description, command, expected_patterns=None):
    """运行单个测试"""
    print(f"\n{'='*60}")
    print(f"🧪 测试: {skill_name}")
    print(f"描述: {description}")
    print(f"命令: {command}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"\n📤 返回码: {result.returncode}")

        if result.stdout:
            print(f"\n✅ 标准输出:")
            print(result.stdout[:1000])  # 限制输出长度

            # 检查期望的模式
            if expected_patterns:
                for pattern in expected_patterns:
                    if pattern in result.stdout.lower():
                        print(f"   ✓ 找到期望内容: {pattern}")
                    else:
                        print(f"   ✗ 未找到期望内容: {pattern}")

        if result.stderr:
            print(f"\n⚠️  标准错误:")
            print(result.stderr[:500])

        # 判断测试是否成功
        if result.returncode == 0:
            print(f"\n✅ {skill_name} 测试通过!")
            return True
        else:
            print(f"\n❌ {skill_name} 测试失败 (返回码: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print(f"\n⏱️  测试超时 (30秒)")
        return False
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        return False


def main():
    """执行所有测试"""
    print("🚀 开始测试不需要 API key 的 MCP 技能")
    print("="*60)

    results = {}

    # 测试 1: Weather - 获取天气预报
    results['weather_forecast'] = run_test(
        skill_name="Weather - 天气预报",
        description="测试获取纽约未来天气预报",
        command="python3 /root/travel-planner/.claude/skills/weather/scripts/forecast.py 40.7128 -74.0060",
        expected_patterns=["temperature", "forecast", "weather"]
    )

    # 测试 2: Weather - 搜索位置
    results['weather_location'] = run_test(
        skill_name="Weather - 位置搜索",
        description="测试搜索城市位置",
        command="python3 /root/travel-planner/.claude/skills/weather/scripts/location.py 'New York'",
        expected_patterns=["latitude", "longitude", "new york"]
    )

    # 测试 3: Weather - 获取当前天气
    results['weather_current'] = run_test(
        skill_name="Weather - 当前天气",
        description="测试获取洛杉矶当前天气",
        command="python3 /root/travel-planner/.claude/skills/weather/scripts/current.py 34.0522 -118.2437",
        expected_patterns=["temperature", "weather", "condition"]
    )

    # 测试 4: Airbnb - 搜索（使用最小参数）
    results['airbnb_search'] = run_test(
        skill_name="Airbnb - 房源搜索",
        description="测试搜索巴黎房源（可能被 robots.txt 阻止）",
        command="python3 /root/travel-planner/.claude/skills/airbnb/scripts/search.py 'Paris, France' --checkin '2026-03-01' --checkout '2026-03-05'",
        expected_patterns=["listing", "price", "airbnb", "disallowed", "robots"]
    )

    # 测试 5: 12306 - 获取当前日期（最简单的测试）
    results['12306_date'] = run_test(
        skill_name="12306 - 获取当前日期",
        description="测试 12306 MCP 服务器连接",
        command="python3 /root/travel-planner/.claude/skills/12306/scripts/get_current_date.py",
        expected_patterns=["date", "2026"]
    )

    # 汇总结果
    print(f"\n\n{'='*60}")
    print("📊 测试结果汇总")
    print(f"{'='*60}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✅ 通过" if passed_test else "❌ 失败"
        print(f"{status} - {test_name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
