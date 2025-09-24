# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commit Message Convention

- Use Conventional Commit prefixes in lowercase, for example `fix:`, `feat:`, `chore:`.
- Scope is optional; keep the summary concise and imperative (e.g. `fix: storyboard plan rendering`).
- Any backend change must finish with `pytest` locally before handing results back to the user.

## Project Overview

This is an AI-powered video production workflow platform centered around Virtual IPs (Virtual Intellectual Properties). The platform consists of two main components:

- **ai-pic-backend**: FastAPI-based Python backend service
- **ai-pic-frontend**: Next.js 15 React frontend application

The platform enables users to create virtual characters, generate AI images for them, and produce script content for short video production.

## Common Development Commands

### Backend (ai-pic-backend/)

**Development:**
```bash
cd ai-pic-backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Testing:**
```bash
# Run all tests
python run_tests.py

# Specific test types
python run_tests.py unit           # Unit tests only
python run_tests.py integration    # Integration tests only
python run_tests.py migration      # Migration tests only
python run_tests.py coverage       # With coverage report
python run_tests.py quick          # Skip slow tests
python run_tests.py parallel       # Parallel execution

# Code quality
python run_tests.py lint

# Direct pytest execution (alternative)
pytest                                    # Run all tests
pytest tests/unit/                        # Unit tests only
pytest tests/integration/                 # Integration tests only
pytest tests/ -v                         # Verbose output
pytest tests/ --cov=app --cov-report=html # Coverage report
pytest tests/ -k "test_name"              # Run specific test
pytest tests/ -x                          # Stop on first failure
pytest tests/ --tb=short                  # Short traceback format
```

**AI Service Testing (Critical for Image Generation):**
```bash
# Test AI image generation workflow (ESSENTIAL)
pytest tests/test_fastapi_full_flow.py::test_fastapi_full_image_generation_flow -v

# Test individual AI service components
pytest tests/unit/test_ai_service.py -v

# Test OSS upload functionality
pytest tests/integration/test_oss_service.py -v

# Test with OpenAI API (requires OPENAI_API_KEY in .env)
SKIP_SLOW_TESTS=false pytest tests/ -k "openai" -v

# Test complete image generation pipeline
pytest tests/ -k "image_generation" -v --tb=long
```

**Testing Best Practices:**
```bash
# Before committing code - RUN THESE TESTS:
pytest tests/test_fastapi_full_flow.py -v      # End-to-end functionality
pytest tests/unit/ -v                          # All unit tests  
pytest tests/integration/ -v                   # All integration tests

# Performance testing for AI services
pytest tests/ -k "performance" -v

# Database testing
pytest tests/ -k "database" -v

# Authentication testing
pytest tests/ -k "auth" -v
```

**Database:**
```bash
# Django-style Management (Recommended)
python manage.py migration init       # Initialize database
python manage.py migration upgrade    # Run migrations
python manage.py migration status     # Check status
python manage.py quickstart          # One-command setup

# MySQL Specific
python migrate_mysql.py init          # Initialize MySQL database
python migrate_mysql.py upgrade       # Run migrations
python migrate_mysql.py test          # Test connection

# Migration Management
python manage.py migration create -m "description"  # Create new migration
python manage.py migration current                  # Show current version
python manage.py migration history                  # Show migration history
python manage.py migration validate                 # Validate migrations

