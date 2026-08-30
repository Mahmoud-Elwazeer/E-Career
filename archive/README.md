> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# E-Career Platform (USAM Jobs)

> **Production Status**: ✅ Live at [https://jobs.usamif.com](https://jobs.usamif.com)

A modern job aggregation platform with AI-powered career intelligence, built with Django REST Framework and React.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 20+
- PostgreSQL 14+
- Redis 6+
- Docker & Docker Compose

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/Mahmoud-Elwazeer/E-Career.git
cd E-Career

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements/development.txt
cp .env.example .env  # Edit with your credentials
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# 3. Start Docker services (Typesense + Qdrant)
docker-compose up -d

# 4. Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

Visit:
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_AUDIT.md](PROJECT_AUDIT.md) | Complete deployment status, architecture, and troubleshooting |
| [WORKFLOW.md](WORKFLOW.md) | Development workflow and common tasks |
| [DEPLOYMENT_GUIDE_PHASE1.md](DEPLOYMENT_GUIDE_PHASE1.md) | Phase 1 deployment instructions |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Nginx (Port 80/443)                │
│              Reverse Proxy + Static Files             │
└───────┬─────────────────────────────────┬───────────┘
        │                                 │
        ▼                                 ▼
┌───────────────┐                  ┌─────────────────┐
│ React Frontend│                  │  Django Backend │
│  (Vite + TS)  │                  │  (DRF + Daphne) │
│  Port: 8080   │                  │   Port: 8000    │
└───────────────┘                  └────────┬────────┘
                                            │
                    ┌───────────────────────┼──────────────────────┐
                    ▼                       ▼                      ▼
            ┌──────────────┐      ┌────────────────┐    ┌────────────────┐
            │ PostgreSQL 14│      │     Redis      │    │     Celery     │
            │  + pgvector  │      │ Cache + Broker │    │ Workers + Beat │
            └──────────────┘      └────────────────┘    └────────────────┘
                    │                                            │
                    └────────────────┬───────────────────────────┘
                                     ▼
                    ┌────────────────────────────────────┐
                    │  Docker Services                   │
                    │  • Typesense (Search)              │
                    │  • Qdrant (Vector DB)              │
                    └────────────────────────────────────┘
