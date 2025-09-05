#!/usr/bin/env python3
"""
使用示例
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from caddy_ssh_manager.api import (
    add_domain_to_caddy,
    batch_add_domains, 
    test_connection,
    get_caddy_config,
    get_system_info,
    quick_add_domain,
    quick_test_connection,
    setup_logging
)


def main():
    """主函数 - 演示各种功能"""
    setup_logging()
    
    print("=== Caddy SSH管理器示例 ===\n")
    
    # 1. 获取系统信息
    print("1. 系统信息:")
    info = get_system_info()
    print(f"   支持的品牌: {info['supported_brands']}")
    print(f"   SSH主机: {info['ssh_host']}")
    print(f"   SSH端口: {info['ssh_port']}")
    print(f"   SSH配置完整: {info['ssh_configured']}")
    print(f"   Caddy配置文件: {info['caddy_file_path']}")
    print()
    
    # 2. 测试连接
    print("2. 测试SSH连接:")
    conn_result = test_connection()
    print(f"   连接状态: {'正常' if conn_result['success'] else '失败'}")
    if conn_result.get('error'):
        print(f"   错误信息: {conn_result['error']}")
    print()
    
    if not conn_result['success']:
        print("SSH连接失败，无法继续演示其他功能")
        return
    
    # 3. 获取当前配置
    print("3. 获取当前Caddy配置:")
    config_result = get_caddy_config()
    if config_result['success']:
        config_lines = config_result['config'].split('\n')
        print(f"   配置文件行数: {len(config_lines)}")
        print("   前5行内容:")
        for i, line in enumerate(config_lines[:5]):
            print(f"     {i+1}: {line}")
    else:
        print(f"   获取配置失败: {config_result['error']}")
    print()
    
    # 4. 示例：为wujie品牌添加域名
    print("4. 示例：为wujie品牌添加域名")
    wujie_domain = "apiwj" + datetime.now().strftime("%m%d") + ".wj0001.cfd"
    
    print(f"   尝试添加域名: {wujie_domain} -> wujie")
    wujie_result = add_domain_to_caddy(wujie_domain, "wujie")
    
    print(f"   添加结果: {'成功' if wujie_result['success'] else '失败'}")
    if wujie_result['success']:
        print(f"   备份文件: {wujie_result.get('backup_path', '无')}")
        completed_steps = [k for k, v in wujie_result.get('steps_completed', {}).items() if v]
        print(f"   完成步骤: {', '.join(completed_steps)}")
    else:
        print(f"   错误信息: {wujie_result.get('error', '未知错误')}")
        completed_steps = [k for k, v in wujie_result.get('steps_completed', {}).items() if v]
        print(f"   已完成步骤: {', '.join(completed_steps)}")
    print()
    
    # 5. 示例：为v2word品牌添加域名
    print("5. 示例：为v2word品牌添加域名")
    v2word_domain = "apiv2" + datetime.now().strftime("%m%d") + ".v20000.cfd"
    
    print(f"   尝试添加域名: {v2word_domain} -> v2word")
    v2word_result = add_domain_to_caddy(v2word_domain, "v2word")
    
    print(f"   添加结果: {'成功' if v2word_result['success'] else '失败'}")
    if v2word_result['success']:
        print(f"   备份文件: {v2word_result.get('backup_path', '无')}")
        completed_steps = [k for k, v in v2word_result.get('steps_completed', {}).items() if v]
        print(f"   完成步骤: {', '.join(completed_steps)}")
    else:
        print(f"   错误信息: {v2word_result.get('error', '未知错误')}")
        completed_steps = [k for k, v in v2word_result.get('steps_completed', {}).items() if v]
        print(f"   已完成步骤: {', '.join(completed_steps)}")
    print()
    
    # 6. 简化接口示例
    print("6. 简化接口示例:")
    print("   快速连接测试:", "成功" if quick_test_connection() else "失败")
    print()
    
    print("=== 演示完成 ===")


if __name__ == "__main__":
    main()