# Data Seeds
python manage.py seed create -n "initial_data"     # Create seed file
python manage.py seed run --all                    # Run all seeds
```

### Frontend (ai-pic-frontend/)

**Development:**
```bash
cd ai-pic-frontend
npm install
npm run dev                        # Standard development server
npm run dev:turbo                  # With Turbopack (faster)
```

**Build & Deploy:**
```bash
npm run build                      # Production build
npm start                          # Start production server
npm run lint                       # ESLint check
```

## Architecture Overview

### Backend Architecture

The backend follows a clean FastAPI architecture:

- **Core (`app/core/`)**: Configuration, database setup, security
- **Models (`app/models/`)**: SQLAlchemy ORM models for Virtual IPs, images, stories, scripts, etc.
- **Schemas (`app/schemas/`)**: Pydantic models for request/response validation
- **API (`app/api/v1/`)**: REST API endpoints organized by domain
- **Services (`app/services/`)**: Business logic, including AI service integrations

**Key Features:**
- Multi-AI service support (OpenAI DALL-E, Stability AI, custom services)
- Virtual IP image generation with categories (portrait, full_body, scene, action, emotion)
- Story and episode generation workflow
- Comprehensive testing framework with pytest

### Frontend Architecture

The frontend uses Next.js 15 with App Router:

- **App Router (`src/app/`)**: Page components following Next.js 15 conventions
- **API Client (`src/utils/api.ts`)**: Centralized HTTP client with TypeScript types
- **Styling**: Tailwind CSS for consistent design

**Key Pages:**
- Virtual IP management (`/virtual-ip/`)
- Image management for Virtual IPs (`/virtual-ip/[id]/images/`)
- Story creation and management (`/stories/`)
- Episode management (`/episodes/[id]/`)
- Script generation (`/scripts/[id]/`)

### Database Schema

**Core Models:**
- `virtual_ips`: Virtual character definitions with style prompts and metadata
- `virtual_ip_images`: Image assets with categorization and AI generation metadata
- `stories`: Story-level content with genre, theme, and character relationships
- `episodes`: Episode-level content linked to stories
- `scripts`: Formatted scripts linked to episodes

## AI Integration

The platform integrates multiple AI services through a comprehensive multi-provider architecture:

1. **Image Generation**: 
   - ✅ OpenAI DALL-E 3 (fully integrated)
   - ✅ Keling AI (快手可灵) - video and image generation (integrated with retry mechanism)
   - ⚡ Stability AI (configured, ready to use)
   - 🔧 Custom endpoints (framework ready)

2. **Video Generation**:
   - ✅ Keling AI - text-to-video and image-to-video (fully integrated)
   - 🔧 Framework supports additional video providers

3. **Content Generation**: Story, episode, and script generation through AI models with template system

4. **AI Service Management**:
   - ✅ Multi-provider architecture with load balancing
   - ✅ Automatic failover and retry mechanisms  
   - ✅ Provider priority and weight configuration
   - ✅ Rate limiting and request management
   - ✅ Real-time provider status monitoring

**Configuration**: All AI services are configured via environment variables in `.env` files.

**Keling AI Integration Status**: ✅ **Fully Integrated** 
- API authentication and requests working correctly
- Retry mechanism handles service busy conditions
- Support for multiple models (kling-image, kling-v1, etc.)
- Seamless integration with existing image generation workflow

## Development Workflow

1. **Backend First**: Start the backend server for API development
2. **Database Setup**: Run migrations to ensure schema is up to date
3. **Frontend Development**: Use the frontend dev server with hot reload
4. **Testing**: Run comprehensive tests before commits
5. **Type Safety**: Both backend (Pydantic) and frontend (TypeScript) enforce strict typing

## Environment Configuration

### Backend (.env in ai-pic-backend/)

**MySQL (Production Recommended):**
```bash
SECRET_KEY=your-secret-key
DATABASE_URL=mysql+pymysql://root:Pa88word@127.0.0.1:13306/ai_video_studio?charset=utf8mb4

# AI服务配置
OPENAI_API_KEY=sk-your-openai-api-key              # OpenAI DALL-E (单密钥)
STABILITY_API_KEY=sk-your-stability-api-key        # Stability AI (单密钥)

# 中国AI服务商 - 双密钥认证
KELING_API_KEY=your-keling-api-key                 # 可灵AI（快手）
KELING_SECRET_KEY=your-keling-secret-key
JIMENG_API_KEY=your-jimeng-api-key                 # 即梦AI  
JIMENG_SECRET_KEY=your-jimeng-secret-key
VOLCENGINE_API_KEY=your-volcengine-api-key         # 火山引擎
VOLCENGINE_SECRET_KEY=your-volcengine-secret-key
VOLCENGINE_REGION=cn-beijing

