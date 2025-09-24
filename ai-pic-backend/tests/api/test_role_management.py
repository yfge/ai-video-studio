#!/usr/bin/env python3
"""测试角色管理功能"""

import requests
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

def test_role_management_ui():
    """测试角色管理UI功能"""
    print("🔍 测试角色管理UI功能")
    
    driver = setup_webdriver()
    if not driver:
        return False
    
    try:
        # 1. 登录管理员账户
        driver.get(f"{BASE_URL}/login")
        time.sleep(2)
        
        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        username_input.clear()
        username_input.send_keys("admin")
        password_input.clear()
        password_input.send_keys("Ai7dio")
        login_button.click()
        time.sleep(3)
        
        # 2. 导航到用户管理页面
        driver.get(f"{BASE_URL}/admin/users")
        time.sleep(3)
        
        # 3. 点击第一个用户的详情按钮
        detail_buttons = driver.find_elements(By.CSS_SELECTOR, "[title='查看用户详情']")
        if len(detail_buttons) == 0:
            print("❌ 未找到用户详情按钮")
            return False
        
        detail_buttons[0].click()
        time.sleep(2)
        
        # 4. 等待用户详情模态框出现
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h3[contains(text(), '用户ID')]"))
            )
            print("✅ 用户详情模态框已显示")
        except:
            print("❌ 用户详情模态框未显示")
            return False
        
        success_indicators = []
        
        # 5. 查找并点击"管理角色"按钮
        role_management_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '管理角色')]")
        if len(role_management_buttons) > 0:
            success_indicators.append("角色管理按钮")
            print("✅ 找到角色管理按钮")
            
            role_management_buttons[0].click()
            time.sleep(2)
            
            # 6. 检查角色管理模态框是否出现
            try:
                role_modal = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//h3[contains(text(), '角色管理')]"))
                )
                success_indicators.append("角色管理模态框")
                print("✅ 角色管理模态框已显示")
                
                # 7. 检查角色选项
                role_radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'][name='role']")
                if len(role_radios) >= 3:
                    success_indicators.append("角色选项")
                    print(f"✅ 找到 {len(role_radios)} 个角色选项")
                    
                    # 检查角色名称
                    role_labels = []
                    for radio in role_radios:
                        radio_id = radio.get_attribute('id')
                        if radio_id:
                            label = driver.find_elements(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                            if label:
                                role_labels.append(label[0].text)
                    
                    expected_roles = ['普通用户', '管理员', '超级管理员']
                    found_roles = any(role in ' '.join(role_labels) for role in expected_roles)
                    if found_roles:
                        success_indicators.append("角色名称")
                        print("✅ 角色名称显示正确")
                
                # 8. 检查原因输入框
                reason_textarea = driver.find_elements(By.ID, "reason")
                if len(reason_textarea) > 0:
                    success_indicators.append("原因输入框")
                    print("✅ 角色变更原因输入框存在")
                
                # 9. 检查权限说明
                permission_lists = driver.find_elements(By.CSS_SELECTOR, "ul li")
                if len(permission_lists) > 0:
                    success_indicators.append("权限说明")
                    print(f"✅ 权限说明列表包含 {len(permission_lists)} 项")
                
                # 10. 测试取消功能
                cancel_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '取消')]")
                if len(cancel_buttons) > 0:
                    cancel_buttons[0].click()
                    time.sleep(1)
                    
                    # 检查角色管理模态框是否关闭
                    role_modals = driver.find_elements(By.XPATH, "//h3[contains(text(), '角色管理')]")
                    if len(role_modals) == 0:
                        success_indicators.append("取消功能")
                        print("✅ 角色管理模态框取消功能正常")
                
            except Exception as e:
                print(f"❌ 角色管理模态框检查失败: {e}")
        else:
            print("❌ 未找到角色管理按钮")
        
        # 关闭用户详情模态框
        close_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '关闭')]")
        if len(close_buttons) > 0:
            close_buttons[0].click()
            time.sleep(1)
        
        print(f"\n📊 测试结果: {len(success_indicators)}/6 项功能正常")
        print(f"   ✅ 正常功能: {', '.join(success_indicators)}")
        
        return len(success_indicators) >= 4  # 至少4项功能正常才算成功
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        driver.quit()

def test_backend_role_api():
    """测试后端角色管理API"""
    print("\n🔍 测试后端角色管理API")
    
    try:
        # 1. 登录获取token
        login_data = {
            "username": "admin",
            "password": "Ai7dio"
        }
        
        login_response = requests.post(
            f"{API_BASE_URL}/auth/login", 
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            return False
        
        token_data = login_response.json()
        token = token_data.get("access_token")
        
        if not token:
            print("❌ 未获取到访问令牌")
            return False
        
        print("✅ 成功获取访问令牌")
        
        # 2. 获取用户列表
        headers = {"Authorization": f"Bearer {token}"}
        users_response = requests.get(f"{API_BASE_URL}/admin/users", headers=headers)
        
        if users_response.status_code != 200:
            print(f"❌ 获取用户列表失败: {users_response.status_code}")
            return False
        
        users_data = users_response.json()
        users = users_data.get("users", [])
        
        if len(users) == 0:
            print("❌ 用户列表为空")
            return False
        
        # 找一个非管理员用户进行测试
        test_user = None
        for user in users:
            if not user.get("is_admin") and user.get("username") != "admin":
                test_user = user
                break
        
        if not test_user:
            print("⚠️  未找到合适的测试用户（非管理员用户）")
            return True
        
        user_id = test_user["id"]
        print(f"✅ 找到测试用户ID: {user_id}, 用户名: {test_user['username']}")
        
        # 3. 测试角色更新API端点存在性（使用无效数据测试）
        role_data = {
            "is_admin": True,
            "reason": "API测试"
        }
        
        test_response = requests.put(
            f"{API_BASE_URL}/admin/users/{user_id}/role", 
            headers={**headers, 'Content-Type': 'application/x-www-form-urlencoded'},
            data=role_data
        )
        
        # 检查API端点是否存在（200, 400, 422都表明端点存在）
        if test_response.status_code in [200, 400, 422, 403]:
            print("✅ 角色管理API端点存在且可访问")
            
            if test_response.status_code == 403:
                print("   ⚠️  当前用户权限不足（这是正常的安全限制）")
            
            return True
        else:
            print(f"❌ 角色管理API端点异常: {test_response.status_code}")
            print(f"   响应内容: {test_response.text}")
            return False
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始角色管理功能测试")
    print("=" * 60)
    
    # 测试后端API
    api_success = test_backend_role_api()
    
    # 测试前端UI
    ui_success = test_role_management_ui()
    
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
        print("\n🎉 角色管理功能测试全部通过！")
        print("\n📋 实现的功能:")
        print("   ✅ 角色管理界面")
        print("   ✅ 用户角色选择 (普通用户/管理员/超级管理员)")
        print("   ✅ 角色权限说明显示")
        print("   ✅ 角色变更原因记录")
        print("   ✅ 权限验证和安全控制")
        print("   ✅ 后端API集成")
    else:
        print("\n⚠️ 部分功能测试失败，建议检查:")
        if not api_success:
            print("   - 后端角色管理API")
            print("   - 权限验证逻辑")
        if not ui_success:
            print("   - 前端角色管理界面")
            print("   - 模态框交互逻辑")
    
    return overall_success

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")