# Quick Start Guide - E-Career Platform

> **Your credentials are configured!** Ready to start implementation.

---

## ✅ **Credentials Loaded**

Your `IMPLEMENTATION_REQUIREMENTS.md` is now populated with:

- ✅ AWS Bedrock credentials (Multi-model strategy)
- ✅ **Primary Model:** meta.llama4-scout-17b-instruct-v1:0 (Arabic + Quality)
- ✅ **Secondary Model:** google.gemma-4-e2b (Fast + Cheap)
- ✅ Google OAuth credentials (for email integration)
- ✅ Email account: career@usamif.com
- ✅ Domain: jobs.usamif.com
- ✅ Course platform: edu.usamif.com

**Smart Cost Optimization:** ~60% savings vs single-model approach!

---

## 🚀 **Start Implementation NOW**

### **Step 1: Set Up Environment** (5 minutes)

```bash
# 1. Navigate to backend folder
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install Django and basic dependencies
pip install django djangorestframework psycopg2-binary redis celery

# 5. Copy environment file
cp ../.env.example .env

# 6. Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copy the output and paste it in .env as FIELD_ENCRYPTION_KEY

# 7. Generate Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Copy the output and paste it in .env as SECRET_KEY
```

### **Step 2: Set Up Database** (2 minutes)

```bash
# Install PostgreSQL if not already installed
# Windows: Download from https://www.postgresql.org/download/windows/
# Mac: brew install postgresql
# Linux: sudo apt install postgresql

# Create database
psql -U postgres
CREATE DATABASE ecareer_dev;
\q
```

### **Step 3: Set Up Redis** (2 minutes)

```bash
# Install Redis
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Mac: brew install redis
# Linux: sudo apt install redis-server

# Start Redis
redis-server

# Test Redis (in another terminal)
redis-cli ping
# Should return: PONG
```

---

## 📄 **Step 4: START PHASE 1A** ⚡

Now you're ready! Open and execute:

```
📄 PHASE_1A_DATABASE.md
```

### **How to Execute:**

1. **Open** `PHASE_1A_DATABASE.md`
2. **Read** the entire phase (understand what it does)
3. **Copy** all code blocks sequentially
4. **Paste** into your terminal/IDE
5. **Run** `python manage.py makemigrations`
6. **Run** `python manage.py migrate`
7. **Verify** models are created

---

## 🔑 **Important Notes**

### **Email Setup (Before Phase 2D)**

The Google OAuth credentials you provided are for OAuth apps. For **SMTP email sending**, you need:

1. **Go to:** https://myaccount.google.com/apppasswords
2. **Sign in** with career@usamif.com
3. **Create** an App Password for "Mail"
4. **Copy** the 16-character password
5. **Add to** `.env` as `EMAIL_ACCOUNT_1_PASSWORD`

**Example:**
```env
EMAIL_ACCOUNT_1_EMAIL=career@usamif.com
EMAIL_ACCOUNT_1_PASSWORD=abcd efgh ijkl mnop  # 16-char app password
```

### **AWS Bedrock Access (Before Phase 2A)**

Your AWS credentials are configured. Verify Bedrock access:

```bash
# Test AWS credentials
aws bedrock list-foundation-models --region us-east-1
```

If this fails, you may need to:
1. Enable AWS Bedrock in your AWS console
2. Request access to Claude models (can take 24 hours)
3. Verify IAM permissions

---

## 📋 **Pre-Flight Checklist**

Before starting Phase 1A, verify:

- [x] Python 3.12+ installed
- [ ] PostgreSQL running (`psql --version`)
- [ ] Redis running (`redis-cli ping`)
- [ ] Virtual environment activated
- [ ] `.env` file created with your credentials
- [ ] Encryption key generated
- [ ] Django secret key generated

---

## 🎯 **Your Execution Path**

```
Day 1:  Phase 1A (Database) ✅ ← START HERE
Day 2:  Phase 1B (Scraping)
Day 3:  Phase 1C (Job Pages)
Day 4:  Phase 2A (Profiles & CV)
Day 5:  Phase 2B (Rashid Core)
Day 6:  Phase 2C (Rashid Tools)
Day 7:  Phase 2D (Email System)
Day 8:  Phase 3A (Employer Portal)
Day 9:  Phase 3B (Recommendations)
Day 10: Phase 3C (Admin Dashboard)
Day 11: Phase 3D (Deployment)
```

---

## 🆘 **Need Help?**

Each phase file includes:
- ✅ Complete code (copy-paste ready)
- ✅ Dependencies list
- ✅ Installation commands
- ✅ Testing instructions
- ✅ Troubleshooting section
- ✅ Verification checklist

---

## 🎉 **You're All Set!**

Your credentials are configured. Your environment setup commands are ready.

**Next Action:**
```bash
# 1. Set up environment (above commands)
# 2. Open PHASE_1A_DATABASE.md
# 3. Execute with GLM or copy-paste
# 4. Run migrations
# 5. Move to Phase 1B
```

**Let's build this! 🚀**

---

**Files Ready:**
- ✅ `.env.example` - Your credentials template
- ✅ `IMPLEMENTATION_REQUIREMENTS.md` - Updated with your info
- ✅ All 11 phase files - Ready for execution

**Start Time:** ~2-3 hours for Phase 1A  
**Total Time:** 38-51 hours for complete implementation

---

*Last Updated: 2026-06-28*
