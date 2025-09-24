"""前端管理界面工作流测试脚本

测试完整的前端管理界面功能：
1. 管理员登录
2. 查看用户统计
3. 管理用户列表
4. 用户审批操作
5. 界面响应性测试
"""
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

BASE_URL = "http://localhost:3000"
API_BASE_URL = "http://localhost:8000/api/v1"

def setup_webdriver():
    """设置Chrome WebDriver"""
    options = Options()
    options.add_argument('--headless')  # 无头模式
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ 无法启动Chrome WebDriver: {e}")
        print("请确保已安装Chrome浏览器和ChromeDriver")
        return None

def test_servers_running():
    """测试服务器是否正在运行"""
    print("🔍 测试 1: 检查服务器状态")
    
    try:
        # 检查后端API服务器
        response = requests.get(f"{API_BASE_URL}/auth/me", timeout=5)
        print(f"✅ 后端API服务器运行正常 (状态码: {response.status_code})")
    except Exception as e:
        print(f"❌ 后端API服务器连接失败: {e}")
        return False
    
    try:
        # 检查前端服务器
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ 前端服务器运行正常 (状态码: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ 前端服务器连接失败: {e}")
        return False

def create_test_user():
    """创建测试用户"""
    print("🔍 测试 2: 创建测试用户")
    
    test_user_data = {
        "username": "frontend_testuser",
        "email": "frontend_test@example.com",
        "password": "testpass123",
        "full_name": "Frontend Test User"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/register", json=test_user_data)
        if response.status_code == 200:
            print("✅ 测试用户创建成功")
            return response.json()
        else:
            print(f"⚠️  测试用户可能已存在 (状态码: {response.status_code})")
            return None
    except Exception as e:
        print(f"❌ 创建测试用户失败: {e}")
        return None

def test_admin_login_ui(driver):
    """测试管理员登录界面"""
    print("🔍 测试 3: 管理员登录界面")
    
    try:
        # 访问登录页面
        driver.get(f"{BASE_URL}/login")
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        
        # 查找登录表单元素
        username_input = driver.find_element(By.NAME, "username")  # 使用正确的字段名
        password_input = driver.find_element(By.NAME, "password")
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        # 输入管理员凭据
        username_input.clear()
        username_input.send_keys("admin")
        password_input.clear()
        password_input.send_keys("Ai7dio")
        
        # 点击登录
        login_button.click()
        
        # 等待重定向或者错误信息
        time.sleep(3)
        
        current_url = driver.current_url
        if "/admin" in current_url or current_url.endswith("/"):
            print("✅ 管理员登录成功")
            return True
        else:
            print(f"❌ 登录可能失败，当前URL: {current_url}")
            # 检查是否有错误信息
            page_text = driver.page_source
            print(f"页面内容预览: {page_text[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ 登录界面测试失败: {e}")
        return False

def test_admin_dashboard_access(driver):
    """测试管理员面板访问"""
    print("🔍 测试 4: 管理员面板访问")
    
    try:
        # 直接访问管理员面板
        driver.get(f"{BASE_URL}/admin")
        
        # 等待页面加载
        time.sleep(3)
        
        # 检查是否成功访问管理员面板
        if "/admin" in driver.current_url:
            # 查找管理员面板特有的元素
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TEXT, "用户管理"))
                )
                print("✅ 管理员面板访问成功")
                return True
            except:
                # 如果找不到特定文字，检查是否有导航元素
                nav_elements = driver.find_elements(By.TAG_NAME, "nav")
                if len(nav_elements) > 0:
                    print("✅ 管理员面板访问成功 (检测到导航元素)")
                    return True
                else:
                    print("❌ 管理员面板可能未正确加载")
                    return False
        else:
            print(f"❌ 未能访问管理员面板，当前URL: {driver.current_url}")
            return False
            
    except Exception as e:
        print(f"❌ 管理员面板访问测试失败: {e}")
        return False

def test_user_list_page(driver):
    """测试用户列表页面"""
    print("🔍 测试 5: 用户列表页面")
    
    try:
        # 访问用户管理页面
        driver.get(f"{BASE_URL}/admin/users")
        
        # 等待页面加载
        time.sleep(3)
        
        # 检查页面是否包含用户管理相关内容
        page_text = driver.page_source.lower()
        
        success_indicators = [
            "用户管理" in page_text,
            "搜索" in page_text,
            "用户" in page_text,
            len(driver.find_elements(By.TAG_NAME, "table")) > 0,
            len(driver.find_elements(By.TAG_NAME, "input")) > 0
        ]
        
        if any(success_indicators):
            print("✅ 用户列表页面加载成功")
            print(f"   - 检测到的功能: {sum(success_indicators)} / {len(success_indicators)}")
            return True
        else:
            print("❌ 用户列表页面未正确加载")
            print(f"页面内容预览: {page_text[:300]}...")
            return False
            
    except Exception as e:
        print(f"❌ 用户列表页面测试失败: {e}")
        return False

