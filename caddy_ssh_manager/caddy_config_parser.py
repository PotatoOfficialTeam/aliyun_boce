#!/usr/bin/env python3
"""
Caddy配置文件解析器
专门处理域名添加逻辑
"""

import re
from typing import Dict, List, Optional, Tuple


class CaddyConfigParser:
    """Caddy配置解析器"""
    
    def __init__(self, config_content: str):
        """
        初始化解析器
        
        Args:
            config_content: Caddy配置文件内容
        """
        self.original_content = config_content
        self.lines = config_content.split('\n')
        
        # 品牌配置
        self.brand_configs = {
            "wujie": {
                "target_host": "wujie.one"
            },
            "v2word": {
                "target_host": "v2word.art"
            }
        }
    
    def find_brand_block_by_target_host(self, brand: str) -> Optional[Dict]:
        """
        通过目标主机查找品牌对应的配置块
        
        Args:
            brand: 品牌名称
            
        Returns:
            配置块信息字典，包含start_line, end_line, domain_line_index
        """
        brand_config = self.brand_configs.get(brand.lower())
        if not brand_config:
            return None
        
        target_host = brand_config["target_host"]
        
        # 查找包含目标主机的reverse_proxy配置块
        for i, line in enumerate(self.lines):
            stripped_line = line.strip()
            
            # 如果找到包含目标主机的reverse_proxy行
            if f"reverse_proxy https://{target_host}" in stripped_line:
                
                # 从这行开始向上查找配置块的开始（包含域名的行）
                domain_line_index = -1
                block_start = -1
                
                for j in range(i, -1, -1):
                    check_line = self.lines[j].strip()
                    # 查找以域名开头且以{结尾的行，排除特殊配置行
                    if ('{' in check_line and 
                        not check_line.startswith(('@', 'handle', 'log', 'encode', 'reverse_proxy', '#')) and
                        not check_line.strip() == '{'):
                        # 找到了域名行
                        domain_line_index = j
                        block_start = j
                        break
                
                if domain_line_index == -1:
                    continue
                
                # 从域名行开始向下查找配置块结束
                brace_count = self.lines[domain_line_index].count('{') - self.lines[domain_line_index].count('}')
                block_end = -1
                
                for k in range(domain_line_index + 1, len(self.lines)):
                    brace_count += self.lines[k].count('{') - self.lines[k].count('}')
                    if brace_count == 0:
                        block_end = k
                        break
                
                if block_end != -1:
                    return {
                        'start_line': block_start,
                        'end_line': block_end,
                        'domain_line_index': domain_line_index,
                        'target_host': target_host,
                        'content': '\n'.join(self.lines[block_start:block_end + 1])
                    }
        
        return None
    
    def add_domain_to_brand_block(self, domain: str, brand: str) -> Tuple[bool, str]:
        """
        为品牌配置块添加域名
        
        Args:
            domain: 要添加的域名
            brand: 品牌名称
            
        Returns:
            Tuple[success, new_config_or_error_message]
        """
        # 查找品牌对应的配置块
        block_info = self.find_brand_block_by_target_host(brand)
        if not block_info:
            return False, f"未找到品牌 {brand} 的配置块"
        
        domain_line_index = block_info['domain_line_index']
        current_domain_line = self.lines[domain_line_index]
        
        # 检查域名是否已存在
        if domain in current_domain_line:
            return True, f"域名 {domain} 已存在"
        
        # 解析当前域名行
        # 格式应该是: "domain1 domain2 domain3 {"
        line_parts = current_domain_line.split('{')
        if len(line_parts) != 2:
            return False, f"域名行格式错误: {current_domain_line}"
        
        domains_part = line_parts[0].strip()
        brace_part = '{'
        
        # 在域名列表前面添加新域名
        new_domains_part = f"{domain} {domains_part}"
        new_domain_line = f"{new_domains_part} {brace_part}"
        
        # 创建新的配置内容
        new_lines = self.lines.copy()
        new_lines[domain_line_index] = new_domain_line
        
        new_config = '\n'.join(new_lines)
        return True, new_config
    
    def get_brand_domains(self, brand: str) -> List[str]:
        """
        获取品牌当前的域名列表
        
        Args:
            brand: 品牌名称
            
        Returns:
            域名列表
        """
        block_info = self.find_brand_block_by_target_host(brand)
        if not block_info:
            return []
        
        domain_line_index = block_info['domain_line_index']
        domain_line = self.lines[domain_line_index]
        
        # 提取域名部分
        line_parts = domain_line.split('{')
        if len(line_parts) != 2:
            return []
        
        domains_part = line_parts[0].strip()
        domains = [d.strip() for d in domains_part.split() if d.strip()]
        
        return domains
    
    def validate_config_syntax(self) -> Tuple[bool, str]:
        """
        验证配置文件语法（简单检查）
        
        Returns:
            Tuple[is_valid, error_message]
        """
        # 检查大括号是否平衡
        brace_count = 0
        for i, line in enumerate(self.lines):
            brace_count += line.count('{') - line.count('}')
            if brace_count < 0:
                return False, f"第{i+1}行大括号不匹配: {line}"
        
        if brace_count != 0:
            return False, f"大括号总数不匹配，差值: {brace_count}"
        
        return True, "语法检查通过"


def test_parser():
    """测试解析器功能"""
    
    # 读取本地配置文件进行测试
    config_path = "/home/xxxx/projects/PythonProjects/aliyun_boce/caddy_ssh_manager/Caddyfile"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        parser = CaddyConfigParser(config_content)
        
        print("=== 测试Caddy配置解析器 ===")
        
        # 测试查找品牌配置块
        print("\n1. 查找wujie品牌配置块:")
        wujie_block = parser.find_brand_block_by_target_host("wujie")
        if wujie_block:
            print(f"   找到配置块: 行{wujie_block['start_line']+1}-{wujie_block['end_line']+1}")
            print(f"   域名行: {wujie_block['domain_line_index']+1}")
            print(f"   目标主机: {wujie_block['target_host']}")
            
            # 获取当前域名
            domains = parser.get_brand_domains("wujie")
            print(f"   当前域名: {domains}")
        else:
            print("   未找到配置块")
        
        print("\n2. 查找v2word品牌配置块:")
        v2word_block = parser.find_brand_block_by_target_host("v2word")
        if v2word_block:
            print(f"   找到配置块: 行{v2word_block['start_line']+1}-{v2word_block['end_line']+1}")
            print(f"   域名行: {v2word_block['domain_line_index']+1}")
            print(f"   目标主机: {v2word_block['target_host']}")
            
            # 获取当前域名
            domains = parser.get_brand_domains("v2word")
            print(f"   当前域名: {domains}")
        else:
            print("   未找到配置块")
        
        # 测试添加域名
        print("\n3. 测试添加域名到wujie:")
        success, result = parser.add_domain_to_brand_block("newapi.test.com", "wujie")
        print(f"   添加结果: {'成功' if success else '失败'}")
        if success:
            print("   新配置生成成功（未保存）")
            # 验证语法
            new_parser = CaddyConfigParser(result)
            valid, msg = new_parser.validate_config_syntax()
            print(f"   语法验证: {'通过' if valid else '失败'} - {msg}")
        else:
            print(f"   错误: {result}")
        
        print("\n4. 原始配置语法验证:")
        valid, msg = parser.validate_config_syntax()
        print(f"   结果: {'通过' if valid else '失败'} - {msg}")
        
    except FileNotFoundError:
        print(f"配置文件不存在: {config_path}")
    except Exception as e:
        print(f"测试出错: {e}")


if __name__ == "__main__":
    test_parser()