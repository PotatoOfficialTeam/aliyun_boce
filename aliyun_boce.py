from DrissionPage import ChromiumPage, ChromiumOptions
import time
import os

def ensure_screenshot_dir():
    """确保截图保存目录存在"""
    screenshot_dir = "screenshots"
    # if not os.path.exists(screenshot_dir):
    #     os.makedirs(screenshot_dir)
    return screenshot_dir

def take_screenshot(page, name_prefix):
    """获取页面截图并保存"""
    try:
        screenshot_dir = ensure_screenshot_dir()
        # timestamp = time.strftime('%Y%m%d_%H%M%S')
        # screenshot_path = os.path.join(screenshot_dir, f"{name_prefix}_{timestamp}.png")
        # page.get_screenshot(screenshot_path)
        # print(f"截图已保存至: {screenshot_path}")
        return screenshot_dir
    except Exception as e:
        print(f"保存截图失败: {e}")
        return None
    
def open_boce_website(page):
    """打开阿里云拨测网站"""
    try:
        print("正在导航至阿里云拨测网站...")
        page.get('https://boce.aliyun.com/detect/http')
        take_screenshot(page, "initial_page")
        time.sleep(5)  # 等待页面加载
        take_screenshot(page, "after_wait")
        return True
    except Exception as e:
        print(f"打开网站失败: {e}")
        take_screenshot(page, "open_website_failed")
        return False

def find_input_field(page):
    """找到并返回URL输入框元素"""
    # 主选择器
    url_input_locator = "xpath://input[contains(@placeholder, 'Please enter')]"
    
    # 备选选择器
    alternative_selectors = [
        "css:input[placeholder*='Please enter']",
        "css:input[type='text']",
        "xpath://input[@type='text']",
        "xpath://div[contains(@class, 'search')]//input",
        "xpath://div[contains(@class, 'input')]//input"
    ]
    
    # 尝试主选择器
    try:
        page.wait.ele_displayed(url_input_locator, timeout=10)
        url_input_element = page.ele(url_input_locator)
        print("成功找到输入框，使用选择器:", url_input_locator)
        return url_input_element
    except Exception as e:
        print(f"使用主选择器 {url_input_locator} 查找输入框失败: {e}")
        take_screenshot(page, "main_selector_failed")
    
    # 尝试备选选择器
    for selector in alternative_selectors:
        try:
            page.wait.ele_displayed(selector, timeout=5)
            url_input_element = page.ele(selector)
            print(f"成功找到输入框，使用替代选择器: {selector}")
            return url_input_element
        except:
            continue
    
    # 如果都失败，打印页面HTML片段并返回None
    print("无法找到URL输入框，输出当前页面HTML片段:")
    print(page.html[:1000])
    take_screenshot(page, "no_input_found")
    return None

def input_url(page, input_element, url):
    """在输入框中输入URL"""
    try:
        input_element.input(url)
        print(f"已输入网址: {url}")
        take_screenshot(page, "after_input_url")
        return True
    except Exception as e:
        print(f"输入URL失败: {e}")
        take_screenshot(page, "input_url_failed")
        return False

