# Enterprise MCP - Complete Deployment Guide

**Last Updated:** 2026-08-07  
**Status:** Ready for Production  
**Budget:** $0/month (using all free tiers)

---

## 📋 DEPLOYMENT ARCHITECTURE

```
┌──────────────────────────────────────────────┐
│  Vercel (Frontend Dashboard)                 │
│  https://enterprise-mcp-exp.vercel.app       │
└────────────┬─────────────────────────────────┘
             │ API Calls
             ▼
┌──────────────────────────────────────────────┐
│  Backend (Oracle Cloud OR Your Laptop)       │
│  http://backend.example.com                  │
│  - ASGI Server (Python)                      │
│  - Redis EventStore                          │
│  - Nginx Load Balancer                       │
└────────────┬─────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────┐
│  Supabase (Database)                         │
│  PostgreSQL + Auth + Realtime                │
└──────────────────────────────────────────────┘
```

---

## 🚀 STEP 1: VERCEL DEPLOYMENT (Frontend)

### 1A. Connect GitHub Repository

1. Go to https://vercel.com
2. Sign in with your GitHub account (divyamsingh4444)
3. Click "New Project"
4. Search for `enterprise-mcp-exp` repository
5. Click "Import"

### 1B. Configure Environment Variables

In Vercel dashboard, go to "Settings" → "Environment Variables":

```
NEXT_PUBLIC_API_URL=http://your-backend-url:8000
NEXT_PUBLIC_JAEGER_UI=http://your-jaeger-url:16686
```

### 1C. Deploy

1. Click "Deploy"
2. Wait for deployment (2-3 minutes)
3. Your frontend is live at: `https://enterprise-mcp-exp.vercel.app`

---

## 🗄️ STEP 2: SUPABASE SETUP (Database)

### 2A. Create Supabase Project

1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up (free tier)
4. Create new project:
   - Project name: `enterprise-mcp`
   - Database password: (save securely)
   - Region: (pick closest to you)

### 2B. Get Connection Details

After project creation:

1. Go to "Settings" → "Database"
2. Copy:
   - Host: `db.supabase.co`
   - Port: `5432`
   - Username: `postgres`
   - Password: (what you set)
   - Database: `postgres`

3. Go to "Settings" → "API"
4. Copy:
   - Project URL (SUPABASE_URL)
   - Anon Key (SUPABASE_KEY)

### 2C. Create Tables (Optional - for persistence)

In Supabase SQL editor, run:

```sql
-- Users table
CREATE TABLE users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  org_id VARCHAR(255) NOT NULL,
  scopes TEXT[] NOT NULL,
  created_at TIMESTAMP DEFAULT now()
);

-- Audit log
CREATE TABLE audit_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  subject VARCHAR(255),
  event_type VARCHAR(50),
  details JSONB,
  org_id VARCHAR(255),
  created_at TIMESTAMP DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX idx_users_org_id ON users(org_id);
CREATE INDEX idx_audit_log_org_id ON audit_log(org_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
```

### 2D. Update Your .env Files

Add to `config/.env.production`:

```
DATABASE_URL=postgresql://postgres:{password}@db.supabase.co:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

---

## 🖥️ STEP 3: BACKEND DEPLOYMENT

### OPTION A: Oracle Cloud (Recommended - FREE FOREVER)

#### 3A.1 Create Oracle Cloud Account

1. Go to https://www.oracle.com/cloud/free/
2. Click "Start for free"
3. Sign up (free tier includes 2 always-on VMs)

#### 3A.2 Create VM Instance

1. Go to Oracle Cloud Console
2. Click "Compute" → "Instances"
3. Click "Create Instance"
4. Configuration:
   - Image: Ubuntu 22.04 LTS
   - Shape: Ampere A1 Compute (free, 4 CPU, 24GB RAM)
   - Storage: 50GB (free)

#### 3A.3 Connect & Deploy

```bash
# SSH into your instance
ssh ubuntu@your-instance-ip

# Clone your repo
git clone https://github.com/divyamsingh4444/enterprise-mcp-exp.git
cd enterprise-mcp-exp

# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Add your user to docker group
sudo usermod -aG docker ubuntu

# Load environment
source config/.env.production

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

#### 3A.4 Setup Firewall

In Oracle Cloud Console:

1. Go to Networking → Virtual Cloud Networks
2. Click your VCN's Security List
3. Add ingress rule:
   - Protocol: TCP
   - Source: 0.0.0.0/0
   - Destination Port: 8000, 8080, 16686

#### 3A.5 Get Your Backend URL

Your backend will be at: `http://your-instance-ip:8080`

Update Vercel environment variable:
```
NEXT_PUBLIC_API_URL=http://your-instance-ip:8080
```

---

### OPTION B: Your Laptop (If Oracle Cloud Fails)

#### 3B.1 Prerequisites

```bash
# Install Docker
# Go to: https://docs.docker.com/install

# Install Docker Compose
docker-compose --version
```

#### 3B.2 Setup Port Forwarding

If behind router/firewall, use ngrok:

```bash
# Install ngrok
# https://ngrok.com/download

# Forward your backend
ngrok http 8080
# Returns: https://xxxx-xx-xxx-xxx-xx.ngrok.io
```

#### 3B.3 Start Backend Locally

```bash
cd /path/to/enterprise-mcp-exp
source config/.env.development
docker-compose up -d

# Logs
docker-compose logs -f
```

#### 3B.4 Update Vercel

If using ngrok:
```
NEXT_PUBLIC_API_URL=https://xxxx-xx-xxx-xxx-xx.ngrok.io
```

---

## ✅ VERIFICATION CHECKLIST

- [ ] GitHub repo created: https://github.com/divyamsingh4444/enterprise-mcp-exp
- [ ] GitHub Actions running (check Actions tab)
- [ ] Vercel project deployed: https://enterprise-mcp-exp.vercel.app
- [ ] Supabase project created with connection details
- [ ] Backend running (Oracle Cloud or laptop)
- [ ] Backend URL in Vercel environment variables
- [ ] Can access Jaeger UI: http://backend-url:16686
- [ ] Can call API from Vercel: Check browser console

---

## 🔐 SECURITY CHECKLIST

- [ ] MCP_SECRET_KEY is strong and unique
- [ ] Database password is NOT in git (use .env files)
- [ ] Supabase API key is restricted (anonymous key only)
- [ ] GitHub token is NOT in git
- [ ] Oracle Cloud firewall restricts ports appropriately
- [ ] TLS/HTTPS enabled for production (Vercel handles this)

---

## 🚨 TROUBLESHOOTING

### Backend won't start
```bash
# Check Docker
docker ps
docker-compose logs

# Check ports
netstat -tuln | grep 8080
```

### Vercel can't reach backend
```bash
# Test connectivity
curl http://backend-url:8000/health
```

### Database connection fails
```bash
# Test connection
psql -h db.supabase.co -U postgres -d postgres
```

---

## 📞 SUPPORT

For issues, check:
1. Vercel Deployment Logs: https://vercel.com/dashboard
2. Docker Logs: `docker-compose logs`
3. GitHub Actions: https://github.com/divyamsingh4444/enterprise-mcp-exp/actions