# 其他AI服务商
DEEPSEEK_API_KEY=your-deepseek-api-key             # DeepSeek (单密钥)
MINIMAX_API_KEY=your-minimax-api-key               # MiniMax
MINIMAX_GROUP_ID=your-minimax-group-id
```

**重要说明：**
- **单密钥服务**：OpenAI、Stability AI、DeepSeek 只需要API_KEY
- **双密钥服务**：可灵、即梦、火山引擎需要API_KEY + SECRET_KEY
- **动态模型检测**：系统会根据配置的环境变量自动检测可用模型
- **只有正确配置的服务才会在模型选择中显示**

**✅ 可灵AI状态**: 已完全集成，包含重试机制和错误处理
- 支持图像生成模型：kling-image
- 支持视频生成模型：kling-v1, kling-video-pro, kling-image2video
- 自动处理服务繁忙状态并重试
- 与现有工作流无缝集成

**SQLite (Development):**
```bash
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./ai_pic.db
OPENAI_API_KEY=your-openai-key
STABILITY_API_KEY=your-stability-key
```

### Frontend (.env.local in ai-pic-frontend/)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing Strategy

The backend uses a comprehensive testing approach with **multiple test execution frameworks**:

### Test Framework Architecture

- **Unit Tests**: Individual component testing (`tests/unit/`)
- **Integration Tests**: API endpoint testing (`tests/integration/`)  
- **End-to-End Tests**: Full workflow testing (`tests/test_fastapi_full_flow.py`)
- **Migration Tests**: Database schema validation
- **Coverage Reports**: Minimum 80% coverage requirement

### Test Execution Methods

1. **`run_tests.py` Script** (Recommended for CI/CD):
   ```bash
   python run_tests.py                    # All tests with intelligent categorization
   python run_tests.py unit              # Unit tests only
   python run_tests.py integration       # Integration tests only
   python run_tests.py coverage          # With HTML coverage report
   ```

2. **Direct pytest** (Recommended for Development):
   ```bash
   pytest tests/ -v                      # All tests with verbose output
   pytest tests/unit/ -v                 # Unit tests only
   pytest tests/integration/ -v          # Integration tests only
   ```

3. **AI Service Testing** (Critical Components):
   ```bash
   # ESSENTIAL: Full AI image generation workflow test
   pytest tests/test_fastapi_full_flow.py::test_fastapi_full_image_generation_flow -v
   
   # Component-level AI service testing
   pytest tests/unit/test_ai_service.py -v
   pytest tests/integration/test_oss_service.py -v
   ```

### Critical Test Cases for AI Image Generation

**必须通过的核心测试** (Must-pass core tests):

1. **End-to-End Workflow**: `test_fastapi_full_image_generation_flow`
   - Tests: FastAPI → AI Service → OpenAI DALL-E → Image Download → Local Storage → OSS Upload → Database Save
   - **Status**: ✅ PASSING (All components working)

2. **AI Service Unit Tests**: Individual component validation
   - OpenAI API integration
   - Image format handling (base64/URL)
   - Error handling and fallbacks

3. **OSS Integration Tests**: Storage service validation
   - File upload to Aliyun OSS
   - Metadata handling
   - Signature generation

### Test Environment Requirements

**Environment Variables for Testing:**
```bash
# Required for AI service tests
OPENAI_API_KEY=sk-your-actual-openai-key    # Real key needed for integration tests

# Required for OSS tests (if testing OSS functionality)  
OSS_ACCESS_KEY_ID=your-oss-access-key
OSS_ACCESS_KEY_SECRET=your-oss-secret-key
OSS_BUCKET_NAME=your-bucket-name