def click_ok_button(page):
    """点击OK按钮开始拨测"""
    # 根据日志，保留有效的选择器，移除无效的
    ok_button_selectors = [
        "xpath://button[.//span[text()='OK']]",  # 这个选择器有效
        "css:.ant-btn-primary",  # Ant Design的主按钮，可能有效
        "xpath://button[contains(text(), 'OK')]",  # 可能有效
        "css:button[type='submit']"  # 可能有效
    ]
    
    # 尝试点击按钮
    for selector in ok_button_selectors:
        try:
            ok_button = page.ele(selector)
            if ok_button:
                take_screenshot(page, f"before_click_button_{selector.replace(':', '_')}")
                ok_button.click()
                print(f"已点击OK按钮，使用选择器: {selector}")
                take_screenshot(page, f"after_click_button_{selector.replace(':', '_')}")
                return True
        except Exception as e:
            print(f"尝试点击按钮失败，选择器: {selector}, 错误: {e}")
            continue
    
    # 备用方案: 尝试使用更通用的方法找到按钮
    try:
        # 查找带有箭头图标的按钮（根据截图观察）
        arrow_button = page.ele("xpath://button[.//span[contains(@class, 'arrow') or contains(@class, 'icon')]]")
        if arrow_button:
            take_screenshot(page, "before_click_arrow_button")
            arrow_button.click()
            print("已点击带箭头的按钮")
            take_screenshot(page, "after_click_arrow_button")
            return True
    except Exception as e:
        print(f"尝试点击带箭头的按钮失败: {e}")
    
    # 尝试按Enter键
    try:
        # 找到输入框再按Enter
        input_element = find_input_field(page)
        if input_element:
            input_element.click()
            page.keyboard.press_key(13)  # 13是Enter键的键码
            print("尝试通过按Enter键提交")
            take_screenshot(page, "after_press_enter")
            return True
    except Exception as e:
        print(f"尝试按Enter键失败: {e}")
    
    take_screenshot(page, "all_button_attempts_failed")
    return False


def wait_for_export_button_clickable(page, max_wait_time=180):
    """等待Export Report按钮出现并且变为可点击状态"""
    print("等待Export Report按钮出现并变为可点击状态...")
    
    wait_interval = 5  # 每5秒检查一次
    start_time = time.time()
    export_button = None
    
    while time.time() - start_time < max_wait_time:
        elapsed_time = int(time.time() - start_time)
        screenshot_path = take_screenshot(page, f"waiting_export_button_{elapsed_time}")
        print(f"已等待{elapsed_time}秒，查找并检查Export Report按钮状态...")
        
        # 打印所有按钮的文本，帮助调试
        all_buttons = []
        try:
            all_buttons = page.eles("tag:button")
            print(f"找到 {len(all_buttons)} 个按钮:")
            for i, btn in enumerate(all_buttons):
                try:
                    btn_text = btn.text
                    disabled = False
                    try:
                        # 尝试检查按钮是否被禁用
                        cls = btn.attr('class')
                        disabled = 'disabled' in cls or 'ant-btn-disabled' in cls
                    except:
                        pass
                except:
                    print(f"  按钮 {i+1} 无法获取文本")
        except Exception as e:
            print(f"获取按钮列表失败: {e}")
        
        # 查找Export Report按钮
        export_button = None
        for btn in all_buttons:
            try:
                btn_text = btn.text
                if btn_text and ("Export" in btn_text or "Report" in btn_text):
                    export_button = btn
                    print(f"找到Export Report按钮，文本: '{btn_text}'")
                    
                    # 检查按钮是否可点击
                    try:
                        cls = btn.attr('class')
                        is_disabled = 'disabled' in cls or 'ant-btn-disabled' in cls
                        
                        if is_disabled:
                            print("Export Report按钮当前处于禁用状态，继续等待...")
                            export_button = None  # 设为None表示我们需要继续等待
                        else:
                            # 使用JavaScript进一步检查按钮是否可点击
                            js_check = page.run_js("""
                                var btn = arguments[0];
                                // 检查按钮是否可见且可点击
                                var rect = btn.getBoundingClientRect();
                                var isVisible = rect.width > 0 && rect.height > 0;
                                var isDisabled = btn.disabled || btn.getAttribute('aria-disabled') === 'true' || 
                                                btn.classList.contains('disabled') || 
                                                btn.classList.contains('ant-btn-disabled');
                                var isClickable = isVisible && !isDisabled;
                                
                                // 额外检查按钮的透明度和指针事件
                                var style = window.getComputedStyle(btn);
                                var isInteractive = style.pointerEvents !== 'none' && 
                                                  parseFloat(style.opacity) > 0.5;
                                
                                return {
                                    isVisible: isVisible,
                                    isDisabled: isDisabled,
                                    isClickable: isClickable,
                                    isInteractive: isInteractive,
                                    className: btn.className,
                                    opacity: style.opacity,
                                    pointerEvents: style.pointerEvents
                                };
                            """, btn)
                            
                            print(f"按钮状态检查结果: {js_check}")
                            
                            if js_check and js_check.get('isClickable') and js_check.get('isInteractive'):
                                print("Export Report按钮现在可点击!")
                                return btn  # 按钮可点击，立即返回
                            else:
                                print("Export Report按钮找到但尚不可点击，继续等待...")
                                export_button = None  # 设为None表示我们需要继续等待
                    except Exception as e:
                        print(f"检查按钮状态失败: {e}")
                        export_button = None  # 出错时设为None继续等待
                    
                    break  # 只检查第一个找到的Export Report按钮
            except:
                continue
        
        # 如果找到了可点击的按钮，则已在上面的检查中返回
        # 如果没找到，则等待后再次检查
        time.sleep(wait_interval)
    
    print(f"等待Export Report按钮可点击超时，已等待{max_wait_time}秒")
    take_screenshot(page, "export_button_timeout")
    
    # 超时后最后一次尝试查找按钮（不强制启用）
    for btn in all_buttons:
        try:
            btn_text = btn.text
            if btn_text and ("Export" in btn_text or "Report" in btn_text):
                print(f"最后找到的Export Report按钮: '{btn_text}'，但可能不可点击")
                return btn
        except:
            continue
    
    return None