```

---

## ✨ Features

### Phase 1 (Deployed) ✅

#### Core Platform
- **User Authentication**: JWT-based auth with email verification
- **Job Aggregation**: Multi-source job scraping with ATS integration
- **Admin Dashboard**: Django Unfold-powered admin interface

#### Search & Discovery
- **Full-Text Search**: Typesense-powered instant search
- **Semantic Search**: Vector embeddings with Qdrant/pgvector
- **Trust Score**: AI-powered legitimacy scoring
- **Smart Filters**: Location, salary, experience, remote options

#### Career Intelligence
- **Talent Score**: Multi-dimensional career scoring (7 dimensions)
  - Skill Score (25%)
  - Experience Score (20%)
  - Portfolio Score (15%)
  - Interview Score (15%)
  - Growth Score (15%)
  - Education Score (15%)
  - Communication Score (10%)
- **Career Brain**: AI-powered career advisor
- **Real-time Updates**: WebSocket-based score notifications
- **Score Trends**: Historical tracking and analytics

#### AI Features
- **Rashid AI**: Egyptian Arabic career assistant
- **Direct Apply Verification**: Automated URL verification
- **Scam Detection**: ML-powered job legitimacy analysis
- **ESCO Taxonomy**: Skills and occupation mapping

#### Employer Portal
- **Job Posting**: Self-service job publishing
- **Application Management**: Track applicants
- **Verification System**: Admin approval workflow

---

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 4.2 + Django REST Framework
- **Database**: PostgreSQL 14 with pgvector extension
- **Cache**: Redis
- **Task Queue**: Celery + Celery Beat
- **WebSockets**: Django Channels + Daphne
- **Search**: Typesense (full-text) + Qdrant/pgvector (semantic)
- **AI**: AWS Bedrock (Claude Sonnet 4, Cohere Embeddings)
- **Web Scraping**: Playwright

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: shadcn/ui + Radix UI
- **Styling**: Tailwind CSS
- **Routing**: React Router
- **State**: React Query + Context
- **Forms**: React Hook Form + Zod

### Infrastructure
- **Server**: Ubuntu 22.04 LTS
- **Web Server**: Nginx
- **Process Manager**: systemd
- **Containerization**: Docker Compose (services)

---

## 📂 Project Structure

```
E-Career/
├── backend/                # Django REST API
│   ├── apps/              # Django applications
│   │   ├── accounts/      # Authentication
│   │   ├── jobs/          # Job listings
│   │   ├── career/        # Career intelligence ⭐
│   │   ├── search/        # Typesense + vector search
│   │   ├── skills/        # ESCO taxonomy
│   │   ├── verification/  # Direct apply verification
│   │   ├── scraper/       # ATS scrapers
│   │   ├── rashid/        # AI assistant
│   │   ├── events/        # Event system + WebSocket
│   │   └── ...
│   ├── config/            # Django settings
│   └── requirements/      # Python dependencies
│
├── frontend/              # React SPA
│   ├── src/
│   │   ├── components/   # Reusable components
│   │   ├── pages/        # Route pages
│   │   ├── services/     # API clients
│   │   └── hooks/        # Custom hooks
│   └── dist/             # Production build
│
├── docs/                  # Documentation
├── PROJECT_AUDIT.md       # Deployment audit ⭐
├── WORKFLOW.md            # Dev workflow ⭐
└── docker-compose.yml     # Local services
```

---

## 🔐 Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=jobs.usamif.com

# Database
DATABASE_URL=postgresql://user:pass@localhost/eusam_db

# AWS Bedrock (for AI features)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_DEFAULT_REGION=us-east-1

# Search
TYPESENSE_API_KEY=your-typesense-key
QDRANT_API_KEY=your-qdrant-key
```

See [.env.example](.env.example) for complete list.

---

## 🚢 Deployment

### Production Deployment

```bash
# 1. Push to GitHub
git add .
git commit -m "Feature description"
git push origin development:main

# 2. Deploy on server
ssh ubuntu@13.49.245.174
cd /var/www/usam/backend
git pull origin main
source /var/www/usam/venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart usam

# 3. Build frontend
cd /var/www/usam/frontend
npm install
npm run build
sudo systemctl reload nginx
```

See [WORKFLOW.md](WORKFLOW.md) for detailed deployment procedures.

---

## 🧪 Testing

```bash
# Backend tests
cd backend
python manage.py test

# Frontend tests
cd frontend
npm test
```

---

## 📊 Monitoring

### Health Checks
- **Backend**: https://jobs.usamif.com/health/
- **Admin**: https://jobs.usamif.com/admin/

### Logs
```bash
# Application logs
sudo journalctl -u usam -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Django logs
tail -f /var/www/usam/backend/logs/django.log
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is proprietary software. All rights reserved.

---

## 👥 Team

- **Backend**: Django REST Framework, Celery, PostgreSQL
- **Frontend**: React, TypeScript, Vite
- **AI/ML**: AWS Bedrock (Claude), Vector Search
- **DevOps**: Nginx, systemd, Docker

---

## 📞 Support

- **Documentation**: [PROJECT_AUDIT.md](PROJECT_AUDIT.md) | [WORKFLOW.md](WORKFLOW.md)
- **Issues**: Use GitHub Issues for bug reports
- **Production**: https://jobs.usamif.com

---

## 🎯 Roadmap

### Phase 2 (Planned)
- [ ] Mobile apps (React Native)
- [ ] Advanced analytics dashboard
- [ ] Company reviews & ratings
- [ ] Salary insights
- [ ] Interview prep tools
- [ ] Career path recommendations

### Phase 3 (Future)
- [ ] Video interviews
- [ ] Skills assessment tests
- [ ] Resume builder
- [ ] Job application tracking
- [ ] Networking features

---

**Built with ❤️ by the USAM Team**

Last Updated: August 2026
