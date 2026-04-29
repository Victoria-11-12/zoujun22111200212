# 网络爬虫工具
# 用于从百度百科搜索电影信息

import re
import time
import subprocess
from langchain.tools import tool


def run_agent_command(cmd: str, timeout: int = 30) -> dict:
    """
    运行agent-browser命令行工具
    
    参数:
        cmd: 要执行的命令字符串，如 'agent-browser open "https://baike.baidu.com"'
        timeout: 命令执行超时时间（秒），默认30秒
    
    返回:
        dict: 包含执行结果的字典
            - success: 布尔值，表示命令是否成功执行
            - stdout: 字符串，命令的标准输出
            - stderr: 字符串，命令的错误输出
            - returncode: 整数，命令的返回码（0表示成功）
    """
    try:
        # subprocess.run() 执行外部命令
        # capture_output=True 表示捕获命令的输出
        # shell=True 表示通过shell执行命令（Windows环境必需）
        # timeout 设置超时时间，防止命令卡死
        result = subprocess.run(
            cmd,
            capture_output=True,
            shell=True,
            timeout=timeout
        )
        
        # 解码输出，使用UTF-8编码，errors='ignore'忽略无法解码的字符
        stdout = result.stdout.decode('utf-8', errors='ignore') if result.stdout else ""
        stderr = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ""
        
        return {
            "success": result.returncode == 0,  # 返回码为0表示成功
            "stdout": stdout,
            "stderr": stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        # 捕获异常，返回失败结果
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }


@tool
def baike_search_tool(movie_name: str) -> str:
    """
    从百度百科搜索电影信息的LangChain工具
    
    这是一个被@tool装饰器封装的函数，可以被LangChain Agent自动调用。
    当本地数据库没有找到电影信息时，Agent会调用此工具从百度百科搜索。
    
    参数:
        movie_name: 电影名称，如"战狼2"、"阿凡达"等
    
    返回:
        str: 格式化的电影信息字符串，包含电影名称、基本信息、剧情简介、主要演员等
             如果搜索失败，返回错误信息字符串
    """
    # 正则拦截：只允许中文、英文、数字、空格、常见标点
    if not re.match(r'^[\w\u4e00-\u9fff\s\-\.·\(\)（）\!！\?？]+$', movie_name):
        return "电影名称包含非法字符，已拒绝执行"
    
    try:
        # 步骤1: 打开百度百科首页
        result = run_agent_command('agent-browser open "https://baike.baidu.com"')
        if not result['success']:
            return f"打开百度百科失败: {result['stderr'][:100]}"
        
        time.sleep(5)  # 等待页面加载完成
        
        # 步骤2: 获取页面交互元素快照，找到搜索框
        # snapshot -i 参数表示只获取可交互元素（输入框、按钮等）
        result = run_agent_command('agent-browser snapshot -i')
        if not result['success'] or 'textbox' not in result['stdout']:
            return "获取页面快照失败"
        
        # 步骤3: 填充搜索框
        # @e84 是搜索框的ref标识，从快照中获取
        result = run_agent_command(f'agent-browser fill @e84 "{movie_name}"')
        if not result['success']:
            return f"填充搜索框失败: {result['stderr'][:100]}"
        
        time.sleep(1)  # 等待输入完成
        
        # 步骤4: 点击"进入词条"按钮
        # @e71 是搜索按钮的ref标识
        result = run_agent_command('agent-browser click @e71')
        if not result['success']:
            return f"点击搜索按钮失败: {result['stderr'][:100]}"
        
        time.sleep(3)  # 等待搜索结果加载
        
        # 步骤5: 获取搜索结果页面的完整快照
        # snapshot 不带参数，获取完整页面内容（包括文本）
        result = run_agent_command('agent-browser snapshot')
        if not result['success']:
            return "获取结果页面快照失败"
        
        snapshot_text = result['stdout']
        movie_info = {}  # 存储提取的电影信息
        
        # 步骤6: 从快照文本中提取电影信息
        if 'heading' in snapshot_text:
            lines = snapshot_text.split('\n')
            
            # 提取电影名称：查找 heading "电影名" 格式
            for line in lines:
                if 'heading "' in line:
                    start = line.find('heading "') + 9
                    end = line.find('"', start)
                    if start > 8 and end > start:
                        movie_info['电影名称'] = line[start:end]
                        break
            
            # 提取基本信息：查找"XXXX年XX执导的动作电影"格式
            for i, line in enumerate(lines):
                if '年' in line and '执导' in line and '电影' in line:
                    movie_info['基本信息'] = line.strip()
                    break
            
            # 提取剧情简介：查找"《电影名》是由XX执导"开头的段落
            for i, line in enumerate(lines):
                if '《' in line and '》是由' in line and '执导' in line:
                    intro_lines = []
                    # 获取这一行及后续几行，直到遇到"..."结束标记
                    for j in range(i, min(i+5, len(lines))):
                        intro_lines.append(lines[j].strip())
                        if '...' in lines[j]:
                            break
                    movie_info['剧情简介'] = ' '.join(intro_lines)
                    break
            
            # 提取主要演员：查找"主要演员"区域下的演员名字
            actors = []
            actor_section = False  # 标记是否进入演员区域
            for line in lines:
                if '主要演员' in line:
                    actor_section = True
                    continue
                # 在演员区域内，查找 link "演员名" 格式
                if actor_section and 'link "' in line:
                    start = line.find('link "') + 6
                    end = line.find('"', start)
                    if start > 5 and end > start:
                        actor_name = line[start:end]
                        # 过滤：演员名长度在2-10个字符之间
                        if 2 <= len(actor_name) <= 10:
                            actors.append(actor_name)
                # 最多提取4个演员
                if actor_section and len(actors) >= 4:
                    break
            
            if actors:
                movie_info['主要演员'] = '、'.join(actors[:4])
        
        # 步骤7: 检查是否提取到信息
        if not movie_info:
            return f"未找到电影 '{movie_name}' 的相关信息"
        
        # 步骤8: 格式化返回结果
        # Agent会自动接收这个字符串，并整合到最终答案中
        result_text = f"从百度百科搜索到电影信息：\n"
        for key, value in movie_info.items():
            result_text += f"{key}：{value}\n"
        
        return result_text
        
    except Exception as e:
        return f"搜索过程出错: {str(e)}"
