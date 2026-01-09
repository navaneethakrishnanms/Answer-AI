# 🚀 Production Deployment Checklist

Complete checklist for deploying AI Exam Evaluator to production.

## Pre-Deployment Verification

### ✅ System Requirements

- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Ollama installed and configured
- [ ] Poppler installed for PDF processing
- [ ] Sufficient disk space (20GB+ for models)
- [ ] Sufficient RAM (16GB+ recommended)

### ✅ Model Installation

- [ ] `qwen2.5:14b` pulled and verified
- [ ] `deepseek-r1:7b-qwen-distill-q8_0` pulled and verified
- [ ] Models tested with sample data
- [ ] Model versions documented

### ✅ Configuration

- [ ] `.env` file created with production values
- [ ] `config.yaml` reviewed and customized
- [ ] OCR API key verified and tested
- [ ] Storage directories created
- [ ] Log directory configured

### ✅ Security

- [ ] API keys stored securely (not in code)
- [ ] Environment variables properly isolated
- [ ] CORS origins restricted to frontend domain
- [ ] File upload size limits configured
- [ ] Input validation implemented
- [ ] Rate limiting considered

### ✅ Testing

- [ ] Backend unit tests passed
- [ ] API endpoints tested
- [ ] OCR extraction tested with real PDFs
- [ ] Mapping validated with sample exams
- [ ] Evaluation verified with known answers
- [ ] End-to-end workflow tested
- [ ] Error handling verified

---

## Backend Deployment

### 1. Environment Setup

```powershell
# Production environment variables
OCR_API_KEY=<your-production-key>
OLLAMA_HOST=http://localhost:11434
MAPPING_MODEL=qwen2.5:14b
EVALUATION_MODEL=deepseek-r1:7b-qwen-distill-q8_0
UPLOAD_DIR=./uploads
RESULTS_DIR=./results
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
SECRET_KEY=<generate-secure-random-key>
```

### 2. Install Dependencies

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run Backend

**Option A: Direct (Development/Testing)**
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Option B: Gunicorn (Production - Linux)**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Option C: Windows Service**
Use `nssm` to run as Windows service

### 4. Backend Verification

- [ ] Health endpoint: `GET /health`
- [ ] API docs accessible: `/docs`
- [ ] Database initialized
- [ ] Logging working
- [ ] File uploads working
- [ ] Ollama connection verified

---

## Frontend Deployment

### 1. Build Frontend

```powershell
cd frontend
npm install
npm run build
```

### 2. Configure API URL

Create `.env.production`:
```
VITE_API_URL=http://your-backend-domain:8000
```

### 3. Deploy Frontend

**Option A: Static Hosting (Netlify, Vercel)**
- Upload `dist/` folder
- Configure API proxy if needed

**Option B: Nginx**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /path/to/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Option C: IIS (Windows)**
- Install IIS with URL Rewrite module
- Copy `dist/` to `C:\inetpub\wwwroot`
- Configure reverse proxy for `/api`

### 4. Frontend Verification

- [ ] UI loads correctly
- [ ] File upload works
- [ ] API calls successful
- [ ] Progress tracking works
- [ ] Results display correctly

---

## Database Setup

### SQLite (Default)

- [ ] Database file created: `evaluations.db`
- [ ] Tables initialized
- [ ] Backup strategy defined

### PostgreSQL (Production Alternative)

```powershell
# Update database.py
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/exam_evaluator"
```

---

## Monitoring & Logging

### 1. Configure Logging

Edit `config.yaml`:
```yaml
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/app.log"
```

### 2. Log Rotation

Use `logrotate` (Linux) or Task Scheduler (Windows)

### 3. Monitoring Points

- [ ] API response times
- [ ] OCR API usage
- [ ] Ollama model performance
- [ ] Disk usage (uploads/results)
- [ ] Database size
- [ ] Error rates

### 4. Alerts

Set up alerts for:
- API failures
- OCR API quota exceeded
- Disk space low
- Ollama connection issues

---

## Performance Optimization

### Backend

- [ ] Enable FastAPI async properly
- [ ] Configure workers (Gunicorn/Uvicorn)
- [ ] Implement caching where appropriate
- [ ] Optimize database queries
- [ ] Set appropriate timeouts

### OCR Service

- [ ] Configure parallel workers (default: 3)
- [ ] Adjust DPI if needed (default: 200)
- [ ] Monitor API rate limits
- [ ] Consider OCR API upgrade for higher limits

### Ollama

- [ ] Allocate sufficient GPU memory
- [ ] Configure model context length
- [ ] Set appropriate timeouts
- [ ] Monitor model performance

---

## Backup Strategy

### Daily Backups

- [ ] Database backup
- [ ] Uploaded files backup
- [ ] Results backup
- [ ] Configuration files backup

### Backup Script Example

