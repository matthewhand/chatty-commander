# Security Configuration Guide

## 🚨 Critical Security Setup

This guide provides essential security configuration for ChattyCommander deployments.

### 1. Generate Secure Tokens

Before running the application, generate cryptographically secure tokens:

```bash
# Generate BEARER_TOKEN (32 bytes)
BEARER_TOKEN=$(openssl rand -hex 32)

# Generate BRIDGE_TOKEN (32 bytes)  
BRIDGE_TOKEN=$(openssl rand -hex 32)

echo "BEARER_TOKEN=$BEARER_TOKEN"
echo "BRIDGE_TOKEN=$BRIDGE_TOKEN"
```

### 2. Environment Configuration

Create a `.env` file with your secure tokens:

```bash
# Copy the template
cp .env.example .env

# Edit with your secure values
nano .env
```

Required environment variables:
- `BEARER_TOKEN`: API authentication token
- `BRIDGE_TOKEN`: Internal service communication token
- `CHATBOT_ENDPOINT`: Your API endpoint URL

### 3. Production Deployment Security

#### Authentication
- ✅ Authentication is **enabled by default** in production
- ❌ Never use `--no-auth` in production environments
- 🔐 Use strong, randomly generated tokens

#### Network Security
- 🌐 Use HTTPS in production (TLS/SSL certificates)
- 🔥 Configure firewall rules to restrict access
- 🚫 Expose only necessary ports (default: 8000)

#### Container Security
- 🐳 Run as non-root user (configured in Dockerfile)
- 📦 Use multi-stage builds to reduce attack surface
- 🔍 Regular security scanning of images

### 4. Security Headers

The application includes security headers by default:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` 
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (when using HTTPS)

### 5. Input Validation

All API endpoints include:
- ✅ JSON schema validation
- ✅ SQL injection prevention
- ✅ XSS protection
- ✅ Path traversal protection

### 6. Rate Limiting

Configure rate limiting in production:
```bash
# Example nginx configuration
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

server {
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://localhost:8000;
    }
}
```

### 7. Monitoring and Logging

Enable security monitoring:
- 📊 Access logs with IP addresses
- 🔍 Failed authentication attempts
- 🚨 Suspicious activity alerts
- 📈 Performance metrics

### 8. Regular Security Updates

- 🔄 Update dependencies regularly
- 🔎 Monitor security advisories
- 🛡️ Apply security patches promptly
- 🧪 Run security scans in CI/CD

## 🚨 Security Checklist

Before deploying to production:

- [ ] Generated secure random tokens
- [ ] Configured environment variables
- [ ] Enabled authentication (no `--no-auth`)
- [ ] Set up HTTPS/TLS
- [ ] Configured firewall rules
- [ ] Enabled security monitoring
- [ ] Tested security controls
- [ ] Reviewed access controls
- [ ] Updated all dependencies
- [ ] Created backup strategy

## 🛡️ Security Best Practices

### Development
- 🔐 Never commit secrets to version control
- 🧪 Use different tokens for dev/staging/prod
- 📝 Document security decisions
- 🔍 Regular security reviews

### Operations
- 🚀 Principle of least privilege
- 📊 Centralized logging
- 🚨 Incident response plan
- 🔄 Regular security audits

### Code Security
- 🛡️ Input validation on all endpoints
- 🔒 Secure authentication mechanisms
- 📋 Security-focused code reviews
- 🧪 Automated security testing

## 🚨 Incident Response

If you suspect a security breach:

1. **Immediate Actions**
   - Rotate all tokens and credentials
   - Review access logs
   - Isolate affected systems

2. **Investigation**
   - Analyze attack vectors
   - Assess data exposure
   - Document timeline

3. **Recovery**
   - Apply security patches
   - Update configurations
   - Monitor for suspicious activity

4. **Prevention**
   - Implement additional controls
   - Update security policies
   - Conduct security training

## 📞 Security Contact

Report security vulnerabilities to:
- 📧 Email: security@chattycommander.dev
- 🔒 Encrypted communications preferred
- ⏰ Response time: 48 hours

---

**Remember**: Security is an ongoing process, not a one-time setup. Regular reviews and updates are essential for maintaining a secure deployment.