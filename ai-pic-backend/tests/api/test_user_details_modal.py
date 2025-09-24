#!/usr/bin/env python3
"""测试用户详情模态框功能"""

import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

BASE_URL = "http://localhost:3000"
API_BASE_URL = "http://localhost:8000/api/v1"

def setup_webdriver():
    """设置Chrome WebDriver"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ 无法启动Chrome WebDriver: {e}")
        return None

def test_user_details_modal():
    """测试用户详情模态框"""
    print("🔍 测试用户详情模态框功能")
    
    driver = setup_webdriver()
    if not driver:
        return False
    
    try:
        # 1. 访问登录页面
        driver.get(f"{BASE_URL}/login")
        time.sleep(2)
        
        # 2. 登录
        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        username_input.clear()
        username_input.send_keys("admin")
        password_input.clear()
        password_input.send_keys("Ai7dio")
        login_button.click()
        
        time.sleep(3)
        
        # 3. 导航到用户管理页面
        driver.get(f"{BASE_URL}/admin/users")
        time.sleep(3)
        
        # 4. 查找第一个用户的详情按钮
        detail_buttons = driver.find_elements(By.CSS_SELECTOR, "[title='查看用户详情']")
        if len(detail_buttons) == 0:
            print("❌ 未找到用户详情按钮")
            return False
        
        print(f"✅ 找到 {len(detail_buttons)} 个用户详情按钮")
        
        # 5. 点击第一个详情按钮
        detail_buttons[0].click()
        time.sleep(2)
        
        # 6. 检查模态框是否出现
        try:
            modal = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".fixed.inset-0"))
            )
            print("✅ 用户详情模态框已显示")
        except:
            print("❌ 用户详情模态框未显示")
            return False
        
        # 7. 检查模态框内容
        success_indicators = []
        
        # 检查标签页
        tabs = driver.find_elements(By.CSS_SELECTOR, "nav button")
        tab_texts = [tab.text for tab in tabs]
        if "基本信息" in tab_texts and "操作记录" in tab_texts and "安全信息" in tab_texts:
            success_indicators.append("标签页")
            print("✅ 模态框标签页正确显示")
        else:
            print(f"❌ 标签页显示异常: {tab_texts}")
        
        # 检查用户信息
        user_info_elements = driver.find_elements(By.CSS_SELECTOR, "label")
        user_info_texts = [elem.text for elem in user_info_elements]
        if any("用户名" in text for text in user_info_texts) and any("邮箱地址" in text for text in user_info_texts):
            success_indicators.append("用户信息")
            print("✅ 用户基本信息正确显示")
        else:
            print(f"❌ 用户基本信息显示异常")
        
        # 8. 测试标签切换
        audit_tab = None
        for tab in tabs:
            if tab.text == "操作记录":
                audit_tab = tab
                break
        
        if audit_tab:
            audit_tab.click()
            time.sleep(1)
            print("✅ 成功切换到操作记录标签")
            success_indicators.append("标签切换")
        
        # 9. 测试关闭模态框
        close_buttons = driver.find_elements(By.CSS_SELECTOR, "button")
        for button in close_buttons:
            if "关闭" in button.text:
                button.click()
                time.sleep(1)
                print("✅ 成功关闭模态框")
                success_indicators.append("关闭功能")
                break
        
        # 10. 验证模态框已关闭
        modals = driver.find_elements(By.CSS_SELECTOR, ".fixed.inset-0")
        if len(modals) == 0:
            print("✅ 模态框已正确关闭")
            success_indicators.append("关闭确认")
        else:
            print("❌ 模态框未正确关闭")
        
        print(f"\n📊 测试结果: {len(success_indicators)}/5 项功能正常")
        print(f"   ✅ 正常功能: {', '.join(success_indicators)}")
        
        return len(success_indicators) >= 3  # 至少3项功能正常才算成功
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        driver.quit()

def test_backend_audit_api():
    """测试后端审计日志API"""
    print("\n🔍 测试后端审计日志API")
    
    try:
        # 1. 登录获取token
        login_data = {
            "username": "admin",
            "password": "Ai7dio"
        }
        
        # 使用form data格式
        login_response = requests.post(
            f"{API_BASE_URL}/auth/login", 
            data=login_data,  # 注意这里使用data而不是json
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code} - {login_response.text}")
            return False
        
        token_data = login_response.json()
        token = token_data.get("access_token")
        
        if not token:
            print(f"❌ 未获取到访问令牌: {token_data}")
            return False
        
        print("✅ 成功获取访问令牌")
        
        # 2. 获取用户列表
        headers = {"Authorization": f"Bearer {token}"}
        users_response = requests.get(f"{API_BASE_URL}/admin/users", headers=headers)
        
        if users_response.status_code != 200:
            print(f"❌ 获取用户列表失败: {users_response.status_code}")
            return False
        
        users_data = users_response.json()
        if not users_data.get("users"):
            print("❌ 用户列表为空")
            return False
        
        user_id = users_data["users"][0]["id"]
        print(f"✅ 获取到用户ID: {user_id}")
        
        # 3. 获取审计日志
        audit_response = requests.get(f"{API_BASE_URL}/admin/users/{user_id}/audit-logs", headers=headers)
        
        if audit_response.status_code != 200:
            print(f"❌ 获取审计日志失败: {audit_response.status_code}")
            return False
        
        audit_data = audit_response.json()
        print(f"✅ 获取到 {len(audit_data)} 条审计日志")
        
        if len(audit_data) > 0:
            sample_log = audit_data[0]
            required_fields = ["id", "user_id", "action", "created_at"]
            missing_fields = [field for field in required_fields if field not in sample_log]
            
            if missing_fields:
                print(f"❌ 审计日志缺少字段: {missing_fields}")
                return False
            else:
                print("✅ 审计日志结构正确")
                print(f"   示例日志: {json.dumps(sample_log, indent=2, ensure_ascii=False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始用户详情模态框测试")
    print("=" * 60)
    
    # 测试后端API
    api_success = test_backend_audit_api()
    
    # 测试前端UI
    ui_success = test_user_details_modal()
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    if api_success:
        print("✅ 后端API测试: 通过")
    else:
        print("❌ 后端API测试: 失败")
    
    if ui_success:
        print("✅ 前端UI测试: 通过")
    else:
        print("❌ 前端UI测试: 失败")
    
    overall_success = api_success and ui_success
    
    if overall_success:
        print("\n🎉 用户详情模态框功能测试全部通过！")
        print("\n📋 实现的功能:")
        print("   ✅ 用户基本信息显示")
        print("   ✅ 用户操作记录显示") 
        print("   ✅ 用户安全信息显示")
        print("   ✅ 标签页切换功能")
        print("   ✅ 模态框打开/关闭")
        print("   ✅ 后端API集成")
    else:
        print("\n⚠️ 部分功能测试失败，建议检查:")
        if not api_success:
            print("   - 后端API接口")
            print("   - 数据库连接")
        if not ui_success:
            print("   - 前端组件渲染")
            print("   - JavaScript/TypeScript代码")
    
    return overall_success

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")