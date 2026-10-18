# 🌟 UtopiaHire - AI-Powered Career Platform

> **A comprehensive, production-ready AI-powered career platform with 5 integrated modules for job seekers and professionals in MENA & Sub-Saharan Africa.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.1.1-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9.3-3178C6.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![Vite](https://img.shields.io/badge/Vite-7.1.7-646CFF.svg)](https://vitejs.dev/)

---

## 📊 Project at a Glance

- **Total Modules**: 5 comprehensive feature modules
- **API Endpoints**: 39 fully documented REST endpoints
- **Database Tables**: 18 optimized PostgreSQL tables with 50+ indexes
- **Backend Dependencies**: 50+ production-grade Python packages
- **Frontend Dependencies**: 20+ modern React ecosystem packages
- **Documentation**: ~9,700+ lines of comprehensive technical documentation
- **Test Coverage**: 15 dedicated test modules covering all features
- **Lines of Code**: Backend (8 API files + 4 migrations), Frontend (12 source directories)

---

## 🚀 Core Features

### 🔐 Module 1: Authentication & User Management
- **Secure JWT-based authentication** with bcrypt password hashing
- User registration and login with email validation
- Protected routes and role-based access control
- Token expiration and refresh mechanisms
- Rate limiting on authentication endpoints (5/minute)

**API Endpoints (6)**: Register, Login, Get Profile, Update Profile, Change Password, Delete Account

### 💼 Module 2: Job Matching & Recommendations
- **AI-powered job matching algorithm** with compatibility scoring
- Real-time job scraping from multiple sources (Google Jobs, LinkedIn, JSearch)
- Advanced filtering by location, salary, experience level, skills
- Job saving and application tracking
- Beautiful animated job grid interface with smooth transitions
- Intelligent fallback strategy across multiple job APIs

**API Endpoints (10)**: Search Jobs, Save Job, Get Saved Jobs, Remove Saved Job, Get Job Details, Get Recommendations, Update Preferences, Get User Jobs, Delete Job, Batch Operations

**Data Sources**: SerpAPI (Google Jobs), LinkedIn RapidAPI, JSearch RapidAPI

### 🤖 Module 3: AI Interview Simulator
- **Interactive AI-powered interview practice** with real-time feedback
- 500+ curated interview questions across multiple categories
- Difficulty levels: Easy, Medium, Hard
- Real-time answer analysis with AI scoring and feedback
- Interview history tracking with performance metrics
- Question categories: Technical, Behavioral, Situational, General

**API Endpoints (8)**: Start Session, Get Questions, Submit Answer, End Session, Get History, Get Feedback, Get Sessions, Delete Session

**AI Engine**: Groq API (llama-3.3-70b-versatile) for ultra-fast response generation

### 🔍 Module 4: Digital Footprint Scanner
- **GitHub profile analysis** with contribution graphs and activity metrics
- **StackOverflow reputation scanning** and expertise tracking
- Multi-platform digital presence assessment (GitHub, StackOverflow, LinkedIn, Twitter)
- Technical, social, and impact score calculation
- Privacy-aware scanning with configurable settings
- AI-powered career recommendations based on footprint analysis

**API Endpoints (5)**: Scan Footprint, Get Scans, Get Scan Details, Update Scan, Delete Scan

**Supported Platforms**: GitHub (full integration), StackOverflow (API integration), LinkedIn (planned), Twitter (planned)

### 📄 Module 5: Resume Analyzer & Enhancer
- **PDF/DOCX resume parsing** with intelligent text extraction
- **AI-powered content analysis** with comprehensive scoring
- Resume structure analysis (sections, formatting, ATS compatibility)
- Skills extraction and categorization
- Professional resume enhancement with AI suggestions
- **3 professional resume templates** (Classic, Modern, Executive)
- **AI-powered cover letter generation** tailored to job descriptions
- **Job compatibility analysis** with detailed insights and recommendations

**API Endpoints (10)**: Upload Resume, Get Resumes, Analyze Resume, Get Analysis, Enhance Resume, Download Enhanced, Generate Cover Letter, Check Compatibility, Delete Resume, Get Templates

**Document Processing**: PyPDF2 3.0.1, python-docx 1.1.0, reportlab 4.0.7

---

## 🛠️ Technology Stack

### Backend (Python 3.9+)

#### Core Framework & API
- **FastAPI** 0.104.1 - Modern async web framework
- **Uvicorn** 0.24.0 [standard] - ASGI server with auto-reload
- **Pydantic** 2.5.0 - Data validation and settings management
- **pydantic-settings** 2.1.0 - Environment configuration

#### Database & Data Layer
- **PostgreSQL** 15+ with advanced features
- **psycopg2-binary** 2.9.9 - PostgreSQL adapter (sync)
- **asyncpg** 0.29.0 - Async PostgreSQL adapter
- **Database Features**:
  - 18 tables organized in 6 modules
  - 50+ optimized indexes (B-tree, GIN, Unique)
  - JSONB columns for flexible data storage
  - Array columns for multi-value fields
  - Triggers and CHECK constraints
  - CASCADE deletes for referential integrity
  - Connection pooling for performance

#### Authentication & Security
- **python-jose[cryptography]** 3.3.0 - JWT token generation
- **passlib[bcrypt]** 1.7.4 - Password hashing
- **python-multipart** 0.0.6 - Form data handling
- **email-validator** 2.1.0 - Email validation

#### AI & Machine Learning
- **Groq API** - Ultra-fast LLM inference (llama-3.3-70b-versatile)
- **nltk** 3.8.1 - Natural Language Processing and text analysis
- **spaCy** (optional) - Advanced NLP features

#### Document Processing
- **PyPDF2** 3.0.1 - PDF parsing and extraction
- **python-docx** 1.1.0 - Word document handling
- **reportlab** 4.0.7 - PDF generation and templates

#### HTTP & External APIs
- **httpx** 0.25.2 - Async HTTP client
- **requests** 2.31.0 - HTTP library for API calls
- **beautifulsoup4** 4.12.2 - HTML parsing
- **lxml** 4.9.3 - XML/HTML processing

#### Development & Testing
- **pytest** 7.4.3 - Testing framework
- **pytest-asyncio** 0.21.1 - Async test support
- **python-dotenv** 1.0.0 - Environment variable management

#### Additional Features
- **slowapi** 0.1.9 - Rate limiting middleware
- **aiofiles** 23.2.1 - Async file operations
- **python-dateutil** 2.8.2 - Date/time utilities

### Frontend (React 19.1.1 + TypeScript 5.9.3)

#### Core Framework
- **React** 19.1.1 - Latest React with concurrent features
- **react-dom** 19.1.1 - React DOM renderer
- **TypeScript** 5.9.3 - Type-safe JavaScript
- **Vite** 7.1.7 - Lightning-fast build tool and dev server

#### Routing & State Management
- **react-router-dom** 7.9.4 - Client-side routing
- **@tanstack/react-query** 5.90.6 - Server state management and caching
- **React Context API** - Global state management

#### HTTP & API Communication
- **axios** 1.12.2 - Promise-based HTTP client

#### Forms & Validation
- **react-hook-form** 7.65.0 - Performant form library
- **zod** 4.1.12 - TypeScript-first schema validation
- **@hookform/resolvers** 5.2.2 - Validation resolvers

#### UI Components & Design
- **@headlessui/react** 2.2.9 - Unstyled, accessible UI components
- **@heroicons/react** 2.2.0 - Beautiful hand-crafted SVG icons
- **lucide-react** 0.546.0 - Icon library
- **react-icons** 5.5.0 - Popular icon packs

#### Styling & Theming
- **tailwindcss** 3.4.18 - Utility-first CSS framework
- **clsx** 2.1.1 - Conditional className utility
- **tailwind-merge** 3.3.1 - Merge Tailwind classes without conflicts
- **@tailwindcss/forms** 0.5.10 - Form styling plugin

#### Animations & Motion
- **framer-motion** 12.23.24 - Production-ready motion library
- **gsap** 3.13.0 - Professional-grade animation library

#### Data Visualization
- **recharts** 3.2.1 - Composable charting library

#### User Experience
- **react-hot-toast** 2.6.0 - Toast notifications

#### Development Tools
- **ESLint** 9.36.0 - Code linting
- **@vitejs/plugin-react** 4.3.4 - Vite React plugin
- **@types/react** 19.0.13 - React TypeScript types

### External APIs & Services

#### AI & Machine Learning
- **Groq API** (llama-3.3-70b-versatile)
  - Ultra-fast LLM inference (< 1 second responses)
  - Resume analysis and enhancement
  - Cover letter generation
  - Interview answer evaluation
  - Career recommendations

#### Job Data Sources (Multi-API Fallback Strategy)
- **SerpAPI** (Google Jobs) - Primary source, 1000+ jobs/search
- **LinkedIn RapidAPI** - Fallback #1, professional network data
- **JSearch RapidAPI** - Fallback #2, aggregated job boards

#### Developer Platform Integrations
- **GitHub API** v3
  - Profile and repository analysis
  - Contribution graphs and activity
  - Language statistics
  - Commit history
- **StackOverflow API** v2.3
  - Reputation tracking
  - Question/answer history
  - Badge and tag expertise
  - Community engagement metrics

---



## 🚀 Quick Start Guide

see SETUP_GUIDE.md
Full Documentation in docs folder

## Deploy online

See [the Vercel and backend deployment guide](docs/DEPLOYMENT.md) to host the
frontend on Vercel and provision PostgreSQL, the API, and persistent resume
storage on Render. The free deployment stores resume files in PostgreSQL and its
database expires after 30 days. The repository includes `vercel.json`, `render.yaml`, and a
production backend container. Hosting requires your provider accounts and API keys.
The Render container also serves the frontend, so the entire application can run
at one Render HTTPS URL when Vercel access is unavailable.

## 🎉 Acknowledgments

- **FastAPI** - For the excellent modern Python web framework
- **React** - For the powerful frontend library
- **Groq** - For ultra-fast LLM inference
- **PostgreSQL** - For the robust database system
- **Vite** - For the lightning-fast build tool
- **TailwindCSS** - For the utility-first CSS framework
- **All Open Source Contributors** - For the amazing tools and libraries

**Built with ❤️ for job seekers in MENA & Sub-Saharan Africa**

⭐ Star us on GitHub if you find UtopiaHire helpful!

</div>