```powershell
# backup.ps1
$date = Get-Date -Format "yyyyMMdd"
$backupDir = "C:\backups\exam_evaluator_$date"

New-Item -ItemType Directory -Path $backupDir

Copy-Item "evaluations.db" "$backupDir\"
Copy-Item -Recurse "uploads" "$backupDir\"
Copy-Item -Recurse "results" "$backupDir\"
Copy-Item ".env" "$backupDir\"
Copy-Item "app\config\config.yaml" "$backupDir\"

Write-Host "Backup completed: $backupDir"
```

---

## Security Hardening

### API Security

- [ ] Implement authentication (JWT tokens)
- [ ] Add rate limiting
- [ ] Validate all inputs
- [ ] Sanitize file uploads
- [ ] Set CORS properly
- [ ] Use HTTPS in production

### File Security

- [ ] Limit upload file sizes
- [ ] Validate PDF files
- [ ] Scan for malware
- [ ] Isolate upload directory
- [ ] Set appropriate permissions

### Environment Security

- [ ] Never commit `.env` to git
- [ ] Use secrets management (Azure Key Vault, AWS Secrets Manager)
- [ ] Rotate API keys regularly
- [ ] Use secure SECRET_KEY
- [ ] Restrict database access

---

## Disaster Recovery

### Recovery Time Objective (RTO)

Target: < 4 hours

### Recovery Point Objective (RPO)

Target: < 24 hours (daily backups)

### Recovery Steps

1. [ ] Restore database from backup
2. [ ] Restore uploaded files
3. [ ] Restore configuration files
4. [ ] Reinstall dependencies
5. [ ] Verify Ollama models
6. [ ] Test system functionality
7. [ ] Resume operations

---

## Maintenance Schedule

### Daily

- [ ] Check logs for errors
- [ ] Monitor disk space
- [ ] Verify backups completed

### Weekly

- [ ] Review API usage
- [ ] Check system performance
- [ ] Update dependencies if needed

### Monthly

- [ ] Review and archive old evaluations
- [ ] Check for security updates
- [ ] Performance optimization review

### Quarterly

- [ ] Full system audit
- [ ] Disaster recovery drill
- [ ] Model performance evaluation

---

## Scaling Considerations

### Horizontal Scaling

- [ ] Load balancer configuration
- [ ] Multiple backend instances
- [ ] Shared storage for uploads
- [ ] Centralized database
- [ ] Session management

### Vertical Scaling

- [ ] Increase RAM for Ollama
- [ ] Add GPU for faster inference
- [ ] Increase CPU cores
- [ ] Faster storage (SSD/NVMe)

---

## Documentation

- [ ] System architecture documented
- [ ] API documentation up to date
- [ ] Deployment procedures documented
- [ ] Troubleshooting guide created
- [ ] User manual available
- [ ] Admin procedures documented

---

## Training & Support

### Team Training

- [ ] Admin training completed
- [ ] User training completed
- [ ] Support team briefed
- [ ] Documentation reviewed

### Support Plan

- [ ] Support contact established
- [ ] Issue tracking system set up
- [ ] Escalation procedures defined
- [ ] Knowledge base created

---

## Go-Live Checklist

### Final Verification (1 week before)

- [ ] All tests passed
- [ ] Security audit completed
- [ ] Performance benchmarks met
- [ ] Backups verified
- [ ] Documentation complete
- [ ] Team trained

### Go-Live Day

- [ ] Final backup taken
- [ ] System deployed
- [ ] Smoke tests passed
- [ ] Monitoring active
- [ ] Support team ready
- [ ] Rollback plan ready

### Post Go-Live (First Week)

- [ ] Monitor closely for issues
- [ ] Gather user feedback
- [ ] Fix any critical bugs
- [ ] Optimize based on real usage
- [ ] Document lessons learned

---

## Success Metrics

### Performance

- API response time < 2 seconds
- Evaluation completion < 5 minutes
- Uptime > 99.5%

### Quality

- Mapping accuracy > 95%
- Evaluation consistency > 90%
- User satisfaction > 4/5

### Usage

- Daily evaluations processed
- Average processing time
- Error rate < 1%

---

## Contact & Escalation

### Level 1 Support
- **Email**: support@example.com
- **Response Time**: 4 hours

### Level 2 Support
- **Email**: tech-support@example.com
- **Response Time**: 2 hours

### Critical Issues
- **Phone**: +1-XXX-XXX-XXXX
- **Response Time**: Immediate

---

## Rollback Plan

### Rollback Trigger

Roll back if:
- Critical bugs discovered
- System instability
- Data integrity issues
- Security vulnerabilities

### Rollback Steps

1. [ ] Stop new evaluations
2. [ ] Complete in-progress jobs
3. [ ] Restore database backup
4. [ ] Deploy previous version
5. [ ] Verify functionality
6. [ ] Notify users
7. [ ] Investigate issue

---

## Sign-Off

### Deployment Approval

- [ ] Technical Lead: _________________ Date: _______
- [ ] Security Officer: ________________ Date: _______
- [ ] Operations Manager: _____________ Date: _______
- [ ] Project Sponsor: ________________ Date: _______

---

**Deployment Checklist Version**: 1.0.0  
**Last Updated**: January 2026  
**Status**: Production Ready ✅
