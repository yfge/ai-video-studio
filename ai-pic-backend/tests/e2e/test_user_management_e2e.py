"""用户管理系统端到端测试脚本

测试完整的用户管理工作流程：
1. 用户注册（默认未激活）
2. 管理员审批用户
3. 用户登录验证
4. 权限控制测试
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"


def test_user_registration():
    """测试用户注册 - 应该创建未激活用户"""
    print("🔍 测试 1: 用户注册")

    # 注册新用户
    registration_data = {
        "username": "testuser123",
        "email": "testuser123@example.com",
        "password": "testpass123",
        "full_name": "Test User 123",
    }

    response = requests.post(f"{BASE_URL}/auth/register", json=registration_data)

    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ 用户注册成功: {user_data['username']}")
        print(f"   - is_active: {user_data['is_active']} (应为 False)")
        print(f"   - is_approved: {user_data['is_approved']} (应为 False)")
        print(f"   - email_verified: {user_data['email_verified']} (应为 False)")
        return user_data
    else:
        print(f"❌ 注册失败: {response.status_code} - {response.text}")
        return None


def test_inactive_user_login(username: str):
    """测试未激活用户登录 - 应该失败"""
    print(f"🔍 测试 2: 未激活用户登录 ({username})")

    login_data = {"username": username, "password": "testpass123"}

    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)

    if response.status_code == 403:
        print("✅ 未激活用户登录被正确拒绝")
        print(f"   错误信息: {response.json()['detail']}")
        return True
    else:
        print(f"❌ 未激活用户登录测试失败: {response.status_code}")
        return False


def get_admin_token():
    """获取管理员令牌"""
    print("🔍 获取管理员令牌")

    # 使用现有的admin账户
    login_data = {"username": "admin", "password": "Ai7dio"}

    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)

    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ 管理员登录成功")
        return token
    else:
        print(f"❌ 管理员登录失败: {response.status_code} - {response.text}")
        return None


def test_admin_user_list(admin_token: str):
    """测试管理员获取用户列表"""
    print("🔍 测试 3: 管理员获取用户列表")

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/admin/users", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 获取用户列表成功，共 {data['total']} 个用户")
        print(f"   当前页: {data['page']}, 每页: {data['size']}")

        # 查找我们刚注册的用户
        test_user = None
        for user in data["users"]:
            if user["username"] == "testuser123":
                test_user = user
                break

        if test_user:
            print(f"✅ 找到测试用户: {test_user['username']}")
            print(f"   - ID: {test_user['id']}")
            print(
                f"   - 状态: 激活={test_user['is_active']}, 审批={test_user['is_approved']}"
            )
            return test_user["id"]
        else:
            print("❌ 未找到测试用户")
            return None
    else:
        print(f"❌ 获取用户列表失败: {response.status_code} - {response.text}")
        return None


def test_approve_user(admin_token: str, user_id: int):
    """测试管理员审批用户"""
    print(f"🔍 测试 4: 管理员审批用户 (ID: {user_id})")

    headers = {"Authorization": f"Bearer {admin_token}"}
    approval_data = {"action": "approve", "reason": "自动化测试审批"}

    response = requests.put(
        f"{BASE_URL}/admin/users/{user_id}/approval",
        headers=headers,
        json=approval_data,
    )

    if response.status_code == 200:
        user_data = response.json()
        print("✅ 用户审批成功")
        print(f"   - is_active: {user_data['is_active']} (现在应为 True)")
        print(f"   - is_approved: {user_data['is_approved']} (现在应为 True)")
        return True
    else:
        print(f"❌ 用户审批失败: {response.status_code} - {response.text}")
        return False


def test_approved_user_login():
    """测试已审批用户登录 - 需要邮箱验证"""
    print("🔍 测试 5: 已审批用户登录")

    login_data = {"username": "testuser123", "password": "testpass123"}

    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)

    if response.status_code == 403:
        error_msg = response.json()["detail"]
        if "验证" in error_msg:
            print("✅ 用户需要邮箱验证才能登录 - 正确的行为")
            print(f"   错误信息: {error_msg}")
            return True
        else:
            print(f"❌ 意外的错误信息: {error_msg}")
            return False
    elif response.status_code == 200:
        print("❌ 未验证邮箱的用户不应该能够登录")
        return False
    else:
        print(f"❌ 登录测试失败: {response.status_code} - {response.text}")
        return False


def test_admin_verify_email(admin_token: str, user_id: int):
    """测试管理员手动验证用户邮箱"""
    print(f"🔍 测试 6: 管理员手动验证邮箱 (ID: {user_id})")

    headers = {"Authorization": f"Bearer {admin_token}"}
    update_data = {"email_verified": True}

    response = requests.put(
        f"{BASE_URL}/admin/users/{user_id}", headers=headers, json=update_data
    )

    if response.status_code == 200:
        user_data = response.json()
        print("✅ 邮箱验证状态更新成功")
        print(f"   - email_verified: {user_data['email_verified']} (现在应为 True)")
        return True
    else:
        print(f"❌ 邮箱验证更新失败: {response.status_code} - {response.text}")
        return False


def test_fully_activated_user_login():
    """测试完全激活用户登录 - 应该成功"""
    print("🔍 测试 7: 完全激活用户登录")

    login_data = {"username": "testuser123", "password": "testpass123"}

    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)

    if response.status_code == 200:
        token_data = response.json()
        print("✅ 完全激活用户登录成功")
        print(f"   - 获得访问令牌: {token_data['access_token'][:20]}...")
        return token_data["access_token"]
    else:
        print(f"❌ 登录失败: {response.status_code} - {response.text}")
        return None


def test_regular_user_cannot_access_admin(user_token: str):
    """测试普通用户无法访问管理员接口"""
    print("🔍 测试 8: 普通用户访问管理员接口")

    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BASE_URL}/admin/users", headers=headers)

    if response.status_code == 403:
        print("✅ 普通用户正确被阻止访问管理员接口")
        print(f"   错误信息: {response.json()['detail']}")
        return True
    else:
        print(f"❌ 普通用户权限控制失败: {response.status_code}")
        return False


def test_user_can_access_protected_routes(user_token: str):
    """测试用户可以访问受保护的普通路由"""
    print("🔍 测试 9: 用户访问受保护路由")

    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        print("✅ 用户可以访问受保护的路由")
        print(f"   - 用户名: {user_data['username']}")
        print(f"   - 邮箱: {user_data['email']}")
        return True
    else:
        print(f"❌ 用户访问受保护路由失败: {response.status_code} - {response.text}")
        return False


def test_admin_user_stats(admin_token: str):
    """测试管理员获取用户统计"""
    print("🔍 测试 10: 管理员获取用户统计")

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/admin/stats", headers=headers)

    if response.status_code == 200:
        stats = response.json()
        print("✅ 获取用户统计成功")
        print(f"   - 总用户数: {stats['total_users']}")
        print(f"   - 活跃用户: {stats['active_users']}")
        print(f"   - 待审批: {stats['pending_approval']}")
        print(f"   - 管理员: {stats['admin_users']}")
        return True
    else:
        print(f"❌ 获取用户统计失败: {response.status_code} - {response.text}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始用户管理系统端到端测试")
    print("=" * 50)

    test_results = []

    # 测试 1: 用户注册
    user_data = test_user_registration()
    test_results.append(user_data is not None)

    if not user_data:
        print("❌ 用户注册失败，终止测试")
        return

    # 测试 2: 未激活用户登录
    result = test_inactive_user_login(user_data["username"])
    test_results.append(result)

    # 获取管理员令牌
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员令牌，终止测试")
        return

    # 测试 3: 管理员获取用户列表
    user_id = test_admin_user_list(admin_token)
    test_results.append(user_id is not None)

    if not user_id:
        print("❌ 无法找到测试用户，终止测试")
        return

    # 测试 4: 管理员审批用户
    result = test_approve_user(admin_token, user_id)
    test_results.append(result)

    # 测试 5: 已审批但未验证邮箱的用户登录
    result = test_approved_user_login()
    test_results.append(result)

    # 测试 6: 管理员手动验证邮箱
    result = test_admin_verify_email(admin_token, user_id)
    test_results.append(result)

    # 测试 7: 完全激活用户登录
    user_token = test_fully_activated_user_login()
    test_results.append(user_token is not None)

    if not user_token:
        print("❌ 用户无法获得访问令牌，跳过权限测试")
    else:
        # 测试 8: 普通用户权限控制
        result = test_regular_user_cannot_access_admin(user_token)
        test_results.append(result)

        # 测试 9: 用户访问受保护路由
        result = test_user_can_access_protected_routes(user_token)
        test_results.append(result)

    # 测试 10: 管理员统计
    result = test_admin_user_stats(admin_token)
    test_results.append(result)

    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)

    passed = sum(test_results)
    total = len(test_results)

    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    print(f"📈 成功率: {passed/total*100:.1f}%")

    if passed == total:
        print("\n🎉 所有测试通过！用户管理系统工作正常！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查系统配置")

    return passed == total


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器已启动")
        print("   启动命令: uvicorn main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
