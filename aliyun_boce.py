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
        # screenshot_dir = ensure_screenshot_dir()
        # timestamp = time.strftime('%Y%m%d_%H%M%S')
        # screenshot_path = os.path.join(screenshot_dir, f"{name_prefix}_{timestamp}.png")
        # page.get_screenshot(screenshot_path)
        # print(f"截图已保存至: {screenshot_path}")
        # return 
        return ''
    except Exception as e:
        print(f"保存截图失败: {e}")
        return None
def export_report_with_js(page):
    """使用JavaScript点击Export Report按钮"""
    try:
        print("尝试使用JavaScript点击Export Report按钮...")
        result = page.run_js("""
            var buttons = document.querySelectorAll('button');
            for(var i=0; i<buttons.length; i++) {
                if(buttons[i].innerText.indexOf('Export') !== -1 || buttons[i].innerText.indexOf('Report') !== -1) {
                    buttons[i].click();
                    return true;
                }
            }
            return false;
        """)
        print(f"JavaScript执行结果: {result}")
        time.sleep(3)  # 等待可能的对话框
        take_screenshot(page, "after_js_click_export")
        return result
    except Exception as e:
        print(f"使用JavaScript点击Export Report按钮失败: {e}")
        return False
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

def click_export_button(page, export_button):
    """点击Export Report按钮导出报告"""
    try:
        take_screenshot(page, "before_export_report")
        export_button.click()
        print("已点击Export Report按钮")
        time.sleep(3)  # 等待导出对话框出现
        take_screenshot(page, "after_export_report")
        return True
    except Exception as e:
        print(f"尝试点击Export Report按钮失败: {e}")
        take_screenshot(page, "export_button_click_failed")
        
        # 尝试使用JavaScript点击
        return export_report_with_js(page)

def click_export_button_with_multiple_attempts(page, button):
    """尝试多种方法点击Export Report按钮"""
    if not button:
        print("Export Report按钮不存在，无法点击")
        return False
    
    # 1. 尝试直接点击
    try:
        take_screenshot(page, "before_direct_click_export")
        button.click()
        print("已直接点击Export Report按钮")
        take_screenshot(page, "after_direct_click_export")
        time.sleep(2)  # 等待可能的下载对话框
        return True
    except Exception as e:
        print(f"直接点击Export Report按钮失败: {e}")
    
    # 2. 尝试先右键点击再左键点击
    try:
        take_screenshot(page, "before_right_click_export")
        button.right_click()
        time.sleep(1)
        button.click()
        print("已通过右键后左键方式点击Export Report按钮")
        take_screenshot(page, "after_right_click_export")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"右键后左键点击Export Report按钮失败: {e}")
    
    # 3. 尝试使用JavaScript点击
    try:
        # 先给按钮添加唯一ID
        page.run_js("""
            arguments[0].id = 'export-report-button';
        """, button)
        
        take_screenshot(page, "before_js_click_export")
        js_result = page.run_js("""
            var btn = document.getElementById('export-report-button');
            if (btn) {
                btn.click();
                return true;
            }
            return false;
        """)
        
        print(f"JavaScript点击Export Report按钮结果: {js_result}")
        take_screenshot(page, "after_js_click_export")
        time.sleep(2)
        
        if js_result:
            return True
    except Exception as e:
        print(f"使用JavaScript点击Export Report按钮失败: {e}")
    
    # 4. 尝试使用键盘快捷键Ctrl+E (假设可能有这样的快捷键)
    try:
        take_screenshot(page, "before_hotkey_export")
        page.keyboard.press_key(['ctrl', 'e'])
        print("已尝试使用Ctrl+E快捷键导出")
        take_screenshot(page, "after_hotkey_export")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"使用快捷键导出失败: {e}")
    
    return False

def wait_for_export_button_clickable(page, max_wait_time=180):
    """等待Export Report按钮出现并且变为可点击状态"""
    print("等待Export Report按钮出现并变为可点击状态...")
    
    wait_interval = 120  # 每5秒检查一次
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
                    
                    print(f"  按钮 {i+1} 文本: '{btn_text}', 禁用状态: {disabled}")
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

def click_export_button(page, button):
    """尝试点击Export Report按钮，只在按钮可点击时点击"""
    if not button:
        print("Export Report按钮不存在，无法点击")
        return False
    
    # 先检查按钮是否可点击
    is_clickable = False
    try:
        js_check = page.run_js("""
            var btn = arguments[0];
            var isDisabled = btn.disabled || btn.getAttribute('aria-disabled') === 'true' || 
                             btn.classList.contains('disabled') || 
                             btn.classList.contains('ant-btn-disabled');
            var rect = btn.getBoundingClientRect();
            var isVisible = rect.width > 0 && rect.height > 0;
            var style = window.getComputedStyle(btn);
            var isInteractive = style.pointerEvents !== 'none' && parseFloat(style.opacity) > 0.5;
            
            return {
                isClickable: !isDisabled && isVisible && isInteractive,
                isDisabled: isDisabled,
                isVisible: isVisible,
                isInteractive: isInteractive
            };
        """, button)
        
        print(f"Export Report按钮状态检查: {js_check}")
        
        if js_check and js_check.get('isClickable'):
            is_clickable = True
            print("Export Report按钮可点击")
        else:
            print("Export Report按钮不可点击，不尝试点击")
            return False
    except Exception as e:
        print(f"检查按钮可点击状态失败: {e}")
        return False
    
    # 如果按钮可点击，尝试点击
    if is_clickable:
        try:
            take_screenshot(page, "before_click_export")
            button.click()
            print("已点击Export Report按钮")
            take_screenshot(page, "after_click_export")
            time.sleep(2)  # 等待可能的下载对话框
            return True
        except Exception as e:
            print(f"点击Export Report按钮失败: {e}")
            return False
    
    return False

def scrape_aliyun_boce(target_url: str):
    """
    使用DrissionPage访问阿里云网站拨测工具并抓取HTTP检测结果。
    
    :param target_url: 需要检测的网址
    :return: 是否成功导出报告
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
        export_button = wait_for_export_button_clickable(page)
        
        # 6. 点击Export Report按钮
        if export_button:
            success = click_export_button(page, export_button)
            if success:
                print("成功点击Export Report按钮")
                return True
            else:
                print("Export Report按钮点击失败或不可点击")
                # 保存最终状态的截图
                take_screenshot(page, "export_button_click_failed")
                return False
        else:
            # 如果找不到Export Report按钮，保存页面截图
            print("未找到可点击的Export Report按钮，保存页面截图...")
            screenshot_path = take_screenshot(page, "no_clickable_export_button")
            print(f"已保存结果页面截图: {screenshot_path}")
            return False
    
    except Exception as e:
        print(f"在爬虫执行过程中发生意外错误: {e}")
        take_screenshot(page, "critical_error")
        return False
    
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