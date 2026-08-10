# Enterprise MCP Server - Kubernetes Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Enterprise MCP Server to Kubernetes using production-ready manifests.

**Architecture:**
- 3 MCP server replicas (autoscaling 3-20)
- Redis StatefulSet for persistent caching
- Nginx Ingress for external access
- HPA for automatic scaling
- Network policies for security
- RBAC for access control

---

## Prerequisites

1. **Kubernetes Cluster** (1.24+)
   - Minimum: 3 nodes, 2 CPU cores each, 4GB RAM
   - Recommended: 3+ nodes for HA

2. **Tools**
   ```bash
   kubectl (v1.24+)
   kustomize (optional, for management)
   helm (optional)
   ```

3. **Ingress Controller**
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.0/deploy/static/provider/cloud/deploy.yaml
   ```

4. **Docker Image**
   - Build and push to registry:
   ```bash
   docker build -t your-registry/enterprise-mcp:latest .
   docker push your-registry/enterprise-mcp:latest
   ```

---

## Deployment Steps

### Step 1: Update Configuration

Edit `secret.yaml` with actual values:
```bash
# Generate a secure JWT secret
openssl rand -base64 32

# Get Supabase credentials
# Update DATABASE_URL, SUPABASE_URL, etc in secret.yaml
```

Edit `configmap.yaml` if needed:
```yaml
CORS_ORIGINS: "https://your-domain.com"
REDIS_URL: "redis://mcp-redis-service:6379"
```

### Step 2: Deploy to Kubernetes

**Option A: Using kubectl apply (Direct)**
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
```

**Option B: Using Kustomize (Recommended)**
```bash
# Ensure Docker image is updated in kustomization.yaml
kubectl apply -k k8s/
```

**Option C: Using Helm (Future)**
```bash
# Helm charts coming soon
helm install enterprise-mcp ./helm/mcp-server \
  --namespace mcp-system \
  --values values-prod.yaml
```

### Step 3: Verify Deployment

```bash
# Check namespace
kubectl get namespace mcp-system

# Check pods
kubectl get pods -n mcp-system
kubectl logs -n mcp-system -l app=enterprise-mcp

# Check services
kubectl get svc -n mcp-system

# Check HPA status
kubectl get hpa -n mcp-system

# Check ingress
kubectl get ingress -n mcp-system
```

### Step 4: Configure DNS

Point your domain to the Ingress LoadBalancer IP:
```bash
# Get external IP
kubectl get svc mcp-loadbalancer -n mcp-system

# Add DNS A record pointing to this IP
# mcp.example.com -> <EXTERNAL-IP>
```

### Step 5: Verify Health

```bash
# Direct pod access (port-forward)
kubectl port-forward -n mcp-system svc/mcp-service 8080:80

curl http://localhost:8080/health

# Via ingress (once DNS propagated)
curl https://mcp.example.com/health
```

---

## Autoscaling Configuration

The HPA is configured to scale based on:

1. **CPU Utilization**: Target 70%
2. **Memory Utilization**: Target 80%
3. **Custom Metrics**: Requests/second (requires metrics-server)

View current status:
```bash
kubectl get hpa -n mcp-system -w
kubectl describe hpa mcp-hpa -n mcp-system
```

Manual scaling (if needed):
```bash
kubectl scale deployment mcp-server -n mcp-system --replicas=5
```

---

## Monitoring & Observability

### Prometheus Metrics

Metrics exposed at `/metrics`:
```bash
kubectl port-forward -n mcp-system svc/mcp-service 9090:9090
curl http://localhost:9090/metrics
```

### Logs

View logs from all pods:
```bash
kubectl logs -n mcp-system -l app=enterprise-mcp -f

# Specific pod
kubectl logs -n mcp-system mcp-server-0 -f
```

### Pod Events

```bash
kubectl describe pod -n mcp-system <pod-name>
```

---

## Common Operations

### Rolling Update

The deployment uses `RollingUpdate` strategy by default:
```bash
# Update image (automatic)
kubectl set image deployment/mcp-server \
  -n mcp-system \
  mcp-server=your-registry/enterprise-mcp:v1.1.0

# Check rollout status
kubectl rollout status deployment/mcp-server -n mcp-system
```

