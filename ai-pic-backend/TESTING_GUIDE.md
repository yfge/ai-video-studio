# 测试指南

本项目使用 pytest 作为测试框架，提供了完整的测试套件来确保代码质量和功能正确性。

## 快速开始

### 安装测试依赖

```bash
# 安装测试依赖
pip install -r requirements-test.txt
```

### 运行测试

```bash
# 使用Python脚本（推荐）
python run_tests.py                    # 运行所有测试
python run_tests.py unit              # 只运行单元测试
python run_tests.py integration       # 只运行集成测试
python run_tests.py migration         # 只运行迁移测试
python run_tests.py coverage          # 运行测试并生成覆盖率报告

# 使用Windows批处理文件
run_tests.bat all                      # 运行所有测试
run_tests.bat unit                     # 只运行单元测试
run_tests.bat coverage                 # 运行测试并生成覆盖率报告

# 直接使用pytest
pytest tests/                          # 运行所有测试
pytest tests/test_models.py            # 运行特定测试文件
pytest tests/test_models.py::TestUserModel::test_create_user  # 运行特定测试
```

## 测试结构

```
tests/
├── __init__.py                 # 测试包初始化
├── conftest.py                 # pytest配置和夹具
├── factories.py                # 测试数据工厂
├── test_migrations.py          # 迁移测试
├── test_models.py              # 模型单元测试
└── test_api.py                 # API集成测试
```

## 测试分类

### 单元测试 (Unit Tests)

- 测试单个函数或方法
- 不依赖外部系统
- 运行速度快
- 标记: `@pytest.mark.unit`

```python
@pytest.mark.unit
def test_user_creation():
    user = User(username="test", email="test@example.com")
    assert user.username == "test"
```

### 集成测试 (Integration Tests)

- 测试多个组件的交互
- 可能涉及数据库、API等
- 标记: `@pytest.mark.integration`

```python
@pytest.mark.integration
def test_create_virtual_ip_api(client):
    response = client.post("/api/v1/virtual-ips/", json={"name": "Test IP"})
    assert response.status_code == 201
```

### 端到端测试 (E2E Tests)

- 测试完整的用户工作流
- 模拟真实用户操作
- 标记: `@pytest.mark.e2e`

```python
@pytest.mark.e2e
def test_complete_story_workflow(client):
    # 创建虚拟IP -> 生成故事 -> 创建剧集 -> 生成剧本
    pass
```

### 迁移测试 (Migration Tests)

- 测试数据库迁移
- 确保SQLite兼容性
- 验证表结构和关系

```python
def test_migration_creates_all_tables():
    # 测试迁移创建所有必要的表
    pass
```

## 测试配置

### pytest.ini

项目根目录的 `pytest.ini` 文件包含了pytest的配置：

```ini
[tool:pytest]
testpaths = tests
markers =
    unit: 单元测试
    integration: 集成测试
    e2e: 端到端测试
    slow: 慢速测试
addopts = -v --cov=app --cov-report=html
```

### 测试数据库

测试使用内存SQLite数据库，每个测试函数都会重置数据库状态：

```python
@pytest.fixture(scope="function")
def db_session():
    # 为每个测试提供干净的数据库会话
    reset_test_database()
    session = next(test_db.get_session())
    yield session
    session.close()
```

## 测试夹具 (Fixtures)

### 数据库夹具

- `db_session`: 提供数据库会话
- `client`: 提供测试客户端
- `setup_test_environment`: 设置测试环境

### 数据夹具

- `sample_image_file`: 提供示例图片文件
- `auth_headers`: 提供认证头部
- `temp_upload_dir`: 提供临时上传目录

### Mock夹具

- `mock_ai_service`: 模拟AI服务
- `mock_redis`: 模拟Redis服务

## 测试工厂

使用 Factory Boy 创建测试数据：

```python
from tests.factories import UserFactory, VirtualIPFactory

def test_user_creation(db_session):
    setup_factories(db_session)
    user = UserFactory()
    assert user.username is not None
```

### 可用工厂

- `UserFactory`: 创建用户
- `VirtualIPFactory`: 创建虚拟IP
- `VirtualIPImageFactory`: 创建虚拟IP图像
- `StoryFactory`: 创建故事
- `EpisodeFactory`: 创建剧集
- `ScriptFactory`: 创建剧本
- `StoryCharacterFactory`: 创建故事角色
- `ScriptTemplateFactory`: 创建剧本模板

## 覆盖率报告

运行覆盖率测试后，会生成多种格式的报告：

```bash
python run_tests.py coverage
```

生成的报告：

- **HTML报告**: `htmlcov/index.html` - 可视化覆盖率报告
- **XML报告**: `coverage.xml` - 用于CI/CD集成
- **终端报告**: 直接在终端显示

