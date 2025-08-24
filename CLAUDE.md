# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IBS is a comprehensive construction management system built with Django 5.2 backend and dual frontend options (Vue 3 + Svelte). It manages construction projects, contracts, payments, cash flow, and document management for construction companies.

## Development Commands

### Django Backend (app/django/)
```bash
# Run migrations
sh migrate.sh  # Creates migrations for all apps and runs migrate

# Collect static files  
python manage.py collectstatic

# Run development server
python manage.py runserver

# Create superuser
python manage.py createsuperuser

# Load seed data
cd ibs/fixtures && sh loaddata.sh

# Run specific tests
python manage.py test <app_name>
```

### Vue Frontend (app/vue/)
```bash
# Install dependencies
pnpm install

# Development server
pnpm dev

# Build for production
pnpm build

# Run tests
pnpm test:unit
pnpm test:e2e

# Lint code
pnpm lint

# Type check
pnpm type-check
```

### Svelte Frontend (app/svelte/)
```bash
# Install dependencies
pnpm install

# Development server  
pnpm dev

# Build for production
pnpm build
```

## Architecture Overview

### Backend Structure
- **Django Apps**: Modular Django apps handle different business domains:
  - `accounts` - User management and authentication
  - `project` - Construction project management
  - `contract` - Contract and unit management
  - `cash` - Financial transactions and cash flow
  - `payment` - Payment processing and billing
  - `company` - Company and contractor management
  - `work` - Work order and issue tracking with Git integration
  - `notice` - Notifications and communications
  - `apiV1` - REST API endpoints for frontend integration

### Database Architecture
- Supports both PostgreSQL and MariaDB/MySQL via `DATABASE_TYPE` setting
- Database routing configured in `_config/database_router.py`
- Multi-database setup for different environments

### API Structure
- REST API endpoints in `apiV1/` app
- JWT authentication using django-rest-framework-simplejwt
- Serializers organized by domain in `apiV1/serializers/`
- Views organized by domain in `apiV1/views/`

### Frontend Integration
- Vue 3 with Vuetify for main frontend (`app/vue/`)
- Svelte for lightweight components (`app/svelte/`)
- Static file serving through Django's collectstatic

### Key Configuration Files
- `_config/settings.py` - Django settings with environment-based configuration
- `_config/urls.py` - URL routing with health checks and API endpoints
- Environment variables loaded from `.env` file using python-decouple

## Deployment

### Docker Deployment
- Multi-container setup with nginx, Django, and database
- Configuration in `deploy/docker-compose.yml`
- Environment variables managed through docker-compose

### Kubernetes Deployment  
- Helm charts in `deploy/helm/`
- CI/CD with GitHub Actions
- NFS storage for persistent data
- cert-manager for SSL certificates

## Testing

### Django Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test contract
```

### Vue Tests
```bash
# Unit tests with Vitest
pnpm test:unit

# E2E tests with Cypress
pnpm test:e2e
```

## Important Notes

- The project uses custom user model: `AUTH_USER_MODEL = 'accounts.User'`
- Static files are served from `_assets/` directory
- Media files handling configured for both local and cloud storage (S3)
- Multi-language support with Korean as primary language
- Git integration in work app for commit tracking and issue management