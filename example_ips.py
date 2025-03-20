#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生成一个示例IP地址Excel文件，用于测试IP地址归属地识别工具
"""

import pandas as pd
import random

# 示例IPv4地址列表（全球知名网站和服务的IP地址）
ipv4_examples = [
    "8.8.8.8",           # Google DNS
    "8.8.4.4",           # Google DNS
    "1.1.1.1",           # Cloudflare DNS
    "208.67.222.222",    # OpenDNS
    "91.198.174.192",    # Wikipedia
    "172.217.21.142",    # Google
    "31.13.72.36",       # Facebook
    "104.244.42.193",    # Twitter
    "13.107.42.16",      # Microsoft
    "151.101.1.140",     # Reddit
]

# 示例IPv6地址列表
ipv6_examples = [
    "2001:4860:4860::8888",      # Google DNS
    "2001:4860:4860::8844",      # Google DNS
    "2606:4700:4700::1111",      # Cloudflare DNS
    "2620:0:2d0:200::7",         # Wikipedia
    "2a03:2880:f131:83:face:b00c:0:25de", # Facebook
    "2400:cb00:2048:1::c629:d7a2", # Fastly CDN
    "2a00:1450:4001:814::200e",   # Google
    "2606:2800:220:1:248:1893:25c8:1946", # Akamai
    "2620:1ec:8fc::1",           # Microsoft
    "2001:67c:2564:a102::5",     # GitHub
]

def create_example_excel(output_path="example_ips.xlsx"):
    """创建一个包含示例IP地址的Excel文件

    Args:
        output_path (str, optional): 输出Excel文件路径. 默认为 "example_ips.xlsx".
    """
    # 创建数据
    data = []
    
    # 添加IPv4地址
    for i, ip in enumerate(ipv4_examples, 1):
        data.append([i, ip])
    
    # 添加IPv6地址
    for i, ip in enumerate(ipv6_examples, len(ipv4_examples) + 1):
        data.append([i, ip])
    
    # 创建DataFrame
    df = pd.DataFrame(data, columns=["序号", "IP地址"])
    
    # 保存到Excel文件
    df.to_excel(output_path, index=False)
    print(f"示例IP地址Excel文件已创建: {output_path}")


if __name__ == "__main__":
    create_example_excel() 