def extract_table_data_from_page(page):
    """直接从网页中提取表格数据而不是下载Excel文件"""
    print("开始从网页直接提取表格数据...")
    take_screenshot(page, "before_extract_table")
    
    try:
        # 使用JavaScript提取表格数据
        table_data = page.run_js("""
            // 定义映射关系，将表格列名映射到Excel文件中的列名
            const columnMapping = {
                '探测点': 'Detection Point',
                '解析结果IP': 'Analysis Result IP',
                '状态': 'Status',
                '总响应时间': 'Total Response Time',
                '解析时间': 'Analysis Time',
                '建连时间': 'Connection Time',
                'SSL时间': 'SSL Time',
                '首包时间': 'First Packet Time',
                '下载时间': 'Download Time'
                // 可能需要根据实际情况添加更多映射
            };
            
            // 获取表格所有行
            const tableRows = Array.from(document.querySelectorAll('table tr, .ant-table-row, [role="row"]'));
            if (!tableRows || tableRows.length <= 1) {
                // 使用备用选择器尝试
                const altRows = Array.from(document.querySelectorAll('.ant-table-tbody tr, div[role="rowgroup"] > div'));
                if (altRows.length > 0) {
                    tableRows.push(...altRows);
                } else {
                    return { error: "找不到表格行" };
                }
            }
            
            // 尝试查找表头
            let headerCells = document.querySelectorAll('th, .ant-table-cell, [role="columnheader"]');
            if (!headerCells || headerCells.length === 0) {
                // 查找表头失败，尝试使用第一行作为表头
                if (tableRows.length > 0) {
                    headerCells = tableRows[0].querySelectorAll('td, th, .ant-table-cell');
                    tableRows.shift(); // 移除第一行，因为它被当作表头
                }
            }
            
            // 提取表头文本
            const headers = Array.from(headerCells).map(cell => {
                const text = cell.innerText.trim();
                // 使用映射转换列名
                return columnMapping[text] || text;
            });
            
            // 提取数据行
            const rowsData = [];
            for (const row of tableRows) {
                const cells = row.querySelectorAll('td, .ant-table-cell, [role="cell"]');
                if (cells && cells.length > 0) {
                    rowsData.push(Array.from(cells).map(cell => cell.innerText.trim()));
                }
            }
            
            // 打印一些调试信息
            console.log(`找到 ${headers.length} 列表头和 ${rowsData.length} 行数据`);
            
            return {
                headers: headers, 
                rows: rowsData
            };
        """);
        
        
        if not table_data or 'error' in table_data:
            print(f"提取表格数据失败: {table_data.get('error', '未知错误')}")
            # 尝试打印页面HTML帮助调试
            html_snippet = page.html[:2000]  # 获取页面前2000个字符
            print(f"页面HTML片段: {html_snippet}")
            return None
        
        # 将提取的数据转换为DataFrame
        import pandas as pd
        
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        
        if not headers or not rows:
            print("提取的表格没有表头或数据行")
            return None
        
        # 处理列数不匹配的情况
        max_cols = max(len(headers), max(len(row) for row in rows))
        if len(headers) < max_cols:
            headers.extend([f'未命名列{i}' for i in range(len(headers), max_cols)])
        
        # 确保所有行有相同的列数
        for i, row in enumerate(rows):
            if len(row) < max_cols:
                rows[i] = row + [''] * (max_cols - len(row))
            elif len(row) > max_cols:
                rows[i] = row[:max_cols]
        
        # 创建DataFrame
        df = pd.DataFrame(rows, columns=headers)
        print(f"成功创建DataFrame，包含{len(df)}行和以下列:")
        print(df.columns.tolist())
        print("\n数据预览:")
        print(df.head())
        
        return df
    
    except Exception as e:
        print(f"从网页提取表格数据时出错: {e}")
        take_screenshot(page, "extract_table_error")
        return None
    
