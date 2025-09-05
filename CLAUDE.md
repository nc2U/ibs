# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IBS is a comprehensive construction management system built with Django 5.2 backend and dual frontend options (Vue 3 + Svelte). It manages construction projects, contracts, payments, cash flow, and document management for construction companies.

## Development Commands

### Docker Development (Recommended)
```bash
# Django commands via Docker
docker compose -f deploy/docker-compose.yml exec web python manage.py <command>

# Examples:
docker compose -f deploy/docker-compose.yml exec web python manage.py check
docker compose -f deploy/docker-compose.yml exec web python manage.py showmigrations
docker compose -f deploy/docker-compose.yml exec web python manage.py test <app_name>
docker compose -f deploy/docker-compose.yml exec web sh migrate.sh
```

### Django Backend (app/django/)
```bash
# Run migrations (creates migrations for all apps and runs migrate)
sh migrate.sh

# Collect static files  
python manage.py collectstatic

# Run development server
python manage.py runserver

# Create superuser
python manage.py createsuperuser

# Load seed data
cd ibs/fixtures && sh loaddata.sh

# Run tests
python manage.py test
python manage.py test <app_name>

# Check system
python manage.py check
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

# Lint and format
pnpm lint
pnpm format

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

# Start production server
pnpm start
```

## Architecture Overview

### Backend Structure
- **Django Apps**: Modular Django apps handle different business domains:
  - `accounts` - User management and authentication (custom User model)
  - `project` - Construction project management
  - `contract` - Contract and unit management
  - `cash` - Financial transactions and cash flow
  - `payment` - Payment processing and billing
  - `company` - Company and contractor management
  - `work` - Work order and issue tracking with Git integration
  - `notice` - Notifications and communications
  - `board` - Board/forum functionality
  - `book` - Document/book management
  - `docs` - Documentation system
  - `items` - Item/inventory management
  - `apiV1` - REST API endpoints for frontend integration

### Database Architecture
- Supports both PostgreSQL and MariaDB/MySQL via `DATABASE_TYPE` environment variable
- Master-slave routing configured in `_config/database_router.py`
- Replica database for read operations (when `KUBERNETES_SERVICE_HOST` environment variable is present)
- All writes go to default database, reads can be distributed to replica
- Multi-database setup for different environments (default/replica)

### API Structure  
- REST API endpoints organized in `apiV1/` app
- JWT authentication using django-rest-framework-simplejwt
- Domain-based organization:
  - Serializers in `apiV1/serializers/` (accounts, company, project, etc.)
  - ViewSets in `apiV1/views/` (corresponding to each domain)
- DefaultRouter for automatic URL generation

### Frontend Integration
- **Vue 3**: Main SPA with Vite build system, TypeScript, Vuetify UI framework
  - Rich component ecosystem (d3, charts, markdown editor, date picker)
  - State management with Pinia
  - Testing with Vitest and Cypress
- **Svelte**: Lightweight components with Rollup build system
- Static file serving through Django's collectstatic from `_assets/` directory
- Media files support (local and S3 cloud storage)

### Configuration Architecture
- `_config/settings.py` - Django settings with python-decouple for environment variables
- `_config/urls.py` - Main URL routing with health checks and API endpoints
- `_config/database_router.py` - Database routing logic for master-slave setup
- Environment variables loaded from `.env` file in Django root
- Docker environment variables in `deploy/docker-compose.yml`

## Deployment

### Docker Deployment (Production Ready)
- **Multi-container setup**: nginx (reverse proxy), Django (uwsgi), PostgreSQL
- **Configuration**: `deploy/docker-compose.yml` with service definitions
- **Current Status**: 3 containers running (ibs-nginx, ibs-django, ibs-postgres)
- **Ports**: nginx on port 80, Django internal on 8000, PostgreSQL on 5432
- **Volumes**: Persistent data, static/media files, database backups
- **Environment**: Timezone set to Asia/Seoul, Korean language support

### Kubernetes Deployment
- **Helm Charts**: Complete deployment setup in `deploy/helm/`
- **CI/CD**: Comprehensive GitHub Actions workflows for automated deployment
  - Separate workflows for Django, Vue, and Svelte components
- **Storage**: NFS subdir external provisioner for persistent storage
- **Security**: cert-manager for SSL certificate management
- **Ingress**: nginx-ingress for traffic management
- **Database**: PostgreSQL with backup and replication support

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

## CI/CD and Automation

### GitHub Actions Workflows
- **Production Deployments**: Automated workflows for master branch
  - `django_prod.yml` - Django backend deployment
  - `vue_prod.yml` - Vue frontend build and deployment  
  - `svelte_prod.yml` - Svelte frontend deployment
- **Development Deployments**: Development branch workflows
- **Database Operations**: Backup, sync, and initialization scripts
- **Helm Deployments**: Kubernetes deployment automation
- **Security**: CodeQL analysis for vulnerability scanning

### Deployment Process
1. **Step 1**: `_init_setup_prod_1.yml` - Initial infrastructure setup
2. **Step 2**: `_init_setup_prod_2.yml` - Application deployment and configuration
3. **Slack Integration**: Notifications for deployment status

## Important Notes

### Core Configuration
- Custom user model: `AUTH_USER_MODEL = 'accounts.User'`
- Static files served from `_assets/` directory
- Media files support: local storage and S3 cloud storage
- Primary language: Korean with timezone Asia/Seoul
- Email integration with SMTP configuration

### Development Practices
- All database migrations applied and up-to-date
- Docker containers stable (7+ days uptime)
- Master-slave database routing for scalability
- Git integration in work app for commit tracking and issue management

### File Structure
- Django backend in `app/django/`
- Vue frontend in `app/vue/` (TypeScript, Vuetify)
- Svelte frontend in `app/svelte/` (Rollup build)
- Deployment configs in `deploy/`
- Docker volumes in `volume/` for persistent data