
import pandas as pd
from aliyun_boce import scrape_aliyun_boce, clean_url

def analyze_domain_availability(df):
    """
    分析域名可用性
    
    :param df: 拨测结果数据DataFrame
    :return: 分析结果字典
    """
    try:
        # 确认DataFrame列名
        print("DataFrame列名:", df.columns.tolist())
        
        # 将Status列转换为整数类型 (可能是字符串)
        df['Status'] = pd.to_numeric(df['Status'], errors='coerce')
        
        # 1. 计算基本统计信息
        total_checks = len(df)
        # 状态码200表示成功，不是失败！
        success_checks = len(df[df['Status'] == 200])
        success_rate = (success_checks / total_checks) * 100 if total_checks > 0 else 0
        
        # 2. 计算响应时间统计
        # 处理响应时间，将'-'替换为NaN，将'ms'去掉，然后转为数值
        df['Response_Time_ms'] = df['Total Response Time'].str.replace('ms', '')
        # 将'-'或空字符串替换为NaN
        df['Response_Time_ms'] = df['Response_Time_ms'].replace(['-', ''], float('nan'))
        # 转换为数值类型
        df['Response_Time_ms'] = pd.to_numeric(df['Response_Time_ms'], errors='coerce')
        
        # 计算平均、最大、最小响应时间 - 状态码200表示成功！
        avg_response_time = df[df['Status'] == 200]['Response_Time_ms'].mean() if success_checks > 0 else float('nan')
        max_response_time = df[df['Status'] == 200]['Response_Time_ms'].max() if success_checks > 0 else float('nan')
        min_response_time = df[df['Status'] == 200]['Response_Time_ms'].min() if success_checks > 0 else float('nan')
        
        # 查找最高延迟的地区 - 更安全的方式，注意状态码200是成功！
        max_latency_area = "N/A"
        max_latency_value = float('nan')
        min_latency_area = "N/A"
        min_latency_value = float('nan')
        
        if success_checks > 0:
            # 只筛选成功的行并且Response_Time_ms不是NaN的行
            success_df = df[(df['Status'] == 200) & df['Response_Time_ms'].notna()].copy()
            
            if not success_df.empty:
                # 对筛选后的DataFrame进行排序，获取最高和最低值
                max_row = success_df.sort_values('Response_Time_ms', ascending=False).iloc[0]
                min_row = success_df.sort_values('Response_Time_ms', ascending=True).iloc[0]
                
                max_latency_area = max_row['Detection Point']
                max_latency_value = max_row['Response_Time_ms']
                min_latency_area = min_row['Detection Point']
                min_latency_value = min_row['Response_Time_ms']
        
        # 3. 分析错误状态码分布 - 非200的状态码才是错误
        error_status_counts = df[df['Status'] != 200]['Status'].value_counts().to_dict()
        
        # 4. 分析不可用地区 - 非200的状态码才表示不可用
        unavailable_areas = df[df['Status'] != 200][['Detection Point', 'Status']].values.tolist()
        
        # 5. 按运营商分组分析
        # 提取运营商信息
        df['ISP'] = df['Detection Point'].str.extract(r'China-(Mobile|Telecom|Unicom)')
        isp_analysis = {}
        
        for isp in df['ISP'].dropna().unique():
            isp_df = df[df['ISP'] == isp]
            isp_total = len(isp_df)
            # 状态码200表示成功！
            isp_success = len(isp_df[isp_df['Status'] == 200])
            isp_success_rate = (isp_success / isp_total) * 100 if isp_total > 0 else 0
            
            isp_analysis[isp] = {
                'total_checks': isp_total,
                'success_checks': isp_success,
                'success_rate': isp_success_rate
            }
        
        # 6. 判断整体可用性
        # 假设：如果成功率 >= 80%，我们认为域名可用
        is_available = success_rate >= 80
        
        # 7. 汇总结果
        analysis_result = {
            'total_checks': total_checks,
            'success_checks': success_checks,
            'success_rate': success_rate,
            'average_response_time_ms': avg_response_time,
            'max_response_time_ms': max_response_time,
            'min_response_time_ms': min_response_time,
            'max_latency_area': max_latency_area,
            'max_latency_value': max_latency_value,
            'min_latency_area': min_latency_area,
            'min_latency_value': min_latency_value,
            'error_status_distribution': error_status_counts,
            'unavailable_areas': unavailable_areas,
            'isp_analysis': isp_analysis,
            'is_available': is_available
        }
        
        return analysis_result
        
    except Exception as e:
        print(f"分析域名可用性时出错: {e}")
        import traceback
        traceback.print_exc()
        return None
    


def run_boce(url_to_check):
    """
    执行完整的拨测流程：执行拨测、等待下载、解析文件
    
    :param url_to_check: 待检测的URL
    :return: 解析后的数据或None（如果任何步骤失败）
    """
    # 清理URL
    cleaned_url = clean_url(url_to_check)
    print(f"\n开始检测网址: {cleaned_url}")
    
    # 执行拨测并直接获取数据
    result_data = scrape_aliyun_boce(cleaned_url)
    
    # 检查result_data是否为DataFrame类型并且不为空
    if result_data is None or (hasattr(result_data, 'empty') and result_data.empty):
        print("拨测失败，无法获取数据")
        return None
    
    # 分析域名可用性
    analysis_result = analyze_domain_availability(result_data)
    if analysis_result is None:
        print("分析域名可用性失败")
        return None
    
    # 4. 分析域名可用性
    analysis_result = analyze_domain_availability(result_data)
    if analysis_result is None:
        print("分析域名可用性失败")
        return None
    print("\n域名可用性分析完成")
    print(f"检测总数: {analysis_result['total_checks']}")
    print(f"成功数量: {analysis_result['success_checks']}")
    print(f"成功率: {analysis_result['success_rate']:.2f}%")
    print(f"平均响应时间: {analysis_result['average_response_time_ms']:.2f}ms")
    print(f"最高延迟地区: {analysis_result['max_latency_area']} ({analysis_result['max_latency_value']}ms)")
    print(f"最低延迟地区: {analysis_result['min_latency_area']} ({analysis_result['min_latency_value']}ms)")
    print(f"域名是否可用: {'是' if analysis_result['is_available'] else '否'}")
    
    # 显示不可用地区
    if analysis_result['unavailable_areas']:
        print("\n不可用地区列表:")
        for area, status in analysis_result['unavailable_areas']:
            print(f"  - {area}: 状态码 {status}")
    

    return analysis_result