# Test database (separate from development)
TEST_DATABASE_URL=sqlite:///./test_ai_pic.db
```

**Dependencies for Testing:**
```bash
pip install pytest pytest-asyncio pytest-cov httpx aiofiles
```

### Test Data Management

- **Test Fixtures**: Automated creation of test users, Virtual IPs, and sample data
- **Database Cleanup**: Automatic cleanup after each test
- **File Cleanup**: Automatic cleanup of generated images and temporary files
- **Mock Services**: Fallback mock services when real AI APIs are unavailable

### Testing Best Practices for This Project

1. **Before Any Commit**: Always run the full E2E test
   ```bash
   pytest tests/test_fastapi_full_flow.py -v
   ```

2. **AI Service Development**: Test individual components first
   ```bash
   pytest tests/unit/test_ai_service.py -v
   ```

3. **API Development**: Test endpoints with authentication
   ```bash
   pytest tests/integration/ -v -k "api"
   ```

4. **Database Changes**: Run migration tests
   ```bash
   pytest tests/ -k "migration" -v
   ```

### Current Test Status

- ✅ **AI Image Generation Pipeline**: Fully tested and working
- ✅ **Authentication System**: Complete test coverage
- ✅ **Database Operations**: Comprehensive CRUD testing  
- ✅ **OSS Storage Integration**: Tested and functional
- ✅ **Error Handling**: Robust error recovery testing

The testing framework has been battle-tested through the complete AI image generation debugging process and provides comprehensive coverage for all critical system components.

## Migration System

The project features a comprehensive database migration system that extends Alembic with FastAPI integration:

**Key Features:**
- Django-style management commands (`manage.py`)
- REST API endpoints for migration status and control
- Data seeding system with rollback support
- Automatic safety checks and data integrity validation
- Migration templates with utility functions
- Backup and rollback point management
- Real-time migration status monitoring via middleware

**Quick Commands:**
```bash
python manage.py quickstart           # One-command project setup
python manage.py migration status     # Check migration status
python manage.py dev check           # Project health check
python manage.py server run          # Start development server
```

**Migration API Endpoints:**
- `GET /api/v1/migrations/status` - Migration status
- `GET /api/v1/migrations/health` - System health check
- `POST /api/v1/migrations/upgrade` - Upgrade database
- `POST /api/v1/migrations/seeds/run` - Run data seeds

See `MIGRATION_SYSTEM_GUIDE.md` for detailed documentation.

## Key Dependencies

**Backend:**
- FastAPI for API framework
- SQLAlchemy for ORM
- Alembic for migrations (extended)
- Pydantic for data validation
- pytest for testing
- Click for CLI commands
- PyMySQL for MySQL support

**Frontend:**
- Next.js 15 with App Router
- React 19
- TypeScript for type safety
- Tailwind CSS for styling

## Current System Status

### ✅ Fully Implemented Features

**User Authentication & Security:**
- ✅ JWT token-based authentication system
- ✅ OAuth2 password flow for login
- ✅ User registration and management
- ✅ Protected API endpoints (all business APIs require authentication)
- ✅ Frontend route guards with AuthGuard component
- ✅ Default admin user: `admin / Ai7dio`
- ✅ Automatic token refresh and management

**Database & Migration System:**
- ✅ MySQL 8.0+ support with UTF8MB4 charset
- ✅ Complete Alembic-based migration system
- ✅ Django-style management commands via `manage.py`
- ✅ Data seeding system with rollback support
- ✅ 11 core business tables initialized
- ✅ Database backup and safety checks
- ✅ REST API for migration management

**Backend Services:**
- ✅ FastAPI application fully configured
- ✅ Virtual IP CRUD operations with authentication
- ✅ Virtual IP image management APIs
- ✅ Story, episode, and script management APIs
- ✅ AI service integration framework
- ✅ File upload and management  
- ✅ Comprehensive error handling
- ✅ **AI Image Generation**: OpenAI DALL-E 3 integration complete
- ✅ **OSS Storage**: Aliyun OSS upload with metadata handling
- ✅ **Advanced Logging**: Request/response tracking with correlation IDs

**Frontend Application:**
- ✅ Next.js 15 with App Router architecture
- ✅ User authentication flow (login/logout)
- ✅ Virtual IP management interface
- ✅ Story creation interface
- ✅ Responsive design with Tailwind CSS
- ✅ API client with automatic authentication
- ✅ Route protection for authenticated pages

### 🚀 Server Status

**Backend Server**: 
- ✅ Running on http://localhost:8000
- ✅ All APIs protected with authentication
- ✅ Swagger documentation: http://localhost:8000/docs

**Frontend Server**:
- ✅ Running on http://localhost:3000  
- ✅ Route guards active
- ✅ Authentication flow working

**Database**:
- ✅ MySQL 8.0.32 running on localhost:13306
- ✅ Database: `ai_video_studio`
- ✅ 11 tables with sample data
- ✅ Initial Virtual IPs: 小雅, 李教授, 奶奶陈

### 🔐 Authentication & Access

**Default User Credentials:**
- Username: `admin`
- Password: `Ai7dio`
- Email: `admin@ai-video-studio.com`
- Role: Super Administrator

**Security Features:**
- ❌ **No authentication** = No access to any business APIs
- ✅ **With authentication** = Full access to all features
- ✅ Frontend redirects to login if not authenticated
- ✅ API returns `{"detail":"Not authenticated"}` for protected endpoints

### 📋 Development Environment

**Python Environment:**
- ✅ Node.js 20.19.4 LTS (for frontend)
- ✅ Python 3.11 with conda environment (for backend)
- ✅ All dependencies installed and working

**Development Commands Currently Running:**
```bash
# Backend (Terminal 1)
cd ai-pic-backend
eval "$(/opt/homebrew/bin/conda shell.bash hook)" && conda activate py311
python manage.py server run --host 0.0.0.0 --port 8000