## 数据库迁移测试

专门的迁移测试确保：

- 所有表都被正确创建
- 索引和外键约束正确
- SQLite兼容性
- 迁移可以回退
- JSON字段正常工作

```python
def test_migration_sqlite_compatibility():
    # 测试迁移与SQLite的兼容性
    command.upgrade(alembic_cfg, "head")
    # 执行CRUD操作验证
```

### 结构化场景/镜头回归

- 校验场景/节拍/镜头的顺序/唯一性与归属关系：
  ```bash
  pytest tests/test_story_structure_endpoints.py -q
  ```
- 覆盖场景、节拍顺序冲突、镜头号重复、beat 场景不匹配等 400 场景。

## 异步任务与 Celery Worker

- 后端异步故事/剧集/剧本生成（`/stories/generate-async`、`/episodes/generate-async`、`/scripts/generate-async`）通过 Celery 执行。
- 本地验证异步任务时，需在 `ai-pic-backend` 目录下额外启动 worker：

  ```bash
  celery -A app.core.celery_app.celery_app worker -l info
  ```

- 生产环境中，`docker/docker-compose.prod.yml` 中的 `ai-video-celery-worker` 服务会自动随后端一同启动。

### 迁移验证与回滚

- 在本地 MySQL/SQLite 运行迁移回填：
  ```bash
  alembic upgrade c4a1cbf0d7c2
  python prototype_story_structure_migration.py --mode live --insert-probe --report-path /tmp/story-migration-report.json
  ```
- 回滚验证：
  ```bash
  alembic downgrade -1
  ```
- 运行快速迁移回归：
  ```bash
  python run_tests.py migration
  ```

### 前端结构化 CRUD 验证

- 前端权限/只读提示与结构化场景加载单测：
  ```bash
  cd ai-pic-frontend
  npm test
  ```
  覆盖只读模式的防写保护、结构加载回调。

## 最佳实践

### 1. 测试隔离

每个测试都应该独立运行，不依赖其他测试的状态：

```python
def test_something(db_session):
    # 每个测试都有干净的数据库会话
    reset_test_database()
    # 测试逻辑
```

### 2. 使用工厂创建数据

使用工厂而不是手动创建测试数据：

```python
# 好的做法
user = UserFactory()

# 避免的做法
user = User(username="test", email="test@example.com", ...)
```

### 3. 测试边界情况

不仅测试正常情况，也要测试边界情况：

```python
def test_user_creation_with_long_username():
    # 测试用户名长度限制
    with pytest.raises(ValidationError):
        UserFactory(username="a" * 1000)
```

### 4. 使用描述性的测试名称

测试名称应该清楚地说明测试的内容：

```python
def test_create_virtual_ip_with_valid_data():
    # 清楚地表明测试的目的
    pass
```

### 5. Mock外部依赖

对于外部API调用，使用mock：

```python
def test_generate_image(mock_ai_service):
    # AI服务被mock，不会真正调用外部API
    result = generate_image("test prompt")
    assert result["success"] is True
```

## 持续集成

测试可以集成到CI/CD流水线中：

```yaml
# GitHub Actions示例
- name: Run tests
  run: |
    python run_tests.py coverage

- name: Upload coverage
  uses: codecov/codecov-action@v1
  with:
    file: ./coverage.xml
```

## 性能测试

对于慢速测试，使用 `slow` 标记：

```python
@pytest.mark.slow
def test_large_dataset_processing():
    # 处理大量数据的测试
    pass
```

快速测试时跳过慢速测试：

```bash
python run_tests.py quick  # 跳过慢速测试
```

## 并行测试

使用 pytest-xdist 进行并行测试：

```bash
python run_tests.py parallel  # 并行运行测试
```

## 故障排除

### 常见问题

1. **导入错误**

   - 确保虚拟环境已激活
   - 检查PYTHONPATH设置

2. **数据库错误**

   - 确保测试数据库配置正确
   - 检查迁移是否已应用

3. **依赖错误**
   - 运行 `pip install -r requirements-test.txt`
   - 确保所有测试依赖已安装

### 调试测试

使用 `-s` 参数查看print输出：

```bash
pytest tests/test_models.py::test_user_creation -s
```

使用 `--pdb` 进入调试器：

```bash
pytest tests/test_models.py::test_user_creation --pdb
```

## 贡献指南

提交代码前请确保：

1. 所有测试通过
2. 代码覆盖率达到80%以上
3. 新功能有对应的测试
4. 代码通过linting检查

```bash
# 运行完整的检查
python run_tests.py coverage
python run_tests.py lint
```