def scrape_aliyun_boce(target_url: str):
    """
    使用DrissionPage访问阿里云网站拨测工具并抓取HTTP检测结果。
    
    :param target_url: 需要检测的网址
    :return: 提取的数据DataFrame或None
    """
    
    # 创建ChromiumOptions对象并配置参数
    options = ChromiumOptions()
    options.headless = True  # 设置为无头模式
    options.set_argument('--no-sandbox')
    options.set_argument('--disable-dev-shm-usage')
    options.set_argument('--headless=new')
    options.set_argument('--window-size=1920,1080')  # 设置较高的分辨率
    
    # 创建ChromiumPage对象
    page = ChromiumPage(options)
    
    try:
        # 1. 打开阿里云拨测网站
        if not open_boce_website(page):
            return False
        
        # 2. 查找输入框
        url_input_element = find_input_field(page)
        if not url_input_element:
            raise Exception("无法找到URL输入框")
        
        # 3. 输入URL
        if not input_url(page, url_input_element, target_url):
            raise Exception("输入URL失败")
        
        # 4. 点击OK按钮
        if not click_ok_button(page):
            raise Exception("无法点击OK按钮")
        
        # 5. 等待Export Report按钮出现并变为可点击
        # 这一步保留，用于判断页面是否完全加载
        export_button = wait_for_export_button_clickable(page)
        
        if not export_button:
            print("未找到可点击的Export Report按钮，无法确认页面加载完成")
            take_screenshot(page, "no_clickable_export_button")
            return None
            
        print("Export Report按钮已变为可点击状态，页面已完全加载")
        take_screenshot(page, "page_fully_loaded")
        
        # 6. 不点击Export按钮，直接从网页提取表格数据
        df = extract_table_data_from_page(page)
        if df is not None:
            print("成功从网页提取表格数据")
            return df
        else:
            print("从网页提取表格数据失败")
            return None
    
    except Exception as e:
        print(f"在爬虫执行过程中发生意外错误: {e}")
        take_screenshot(page, "critical_error")
        return None
    
    finally:
        # 最终截图，无论成功还是失败
        take_screenshot(page, "final_state")
        
        # 确保关闭页面
        try:
            page.quit()
        except Exception as e:
            print(f"关闭页面失败: {e}")

def clean_url(url):
    """清理URL，去除http://或https://前缀"""
    if '://' in url:
        return url.split('://', 1)[-1]
    return url