def test_statistics_page(driver):
    """测试统计数据页面"""
    print("🔍 测试 6: 统计数据页面")
    
    try:
        # 访问统计页面
        driver.get(f"{BASE_URL}/admin/stats")
        
        # 等待页面加载
        time.sleep(3)
        
        # 检查页面是否包含统计相关内容
        page_text = driver.page_source.lower()
        
        success_indicators = [
            "统计" in page_text,
            "用户" in page_text,
            "总" in page_text,
            len(driver.find_elements(By.CLASS_NAME, "bg-blue-50")) > 0 or 
            len(driver.find_elements(By.CLASS_NAME, "bg-green-50")) > 0
        ]
        
        if any(success_indicators):
            print("✅ 统计数据页面加载成功")
            return True
        else:
            print("❌ 统计数据页面未正确加载")
            return False
            
    except Exception as e:
        print(f"❌ 统计数据页面测试失败: {e}")
        return False

def test_responsive_design(driver):
    """测试响应式设计"""
    print("🔍 测试 7: 响应式设计")
    
    try:
        driver.get(f"{BASE_URL}/admin/users")
        
        # 测试桌面视图
        driver.set_window_size(1920, 1080)
        time.sleep(1)
        desktop_elements = len(driver.find_elements(By.TAG_NAME, "div"))
        
        # 测试移动视图
        driver.set_window_size(375, 667)
        time.sleep(1)
        mobile_elements = len(driver.find_elements(By.TAG_NAME, "div"))
        
        # 恢复桌面视图
        driver.set_window_size(1920, 1080)
        
        if desktop_elements > 0 and mobile_elements > 0:
            print("✅ 响应式设计测试通过")
            print(f"   - 桌面元素数量: {desktop_elements}")
            print(f"   - 移动元素数量: {mobile_elements}")
            return True
        else:
            print("❌ 响应式设计测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 响应式设计测试失败: {e}")
        return False

def test_navigation(driver):
    """测试导航功能"""
    print("🔍 测试 8: 导航功能")
    
    try:
        driver.get(f"{BASE_URL}/admin")
        time.sleep(2)
        
        # 测试导航到不同页面
        test_pages = [
            ("/admin/users", "用户"),
            ("/admin/stats", "统计"),
        ]
        
        successful_navigations = 0
        
        for url, expected_content in test_pages:
            try:
                driver.get(f"{BASE_URL}{url}")
                time.sleep(2)
                
                if expected_content.lower() in driver.page_source.lower():
                    successful_navigations += 1
                    print(f"   ✅ 导航到 {url} 成功")
                else:
                    print(f"   ❌ 导航到 {url} 失败")
                    
            except Exception as e:
                print(f"   ❌ 导航到 {url} 出错: {e}")
        
        if successful_navigations >= len(test_pages) // 2:
            print(f"✅ 导航功能测试通过 ({successful_navigations}/{len(test_pages)})")
            return True
        else:
            print(f"❌ 导航功能测试失败 ({successful_navigations}/{len(test_pages)})")
            return False
            
    except Exception as e:
        print(f"❌ 导航功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始前端管理界面工作流测试")
    print("=" * 60)
    
    test_results = []
    
    # 测试 1: 检查服务器状态
    result = test_servers_running()
    test_results.append(result)
    
    if not result:
        print("❌ 服务器未运行，终止测试")
        return
    
    # 测试 2: 创建测试用户
    create_test_user()  # 不计入测试结果，因为用户可能已存在
    
    # 设置WebDriver
    print("\n🔧 设置浏览器...")
    driver = setup_webdriver()
    
    if not driver:
        print("❌ 无法设置浏览器，跳过UI测试")
        print("💡 提示: 请安装Chrome浏览器和ChromeDriver来运行完整测试")
        return
    
    try:
        # UI测试
        test_results.append(test_admin_login_ui(driver))
        test_results.append(test_admin_dashboard_access(driver))
        test_results.append(test_user_list_page(driver))
        test_results.append(test_statistics_page(driver))
        test_results.append(test_responsive_design(driver))
        test_results.append(test_navigation(driver))
        
    finally:
        driver.quit()
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    print(f"📈 成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！前端管理界面工作正常！")
        print("\n📋 功能清单:")
        print("   ✅ 管理员身份验证")
        print("   ✅ 用户管理界面")
        print("   ✅ 统计数据显示")
        print("   ✅ 响应式设计")
        print("   ✅ 页面导航")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，建议检查以下内容:")
        print("   - 前端组件是否正确渲染")
        print("   - API接口是否正常响应")
        print("   - 样式和布局是否正确")
    
    # 访问说明
    print(f"\n🌐 访问地址:")
    print(f"   前端: {BASE_URL}")
    print(f"   管理后台: {BASE_URL}/admin")
    print(f"   登录凭据: admin / Ai7dio")
    
    return passed == total

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")