# 测试目录结构

这个目录包含了AI Video Studio后端项目的所有测试文件，按功能和类型进行分类组织。

## 目录结构

### `/api/` - API测试

包含API端点、用户管理、权限控制等相关测试：

- `test_role_management.py` - 角色管理API测试
- `test_user_approval_modal.py` - 用户审批界面API测试
- `test_user_details_modal.py` - 用户详情界面API测试
- `test_approval_fix.py` - 审批功能修复测试
- `test_suspension_controls.py` - 用户停用控制测试

### `/unit/` - 单元测试

测试独立的功能模块和组件：

- `test_config.py` - 配置模块测试
- `test_database.py` - 数据库连接和操作测试
- `test_openai_unit.py` - OpenAI API单元测试
- `test_user_management_service.py` - 用户管理服务测试

### `/integration/` - 集成测试

测试不同模块之间的交互：

- `test_ai_generation.py` - AI生成功能集成测试
- `test_ai_image_generation.py` - AI图像生成集成测试
- `test_keling_ai.py` - 可灵AI服务集成测试
- `test_oss.py` - 阿里云OSS存储集成测试
- `test_oss_detailed.py` - OSS详细功能测试

### `/e2e/` - 端到端测试

测试完整的用户工作流：

- `test_user_management_e2e.py` - 用户管理端到端测试
- `test_frontend_admin_workflow.py` - 前端管理员工作流测试
- `test_frontend_access.py` - 前端访问控制测试

### `/manual/` - 手动测试

需要手动执行或特殊环境的测试：

- `test_migration_manual.py` - 数据库迁移手动测试
- `test_mysql_connection.py` - MySQL连接手动测试

### `/experimental/` - 实验性测试

开发过程中的实验性和调试测试：

- `test_keling_direct.py` - 可灵AI直接调用测试
- `test_keling_fixed.py` - 可灵AI修复版本测试
- `test_keling_mock.py` - 可灵AI模拟测试
- `test_simple.py` - 简单功能测试
- `test_imports.py` - 导入模块测试

### `/services/` - 服务测试

特定服务的测试：

- `test_diagnostic_service.py` - 诊断服务测试

## 核心测试文件

根目录下的重要测试文件：

- `test_fastapi_full_flow.py` - **关键** - 完整FastAPI流程测试
- `test_full_image_generation.py` - 完整图像生成流程测试
- `test_ai_service.py` - AI服务核心测试
- `conftest.py` - pytest配置和fixture
- `factories.py` - 测试数据工厂

## 运行测试

### 运行所有测试

```bash
python run_tests.py
```

### 按类别运行测试

```bash
python run_tests.py unit              # 单元测试
python run_tests.py integration       # 集成测试
python run_tests.py e2e              # 端到端测试
```

### 运行特定目录的测试

```bash
pytest tests/api/ -v                  # API测试
pytest tests/unit/ -v                 # 单元测试
pytest tests/integration/ -v          # 集成测试
pytest tests/e2e/ -v                  # 端到端测试
```

### 运行关键测试

```bash
# 最重要的端到端测试
pytest tests/test_fastapi_full_flow.py::test_fastapi_full_image_generation_flow -v

# AI图像生成完整流程
pytest tests/test_full_image_generation.py -v
```

## 测试标记

测试使用了以下pytest标记进行分类：

- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.e2e` - 端到端测试
- `@pytest.mark.manual` - 手动测试
- `@pytest.mark.slow` - 慢速测试

## 注意事项

1. **环境配置**: 确保在运行测试前设置了正确的环境变量（OPENAI_API_KEY等）
2. **数据库**: 集成测试会使用测试数据库，确保数据库连接正常
3. **依赖服务**: 某些测试需要外部服务（OpenAI API、OSS等）
4. **并发执行**: 使用 `python run_tests.py parallel` 可以并发运行测试提高速度

## 测试覆盖率

运行覆盖率测试：

```bash
python run_tests.py coverage
```

这将生成HTML覆盖率报告，目标是保持80%以上的测试覆盖率。
