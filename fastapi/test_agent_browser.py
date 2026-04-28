"""
测试 agent-browser 是否能正常工作
用于验证 agent-browser CLI 工具的安装和基本功能
"""

import subprocess
import json
import time


def run_command(cmd, timeout=30):
    """
    执行 agent-browser 命令并返回结果
    
    参数:
        cmd: 命令列表，如 ["agent-browser", "open", "https://baike.baidu.com"]
        timeout: 超时时间（秒）
    
    返回:
        dict: 包含 stdout, stderr, returncode 的字典
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8'
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"命令执行超时（{timeout}秒）",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }


def test_agent_browser_version():
    """测试 agent-browser 版本"""
    print("=" * 50)
    print("测试 1: 检查 agent-browser 版本")
    print("=" * 50)
    
    result = run_command(["agent-browser", "--version"], timeout=5)
    
    if result["success"]:
        print(f"[OK] agent-browser 已安装")
        print(f"版本信息: {result['stdout'].strip()}")
    else:
        print(f"[FAIL] agent-browser 未安装或命令不存在")
        print(f"错误: {result['stderr']}")
    
    return result["success"]


def test_agent_browser_doctor():
    """测试 agent-browser 诊断"""
    print("\n" + "=" * 50)
    print("测试 2: 运行 agent-browser 诊断")
    print("=" * 50)
    
    result = run_command(["agent-browser", "doctor"], timeout=30)
    
    if result["success"]:
        print(f"[OK] 诊断通过")
        print(f"输出: {result['stdout'][:500]}...")  # 只显示前500字符
    else:
        print(f"[FAIL] 诊断失败")
        print(f"错误: {result['stderr'][:500]}")
    
    return result["success"]


def test_open_baidu():
    """测试打开百度"""
    print("\n" + "=" * 50)
    print("测试 3: 打开百度首页")
    print("=" * 50)
    
    result = run_command(["agent-browser", "open", "https://www.baidu.com"], timeout=15)
    
    if result["success"]:
        print(f"[OK] 成功打开百度")
        print(f"输出: {result['stdout'][:200]}")
    else:
        print(f"[FAIL] 打开失败")
        print(f"错误: {result['stderr'][:500]}")
    
    return result["success"]


def test_open_baike():
    """测试打开百度百科"""
    print("\n" + "=" * 50)
    print("测试 4: 打开百度百科")
    print("=" * 50)
    
    result = run_command(["agent-browser", "open", "https://baike.baidu.com"], timeout=15)
    
    if result["success"]:
        print(f"[OK] 成功打开百度百科")
        print(f"输出: {result['stdout'][:200]}")
    else:
        print(f"[FAIL] 打开失败")
        print(f"错误: {result['stderr'][:500]}")
    
    return result["success"]


def test_snapshot():
    """测试获取页面快照"""
    print("\n" + "=" * 50)
    print("测试 5: 获取页面快照")
    print("=" * 50)
    
    # 先打开百度
    run_command(["agent-browser", "open", "https://www.baidu.com"], timeout=10)
    time.sleep(2)  # 等待页面加载
    
    # 获取快照
    result = run_command(["agent-browser", "snapshot", "-i", "--json"], timeout=10)
    
    if result["success"]:
        print(f"[OK] 成功获取快照")
        try:
            data = json.loads(result['stdout'])
            print(f"快照包含 {len(data.get('data', {}).get('refs', {}))} 个元素")
        except:
            print(f"输出: {result['stdout'][:300]}")
    else:
        print(f"[FAIL] 获取快照失败")
        print(f"错误: {result['stderr'][:500]}")
    
    return result["success"]


def test_close_browser():
    """测试关闭浏览器"""
    print("\n" + "=" * 50)
    print("测试 6: 关闭浏览器")
    print("=" * 50)
    
    result = run_command(["agent-browser", "close"], timeout=10)
    
    if result["success"]:
        print(f"[OK] 成功关闭浏览器")
    else:
        print(f"[WARN] 关闭时出现问题（可能已关闭）")
        print(f"错误: {result['stderr'][:300]}")
    
    return True  # 关闭失败不影响整体结果


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("agent-browser 功能测试")
    print("=" * 60)
    
    results = []
    
    # 执行各项测试
    results.append(("版本检查", test_agent_browser_version()))
    results.append(("诊断检查", test_agent_browser_doctor()))
    results.append(("打开百度", test_open_baidu()))
    results.append(("打开百度百科", test_open_baike()))
    results.append(("页面快照", test_snapshot()))
    results.append(("关闭浏览器", test_close_browser()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, success in results:
        status = "[OK] 通过" if success else "[FAIL] 失败"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("[SUCCESS] 所有测试通过，agent-browser 可以正常使用！")
    elif passed >= 4:
        print("[WARN] 部分测试未通过，但核心功能可用")
    else:
        print("[ERROR] 测试未通过较多，请检查安装")


if __name__ == "__main__":
    main()
