#!/usr/bin/env python3
"""测试审批API修复"""

import requests

API_BASE_URL = "http://localhost:8000/api/v1"

def test_approval_api():
    """测试审批API"""
    print("🔍 测试审批API修复")
    
    try:
        # 1. 登录
        login_response = requests.post(
            f"{API_BASE_URL}/auth/login", 
            data={"username": "admin", "password": "Ai7dio"},
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            return False
        
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 登录成功")
        
        # 2. 获取用户列表
        users_response = requests.get(f"{API_BASE_URL}/admin/users", headers=headers)
        if users_response.status_code != 200:
            print(f"❌ 获取用户列表失败: {users_response.status_code}")
            return False
        
        users_data = users_response.json()
        users = users_data.get('users', [])
        print(f"✅ 获取到 {len(users)} 个用户")
        
        # 3. 找一个未审批的用户
        pending_user = None
        for user in users:
            if not user.get('is_approved'):
                pending_user = user
                break
        
        if not pending_user:
            print("⚠️  没有待审批用户，跳过审批测试")
            return True
        
        user_id = pending_user['id']
        print(f"✅ 找到待审批用户: {pending_user['username']} (ID: {user_id})")
        
        # 4. 测试审批API - 使用正确的格式
        approval_data = {
            "action": "approve", 
            "reason": "API修复测试 - 自动审批"
        }
        
        approval_response = requests.put(
            f"{API_BASE_URL}/admin/users/{user_id}/approval",
            headers={**headers, 'Content-Type': 'application/json'},
            json=approval_data
        )
        
        if approval_response.status_code == 200:
            print("✅ 审批API正常工作")
            result = approval_response.json()
            print(f"   用户 {result.get('username')} 审批状态: {'已审批' if result.get('is_approved') else '未审批'}")
            return True
        else:
            print(f"❌ 审批API失败: {approval_response.status_code}")
            print(f"   错误详情: {approval_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    print("🚀 审批API修复验证")
    print("=" * 40)
    
    if test_approval_api():
        print("\n✅ 审批API修复成功")
        print("现在前端审批功能应该可以正常工作了")
    else:
        print("\n❌ 审批API仍有问题")
    
    print("\n💡 建议:")
    print("  1. 重新登录前端系统清除旧token")
    print("  2. 测试审批模态框功能")
    print("  3. 检查浏览器控制台错误")

if __name__ == "__main__":
    main()