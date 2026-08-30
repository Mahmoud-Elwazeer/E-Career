# 🚀 E-Career Deployment Guide

**Single Server Deployment** - Everything on one EC2 instance!

## Server Details
- **Server:** usam-backend (13.49.245.174)
- **Domain:** jobs.usamif.com
- **What's deployed:** Backend API + Frontend + Database + Redis + Celery

---

## 📋 Prerequisites

1. **EC2 Instance:** usam-backend (13.49.245.174) - Ubuntu 22.04
2. **SSH Key:** Your EC2 key pair (.pem file)
3. **Domain:** Point jobs.usamif.com DNS A record → 13.49.245.174
4. **Credentials:**
   - AWS Access Key (for Bedrock AI)
   - Email account credentials (career@usamif.com)

---

## 🎯 Initial Deployment (Run Once)

### Step 1: SSH into Server
```bash
ssh -i your-key.pem ubuntu@13.49.245.174
```

### Step 2: Download Setup Script
```bash
curl -o ec2-setup.sh https://raw.githubusercontent.com/Mahmoud-Elwazeer/E-Career/develop/deploy/ec2-setup.sh
chmod +x ec2-setup.sh
```

### Step 3: Run Setup
```bash
sudo bash ec2-setup.sh
```

**This will:**
- ✅ Install all dependencies (Python, Node.js, PostgreSQL, Redis, Nginx)
- ✅ Clone the repository from GitHub
- ✅ Set up PostgreSQL database
- ✅ Install Python packages
- ✅ Build React frontend
- ✅ Configure Nginx
- ✅ Start Gunicorn service
- ✅ Everything ready!

**Save the database password shown at the end!**

### Step 4: Configure Environment
```bash
sudo nano /var/www/usam/backend/.env
```

**Edit these values:**
```env
# AWS Bedrock (for AI features)
AWS_ACCESS_KEY_ID=your_actual_key
AWS_SECRET_ACCESS_KEY=your_actual_secret

# Email (career@usamif.com)
EMAIL_ACCOUNT_1_EMAIL=career@usamif.com
EMAIL_ACCOUNT_1_PASSWORD=your_gmail_app_password

# Encryption key (generate one)
FIELD_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Production settings
DEBUG=False
ALLOWED_HOSTS=jobs.usamif.com,13.49.245.174
```

### Step 5: Create Admin User
```bash
cd /var/www/usam/backend
/var/www/usam/venv/bin/python manage.py createsuperuser
```

### Step 6: Restart Services
```bash
sudo systemctl restart gunicorn-usam
sudo systemctl reload nginx
```

### Step 7: Setup SSL (After DNS is pointed)
```bash
sudo bash /var/www/usam/deploy/ssl-setup.sh
```

---

## 🔄 Update Deployment (When You Make Changes)

### From Your Local Machine:

1. **Make changes locally**
2. **Commit and push:**
   ```bash
   git add .
   git commit -m "fix: your changes"
   git push origin develop
   ```

3. **SSH into server:**
   ```bash
   ssh -i your-key.pem ubuntu@13.49.245.174
   ```

4. **Run deploy script:**
   ```bash
   cd /var/www/usam
   sudo bash deploy/deploy.sh
   ```

**This automatically:**
- ✅ Pulls latest code from GitHub
- ✅ Installs any new Python packages
- ✅ Runs database migrations
- ✅ Rebuilds React frontend
- ✅ Collects static files
- ✅ Restarts backend
- ✅ Reloads Nginx

**Both backend AND frontend updated in one command!** 🎉

---

## 📍 Access Points

After deployment:

- **Frontend:** https://jobs.usamif.com
- **API:** https://jobs.usamif.com/api/
- **Admin:** https://jobs.usamif.com/secret-admin-path/
- **Health Check:** https://jobs.usamif.com/health/

---

## 🔍 Troubleshooting

### Check Backend Status
```bash
sudo systemctl status gunicorn-usam
sudo journalctl -u gunicorn-usam -n 50 --no-pager
```

### Check Backend Logs
```bash
tail -f /var/www/usam/logs/gunicorn-error.log
```

### Check Nginx Status
```bash
sudo systemctl status nginx
sudo nginx -t
tail -f /var/log/nginx/usam_error.log
```

### Check Database
```bash
sudo -u postgres psql usam_db
# \dt  (list tables)
# \q   (quit)
```

### Restart Everything
```bash
sudo systemctl restart gunicorn-usam
sudo systemctl reload nginx
```

---

## 📦 Directory Structure on Server

```
/var/www/usam/
├── backend/
│   ├── apps/          (Django apps)
│   ├── config/        (Settings)
│   ├── .env          (Environment variables)
│   └── manage.py
├── frontend/
│   ├── src/          (React source)
│   └── dist/         (Built files - served by Nginx)
├── deploy/
│   ├── deploy.sh     (Update script)
│   └── nginx.conf    (Nginx config)
├── venv/             (Python virtual environment)
├── logs/             (Application logs)
├── media/            (User uploads)
└── staticfiles/      (Django static files)
```

---

## 🎯 Quick Commands Reference

```bash
# Deploy updates (most common)
cd /var/www/usam && sudo bash deploy/deploy.sh

# Restart backend
sudo systemctl restart gunicorn-usam

# View logs
tail -f /var/www/usam/logs/gunicorn-error.log

# Run Django commands
cd /var/www/usam/backend
/var/www/usam/venv/bin/python manage.py <command>

# Check site is running
curl https://jobs.usamif.com/health/
```

---

## ✅ Done!

Your E-Career platform is deployed on one server with automatic frontend + backend updates! 🚀