### Rollback

```bash
kubectl rollout undo deployment/mcp-server -n mcp-system
kubectl rollout history deployment/mcp-server -n mcp-system
```

### Scale Up/Down

```bash
# Manual scaling
kubectl scale deployment mcp-server -n mcp-system --replicas=10

# Auto-scaling will take over after 5 minutes of stable load
```

### Update Configuration

```bash
# Edit ConfigMap
kubectl edit configmap mcp-config -n mcp-system

# Edit Secret
kubectl edit secret mcp-secrets -n mcp-system

# Restart pods to apply changes
kubectl rollout restart deployment/mcp-server -n mcp-system
```

---

## Troubleshooting

### Pods not starting?

```bash
# Check events
kubectl describe pod -n mcp-system <pod-name>

# Check logs
kubectl logs -n mcp-system <pod-name>

# Check resource availability
kubectl top nodes
kubectl top pods -n mcp-system
```

### Service not accessible?

```bash
# Check endpoints
kubectl get endpoints -n mcp-system

# Check ingress
kubectl get ingress -n mcp-system
kubectl describe ingress mcp-ingress -n mcp-system

# Check LoadBalancer
kubectl get svc mcp-loadbalancer -n mcp-system
```

### Redis connection issues?

```bash
# Check Redis pod
kubectl logs -n mcp-system mcp-redis-0

# Test connection from MCP pod
kubectl exec -it -n mcp-system <mcp-pod-name> -- redis-cli -h mcp-redis-service ping
```

---

## Security

### Network Policies
Configured in `network-policy.yaml`:
- Ingress traffic only from Ingress controller
- Egress to Redis, DNS, external services

### RBAC
ServiceAccount with minimal permissions:
- Read ConfigMaps, Secrets
- List Pods, Services, Endpoints
- No write permissions

### Pod Security
- Non-root user (UID 1000)
- Read-only root filesystem (except /tmp)
- Resource limits
- Security context

---

## Backup & Recovery

### Redis Data Backup
```bash
# Exec into Redis pod
kubectl exec -it -n mcp-system mcp-redis-0 -- bash

# Create backup
redis-cli --rdb /tmp/backup.rdb

# Extract backup
kubectl cp mcp-system/mcp-redis-0:/tmp/backup.rdb ./backup.rdb
```

### Namespace Backup
```bash
# Backup all manifests
kubectl get all -n mcp-system -o yaml > mcp-backup.yaml

# Restore
kubectl apply -f mcp-backup.yaml
```

---

## Production Checklist

- [ ] Update secret.yaml with production credentials
- [ ] Update ingress hostname (mcp.example.com)
- [ ] Configure DNS records
- [ ] Update Docker image to your registry
- [ ] Configure cert-manager for HTTPS
- [ ] Set up metrics-server for HPA
- [ ] Configure Prometheus scraping
- [ ] Set up log aggregation (ELK, Loki)
- [ ] Test failover (kill pod, verify restart)
- [ ] Test autoscaling under load
- [ ] Backup Redis data
- [ ] Document runbooks
- [ ] Set up monitoring alerts

---

## Resource Requirements

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|------------|-----------|-----------------|--------------|
| MCP Server | 250m | 500m | 256Mi | 512Mi |
| Redis | 100m | 250m | 256Mi | 512Mi |

---

## Helpful Commands

```bash
# Watch pod status
kubectl get pods -n mcp-system -w

# Stream logs
kubectl logs -n mcp-system -l app=enterprise-mcp -f

# Debug pod
kubectl debug pod/<pod-name> -n mcp-system -it -- sh

# Port forward
kubectl port-forward -n mcp-system svc/mcp-service 8080:80

# Exec into pod
kubectl exec -it -n mcp-system <pod-name> -- sh

# Get resource usage
kubectl top pods -n mcp-system
```

---

## Next Steps

1. Deploy to development Kubernetes cluster
2. Run load tests (see testing guide)
3. Configure monitoring and alerting
4. Set up CI/CD pipeline for automated deployments
5. Document operational runbooks

---

**For questions or issues, refer to the main README.md or GitHub issues.**
