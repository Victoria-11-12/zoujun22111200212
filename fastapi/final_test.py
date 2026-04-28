import subprocess
import time
import json
from datetime import datetime

def safe_print(text):
    """安全打印函数，完全避免编码问题"""
    safe_text = text.replace('✓', '[OK]').replace('✗', '[FAIL]').replace('⚠', '[WARN]')
    safe_text = safe_text.replace('\u2713', '[OK]').replace('\u2717', '[FAIL]').replace('\u26a0', '[WARN]')
    print(safe_text)

def run_agent_command(cmd):
    """运行agent-browser命令"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            shell=True,
            timeout=30
        )
        
        stdout = result.stdout.decode('utf-8', errors='ignore') if result.stdout else ""
        stderr = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ""
        
        return {
            "success": result.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def main():
    safe_print("=== 百度百科搜索测试 ===")
    
    movie_data = {
        "search_keyword": "战狼2",
        "search_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "home_page_title": "",
        "result_page_title": "",
        "result_page_url": "",
        "search_success": False,
        "movie_info": {}
    }
    
    # 1. 测试agent-browser是否正常工作
    safe_print("\n[1] 测试agent-browser...")
    result = run_agent_command('agent-browser --version')
    if result['success']:
        safe_print(f"[OK] agent-browser版本: {result['stdout'].strip()}")
    else:
        safe_print(f"[FAIL] 测试失败: {result['stderr'][:200]}")
        return
    
    # 2. 打开百度百科
    safe_print("\n[2] 打开百度百科...")
    result = run_agent_command('agent-browser open "https://baike.baidu.com"')
    
    if result['success']:
        safe_print("[OK] 页面打开成功")
        time.sleep(5)
    else:
        safe_print(f"[FAIL] 打开失败: {result['stderr'][:200]}")
        return
    
    # 3. 获取页面标题
    safe_print("\n[3] 获取页面信息...")
    result = run_agent_command('agent-browser eval "document.title"')
    if result['success']:
        home_title = result['stdout'].strip().strip('"')
        safe_print(f"[OK] 页面标题: {home_title}")
        movie_data["home_page_title"] = home_title
    else:
        safe_print(f"[FAIL] 获取标题失败: {result['stderr'][:200]}")
    
    # 4. 获取页面快照找到搜索框
    safe_print("\n[4] 获取页面快照...")
    result = run_agent_command('agent-browser snapshot -i')
    if result['success']:
        safe_print("[OK] 快照获取成功")
        
        # 检查是否包含textbox
        if 'textbox' in result['stdout']:
            safe_print("[OK] 找到搜索框(textbox)")
        else:
            safe_print("[FAIL] 未找到搜索框")
            return
    else:
        safe_print(f"[FAIL] 快照失败: {result['stderr'][:200]}")
        return
    
    # 5. 使用ref填充搜索框
    safe_print("\n[5] 填充搜索框...")
    result = run_agent_command('agent-browser fill @e84 "战狼2"')
    if result['success']:
        safe_print("[OK] 填充成功")
        time.sleep(1)
    else:
        safe_print(f"[FAIL] 填充失败: {result['stderr'][:200]}")
        return
    
    # 6. 点击"进入词条"按钮
    safe_print("\n[6] 点击搜索按钮...")
    result = run_agent_command('agent-browser click @e71')
    if result['success']:
        safe_print("[OK] 点击成功")
        time.sleep(3)
    else:
        safe_print(f"[FAIL] 点击失败: {result['stderr'][:200]}")
        return
    
    # 7. 获取搜索结果页面标题
    safe_print("\n[7] 获取搜索结果...")
    result = run_agent_command('agent-browser eval "document.title"')
    if result['success']:
        result_title = result['stdout'].strip().strip('"')
        safe_print(f"[OK] 结果页面标题: {result_title}")
        movie_data["result_page_title"] = result_title
    
    # 8. 获取页面URL
    safe_print("\n[8] 获取页面URL...")
    result = run_agent_command('agent-browser eval "window.location.href"')
    if result['success']:
        result_url = result['stdout'].strip().strip('"')
        safe_print(f"[OK] 页面URL: {result_url}")
        movie_data["result_page_url"] = result_url
    
    # 9. 获取页面快照提取信息
    safe_print("\n[9] 获取页面快照提取信息...")
    result = run_agent_command('agent-browser snapshot')
    if result['success']:
        safe_print("[OK] 快照获取成功")
        
        # 从快照中提取信息
        snapshot_text = result['stdout']
        movie_info = {}
        
        # 提取电影名称
        if 'heading "战狼Ⅱ"' in snapshot_text:
            movie_info['电影名称'] = '战狼Ⅱ'
        
        # 提取基本信息
        if '2017年吴京执导的动作电影' in snapshot_text:
            movie_info['基本信息'] = '2017年吴京执导的动作电影'
        
        # 提取剧情简介（从快照中查找）
        lines = snapshot_text.split('\n')
        for i, line in enumerate(lines):
            if '《战狼Ⅱ》是由吴京执导' in line:
                # 获取这一行及后续几行的内容
                intro_lines = []
                for j in range(i, min(i+5, len(lines))):
                    intro_lines.append(lines[j].strip())
                    if '...' in lines[j]:
                        break
                movie_info['剧情简介'] = ' '.join(intro_lines)
                break
        
        # 提取主要演员
        actors = []
        actor_section = False
        for line in lines:
            if '主要演员' in line:
                actor_section = True
                continue
            if actor_section and 'link "' in line:
                # 提取演员名字
                start = line.find('link "') + 6
                end = line.find('"', start)
                if start > 5 and end > start:
                    actor_name = line[start:end]
                    if len(actor_name) >= 2 and len(actor_name) <= 10:
                        actors.append(actor_name)
            if actor_section and len(actors) >= 4:
                break
        
        if actors:
            movie_info['主要演员'] = '、'.join(actors[:4])
        
        movie_data["movie_info"] = movie_info
        safe_print(f"[OK] 提取到 {len(movie_info)} 个信息字段")
        
        # 显示提取到的信息
        for key, value in movie_info.items():
            if len(str(value)) > 100:
                safe_print(f"    {key}: {str(value)[:100]}...")
            else:
                safe_print(f"    {key}: {value}")
    else:
        safe_print(f"[FAIL] 快照失败: {result['stderr'][:200]}")
    
    movie_data["search_success"] = True
    
    # 10. 保存数据到文件
    safe_print("\n[10] 保存数据到文件...")
    output_file = "movie_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(movie_data, f, ensure_ascii=False, indent=4)
    safe_print(f"[OK] 数据已保存到 {output_file}")
    
    safe_print("\n=== 搜索完成 ===")

if __name__ == "__main__":
    main()