# Frontend (Terminal 2) 
cd ai-pic-frontend
npm run dev
```

### 🛠️ Next Development Steps

**Immediate Priorities:**
1. ✅ **AI Integration**: OpenAI DALL-E image generation fully implemented and tested
2. **Story Generation**: Complete AI-powered story creation workflow
3. ✅ **File Management**: Local storage and OSS upload fully implemented
4. **UI Polish**: Enhance frontend user experience and design

**AI Image Generation Status**: 🎉 **FULLY OPERATIONAL**
- ✅ OpenAI DALL-E 3 integration working
- ✅ Base64 and URL image format handling
- ✅ Local file storage with UUID naming
- ✅ OSS upload with signature issue resolved
- ✅ Database persistence complete
- ✅ Comprehensive testing framework

**Future Enhancements:**
1. **Role-based Access Control**: Implement user roles and permissions
2. **API Rate Limiting**: Add rate limiting for production use
3. **Monitoring**: Add logging and monitoring systems
4. **Deployment**: Configure production deployment

### ⚡ Quick Start for Development

To resume development:

1. **Start Backend:**
   ```bash
   cd ai-pic-backend
   eval "$(/opt/homebrew/bin/conda shell.bash hook)" && conda activate py311
   python manage.py server run --host 0.0.0.0 --port 8000
   ```

2. **Start Frontend:**
   ```bash
   cd ai-pic-frontend  
   npm run dev
   ```

3. **Access System:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - Login: admin / Ai7dio

The system is now fully operational with complete user authentication, database management, and AI image generation capabilities!

## Testing Requirements and Practices

### 🧪 Essential Testing Commands

**Before ANY code changes, ALWAYS run these tests:**

```bash
# 1. CRITICAL: Full AI image generation workflow test
pytest tests/test_fastapi_full_flow.py::test_fastapi_full_image_generation_flow -v

# 2. All unit tests 
pytest tests/unit/ -v

# 3. All integration tests
pytest tests/integration/ -v
```

**For AI service development specifically:**
```bash
# Test AI service components individually
pytest tests/unit/test_ai_service.py -v

# Test OSS upload functionality  
pytest tests/integration/test_oss_service.py -v

