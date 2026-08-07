# Enterprise MCP - Quick Start Guide

**Total Setup Time:** 20-30 minutes  
**Total Cost:** $0/month (all free tiers)

---

## ⚡ 5-MINUTE SETUP

### 1. GitHub & GitHub Actions (5 min)
✅ Already done! Your repo is ready at:
```
https://github.com/divyamsingh4444/enterprise-mcp-exp
```

Automated testing runs on every push via GitHub Actions.

---

## 🚀 20-MINUTE DEPLOYMENT

### STEP 1: Deploy Frontend to Vercel (5 min)

```bash
1. Go to: https://vercel.com
2. Sign in with GitHub (divyamsingh4444)
3. Click "New Project"
4. Select: enterprise-mcp-exp
5. Click "Deploy"
6. Wait 2-3 minutes...
7. Your frontend is at: https://enterprise-mcp-exp.vercel.app
```

### STEP 2: Create Supabase Database (5 min)

```bash
1. Go to: https://supabase.com
2. Sign up (free tier)
3. Create project: "enterprise-mcp"
4. Save credentials:
   - SUPABASE_URL
   - SUPABASE_KEY
   - DATABASE_URL
```

### STEP 3: Deploy Backend (10 min)

**BEST OPTION: Oracle Cloud (FREE)**

```bash
1. Sign up: https://www.oracle.com/cloud/free/
2. Create Ubuntu 22.04 VM (Always Free tier)
3. SSH into VM:
   ssh ubuntu@your-instance-ip

4. Clone & deploy:
   git clone https://github.com/divyamsingh4444/enterprise-mcp-exp.git
   cd enterprise-mcp-exp
   sudo apt-get install docker.io docker-compose
   source config/.env.production
   docker-compose up -d

5. Your backend is at: http://your-instance-ip:8080
```

**FALLBACK OPTION: Your Laptop**

```bash
# Install Docker: https://docs.docker.com/install

# Start backend:
cd enterprise-mcp-exp
source config/.env.development
docker-compose up -d

# Use ngrok for remote access:
ngrok http 8080
# Get URL like: https://xxxx-xx-xxx-xxx-xx.ngrok.io
```

---

## ✅ VERIFICATION

After all 3 steps:

```bash
# Test backend
curl http://your-backend-url:8080/health

# Test frontend
Open: https://enterprise-mcp-exp.vercel.app

# View traces
Open: http://your-backend-url:16686 (Jaeger)
```

---

## 📚 NEXT STEPS

1. **Read full guide:** See `DEPLOYMENT_GUIDE.md`
2. **Configure environment variables** in Vercel dashboard
3. **Test OAuth flow:** Create user at `/auth/signup`
4. **Run a tool:** Use `/api/v1/mcp/tools/call`
5. **Monitor traces:** Check Jaeger UI

---

## 💡 QUICK REFERENCE

| Component | Status | URL |
|-----------|--------|-----|
| GitHub | ✅ Ready | https://github.com/divyamsingh4444/enterprise-mcp-exp |
| Frontend | ⏳ Deploy now | https://enterprise-mcp-exp.vercel.app |
| Backend | ⏳ Deploy now | http://your-backend-url:8080 |
| Database | ⏳ Create now | https://supabase.com |
| Jaeger | ⏳ Auto-running | http://your-backend-url:16686 |

---

## 🆘 STUCK?

1. Backend won't start? → Check Docker: `docker ps`
2. Vercel won't connect? → Test: `curl http://backend:8080/health`
3. Database error? → Check credentials in `.env`
4. More help? → See `DEPLOYMENT_GUIDE.md`

