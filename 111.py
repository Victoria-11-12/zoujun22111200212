#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国家名称转换模块
提供将中文国家名称转换为英文格式的功能
"""

def convert_country_to_english(country_str):
    """
    将中文国家名称转换为英文格式
    
    功能说明：
    1. 空值保持不变（None 或空字符串）
    2. 已经是英文的保持不变
    3. 包含逗号的分割处理（多个国家用逗号分隔）
    4. 使用映射表转换常见国家
    
    参数：
    country_str : str 或 None
        待转换的国家名称字符串，可以是中文、英文或包含逗号分隔的多个国家
        
    返回值：
    str 或 None
        转换后的英文国家名称字符串，如果输入为空则返回原值
        
    示例：
    >>> convert_country_to_english("中国大陆")
    'China'
    >>> convert_country_to_english("美国,日本")
    'USA,Japan'
    >>> convert_country_to_english("China")
    'China'
    >>> convert_country_to_english(None)
    None
    >>> convert_country_to_english("")
    ''
    """
    
    # 处理空值情况
    if country_str is None:
        return None
        
    # 转换为字符串类型，确保处理非字符串输入
    country_str = str(country_str)
    
    # 去除首尾空格
    country_str = country_str.strip()
    
    # 如果是空字符串，直接返回
    if country_str == '':
        return ''
    
    # 定义国家名称映射表（中文 -> 英文）
    country_mapping = {
        # 用户指定的映射
        "中国大陆": "China",
        "中国": "China",
        "美国": "USA",
        "日本": "Japan",
        "英国": "UK",
        "爱尔兰": "Ireland",
        "中国香港": "Hong Kong",
        "香港": "Hong Kong",
        "意大利": "Italy",
        "加拿大": "Canada",
        "法国": "France",
        "德国": "Germany",
        # 补充其他常见国家映射
        "澳大利亚": "Australia",
        "新西兰": "New Zealand",
        "韩国": "South Korea",
        "新加坡": "Singapore",
        "印度": "India",
        "俄罗斯": "Russia",
        "巴西": "Brazil",
        "墨西哥": "Mexico",
        "西班牙": "Spain",
        "葡萄牙": "Portugal",
        "荷兰": "Netherlands",
        "瑞士": "Switzerland",
        "瑞典": "Sweden",
        "挪威": "Norway",
        "丹麦": "Denmark",
        "芬兰": "Finland",
        "奥地利": "Austria",
        "比利时": "Belgium",
        "波兰": "Poland",
        "泰国": "Thailand",
        "越南": "Vietnam",
        "马来西亚": "Malaysia",
        "印度尼西亚": "Indonesia",
        "菲律宾": "Philippines",
        "沙特阿拉伯": "Saudi Arabia",
        "阿联酋": "United Arab Emirates",
        "土耳其": "Turkey",
        "埃及": "Egypt",
        "南非": "South Africa",
    }
    
    # 将中文逗号替换为英文逗号，统一分隔符
    country_str = country_str.replace('，', ',')
    
    # 检查是否包含逗号（多个国家）
    if ',' in country_str:
        # 分割字符串，处理每个部分
        parts = country_str.split(',')
        converted_parts = []
        
        for part in parts:
            part = part.strip()
            if part == '':
                # 空部分保留
                converted_parts.append('')
                continue
                
            # 检查是否为中文（在映射表中）
            if part in country_mapping:
                converted_parts.append(country_mapping[part])
            else:
                # 不在映射表中，假设已经是英文，原样保留
                converted_parts.append(part)
        
        # 用逗号重新连接
        return ','.join(converted_parts)
    
    # 单个国家处理
    # 检查是否在映射表中
    if country_str in country_mapping:
        return country_mapping[country_str]
    
    # 不在映射表中，假设已经是英文，原样返回
    return country_str


# 测试代码
if __name__ == "__main__":
    # 测试用例
    test_cases = [
        ("中国大陆", "China"),
        ("美国", "USA"),
        ("日本", "Japan"),
        ("英国", "UK"),
        ("爱尔兰", "Ireland"),
        ("中国香港", "Hong Kong"),
        ("意大利", "Italy"),
        ("加拿大", "Canada"),
        ("法国", "France"),
        ("德国", "Germany"),
        ("美国,日本", "USA,Japan"),
        ("美国，日本", "USA,Japan"),
        ("中国大陆,英国,加拿大", "China,UK,Canada"),
        ("China", "China"),
        ("USA", "USA"),
        ("Japan,UK", "Japan,UK"),
        ("", ""),
        (None, None),
        ("未知国家", "未知国家"),
        ("香港", "Hong Kong"),
        ("澳大利亚", "Australia"),
    ]
    
    print("开始测试 convert_country_to_english 函数：")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for input_val, expected in test_cases:
        # 处理 None 输入的特殊情况
        if input_val is None:
            result = convert_country_to_english(input_val)
            if result == expected:
                print(f"[PASS] 测试通过: {repr(input_val)} -> {repr(result)}")
                passed += 1
            else:
                print(f"[FAIL] 测试失败: {repr(input_val)} -> {repr(result)} (期望: {repr(expected)})")
                failed += 1
        else:
            result = convert_country_to_english(input_val)
            if result == expected:
                print(f"[PASS] 测试通过: {repr(input_val)} -> {repr(result)}")
                passed += 1
            else:
                print(f"[FAIL] 测试失败: {repr(input_val)} -> {repr(result)} (期望: {repr(expected)})")
                failed += 1
    
    print("=" * 50)
    print(f"测试结果: 通过 {passed} 个，失败 {failed} 个")
    
    if failed == 0:
        print("所有测试用例均通过！")
    else:
        print("存在测试失败的用例，请检查代码逻辑。")