# Test with real OpenAI API (requires valid OPENAI_API_KEY)
SKIP_SLOW_TESTS=false pytest tests/ -k "openai" -v
```

### 🔍 Debugging AI Image Generation Issues

If AI image generation fails, follow this debugging sequence:

1. **Check Environment Variables:**
   ```bash
   # Verify OpenAI API key is set
   echo $OPENAI_API_KEY
   
   # Check OSS configuration  
   echo $OSS_ACCESS_KEY_ID
   echo $OSS_BUCKET_NAME
   ```

2. **Run Diagnostic Tests:**
   ```bash
   # Test OpenAI API connectivity
   pytest tests/unit/test_ai_service.py::test_openai_dalle_generation -v
   
   # Test OSS upload
   pytest tests/integration/test_oss_service.py::test_upload_file -v
   
   # Full end-to-end test with detailed logging
   pytest tests/test_fastapi_full_flow.py -v --tb=long
   ```

3. **Check Logs:**
   ```bash
   # View recent application logs
   tail -f logs/ai-video-studio.log
   
   # Filter for AI service specific logs
   grep "generate_virtual_ip_image" logs/ai-video-studio.log
   
   # Check for OSS upload issues
   grep "OSS" logs/ai-video-studio.log
   ```

### 📋 Test File Structure and Key Tests

```
tests/
├── conftest.py                          # pytest configuration and fixtures
├── test_fastapi_full_flow.py           # 🔥 CRITICAL E2E tests
│   └── test_fastapi_full_image_generation_flow  # Must-pass test
├── unit/
│   ├── test_ai_service.py              # AI service unit tests
│   ├── test_models.py                  # Database model tests  
│   └── test_schemas.py                 # Pydantic schema tests
└── integration/
    ├── test_oss_service.py             # OSS upload tests
    ├── test_api_endpoints.py           # API endpoint tests
    └── test_database.py               # Database integration tests
```

### 🛠️ Test Environment Setup

**Required Environment Variables:**
```bash
# Core testing requirements
OPENAI_API_KEY=sk-your-actual-key        # Required for AI tests
TEST_DATABASE_URL=sqlite:///./test.db    # Separate test database

# Optional (for OSS testing)
OSS_ACCESS_KEY_ID=your-key
OSS_ACCESS_KEY_SECRET=your-secret
OSS_BUCKET_NAME=test-bucket
OSS_REGION=oss-cn-beijing
```

**Test Dependencies:**
```bash
pip install pytest pytest-asyncio pytest-cov httpx aiofiles python-multipart
```

### 🚨 Critical Test Cases Status

- ✅ **AI Image Generation End-to-End**: PASSING
  - Creates test user and Virtual IP
  - Calls OpenAI DALL-E API and Keling AI
  - Downloads and saves image locally  
  - Uploads to OSS storage
  - Saves metadata to database
  - **NEW**: Multi-provider support with automatic failover
  
- ✅ **Multi-Provider AI Integration**: PASSING
  - ✅ OpenAI DALL-E integration working
  - ✅ Keling AI provider fully integrated with retry mechanism
  - ✅ AI service manager load balancing and failover
  - ✅ Provider priority and weight management
  
- ✅ **Authentication System**: PASSING
  - JWT token generation and validation
  - Protected endpoint access
  - User session management
  
- ✅ **Database Operations**: PASSING
  - CRUD operations for all models
  - Migration system validation
  - Data integrity checks

### 💡 Testing Best Practices

1. **Always run the E2E test first** - it catches integration issues
2. **Use verbose output** (`-v`) to see detailed test progress
3. **Check logs** if tests fail - the logging system provides detailed error information
4. **Test with real APIs** when possible - mock tests don't catch API changes
5. **Clean test data** - tests automatically clean up created files and database records

This comprehensive testing strategy ensures the AI image generation system remains reliable and catches issues early in development.

**🎯 Recent Achievement**: Successfully integrated Keling AI (快手可灵) with complete multi-provider architecture, demonstrating robust error handling, retry mechanisms, and seamless provider switching capabilities.
