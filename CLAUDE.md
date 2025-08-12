# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
```

**Database:**
```bash
# Run migrations
python migrate.py
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

The platform integrates multiple AI services:

1. **Image Generation**: OpenAI DALL-E, Stability AI, custom endpoints
2. **Content Generation**: Story, episode, and script generation through AI models
3. **Prompt Engineering**: Automatic prompt optimization based on Virtual IP characteristics

**Configuration**: All AI services are configured via environment variables in `.env` files.

## Development Workflow

1. **Backend First**: Start the backend server for API development
2. **Database Setup**: Run migrations to ensure schema is up to date
3. **Frontend Development**: Use the frontend dev server with hot reload
4. **Testing**: Run comprehensive tests before commits
5. **Type Safety**: Both backend (Pydantic) and frontend (TypeScript) enforce strict typing

## Environment Configuration

### Backend (.env in ai-pic-backend/)
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

The backend uses a comprehensive testing approach:
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Migration Tests**: Database schema validation
- **Coverage Reports**: Minimum 80% coverage requirement

Testing is managed through the `run_tests.py` script with multiple execution modes.

## Key Dependencies

**Backend:**
- FastAPI for API framework
- SQLAlchemy for ORM
- Alembic for migrations
- Pydantic for data validation
- pytest for testing

**Frontend:**
- Next.js 15 with App Router
- React 19
- TypeScript for type safety
- Tailwind CSS for styling