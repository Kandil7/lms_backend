# Server Hardening Guide for LMS Production Deployment

This document provides comprehensive server hardening guidelines for deploying the LMS backend in production environments.

## 1. Operating System Hardening

### 1.1 OS Patching
- Enable automatic security updates
- Apply patches within 24 hours of critical CVE releases
- Maintain patch inventory and verification logs

### 1.2 User Account Management
- Disable root login via SSH
- Use key-based authentication only (no password authentication)
- Implement least privilege principle for service accounts
- Regularly review and rotate service account credentials

### 1.3 File System Security
- Set proper file permissions (600 for secrets, 644 for configs)
- Use immutable filesystem attributes where possible
- Enable SELinux/AppArmor for additional process isolation

## 2. Network Security

### 2.1 Firewall Configuration
```
# Allow only required ports
iptables -A INPUT -p tcp --dport 22 -s <admin-ip-range> -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 6379 -s <internal-network> -j ACCEPT
iptables -A INPUT -p tcp --dport 5432 -s <internal-network> -j ACCEPT
iptables -A INPUT -j DROP
```

### 2.2 SSH Hardening
```bash
# /etc/ssh/sshd_config
Port 2222
Protocol 2
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowTcpForwarding no
ClientAliveInterval 300
ClientAliveCountMax 3
```

### 2.3 Network Segmentation
- Separate database, cache, and application tiers
- Use private subnets for internal services
- Implement VPC peering for multi-cloud deployments

## 3. Application Security

### 3.1 Container Security
- Run containers as non-root user (nobody:nogroup)
- Use read-only filesystems where possible
- Implement seccomp and AppArmor profiles
- Scan container images for vulnerabilities

### 3.2 API Security
- Enforce rate limiting on all endpoints
- Implement proper input validation and sanitization
- Use parameterized queries to prevent SQL injection
- Validate and sanitize all user inputs

### 3.3 Authentication & Authorization
- Enforce MFA for administrative access
- Implement account lockout after 5 failed attempts
- Use short-lived JWT tokens with proper refresh mechanisms
- Implement proper session management and timeout

## 4. Monitoring and Logging

### 4.1 Log Collection
- Centralize logs to SIEM system
- Retain logs for at least 90 days
- Include audit trails for sensitive operations
- Monitor for suspicious patterns and anomalies

### 4.2 Security Monitoring
- Alert on failed login attempts
- Monitor for unusual API request patterns
- Track data exfiltration attempts
- Implement anomaly detection for user behavior

## 5. Compliance Requirements

### 5.1 GDPR Compliance
- Implement data subject rights (access, deletion, portability)
- Conduct regular data protection impact assessments
- Maintain records of processing activities
- Implement appropriate technical and organizational measures

### 5.2 HIPAA Compliance (if handling PHI)
- Implement encryption at rest and in transit
- Conduct regular risk assessments
- Implement access controls and audit logging
- Sign business associate agreements

## 6. Verification Checklist

### Pre-Deployment Verification
- [ ] OS patches applied and verified
- [ ] Firewall rules configured and tested
- [ ] SSH hardening implemented and verified
- [ ] Container security policies applied
- [ ] Rate limiting configured and tested
- [ ] Secret management validated
- [ ] TLS configuration verified
- [ ] Logging and monitoring enabled

### Post-Deployment Verification
- [ ] Security scanning completed with no high/critical findings
- [ ] Penetration testing performed
- [ ] Vulnerability assessment completed
- [ ] Incident response procedures tested
- [ ] Backup and restore procedures validated

## 7. Tools and References

### Security Scanning Tools
- `pip-audit` - Python dependency vulnerability scanning
- `bandit` - Python static security analysis
- `gitleaks` - Secret detection in source code
- `trivy` - Container image vulnerability scanning
- `nmap` - Network security scanning

### Compliance Frameworks
- NIST SP 800-53 - Security and Privacy Controls
- CIS Benchmarks - Secure configuration guidelines
- OWASP Top 10 - Web application security risks
- ISO 27001 - Information security management

## 8. Emergency Response

### Immediate Actions for Security Incidents
1. Isolate affected systems
2. Preserve evidence and logs
3. Notify incident response team
4. Contain the breach
5. Eradicate threat
6. Recover systems
7. Post-incident review

### Contact Information
- Security Team: security@yourcompany.com
- 24/7 Incident Response: +1-555-SECURITY
- SOC Operations: soc@yourcompany.com

## Appendix A: Sample Hardening Script

```bash
#!/bin/bash
# Server hardening script for LMS production deployment

set -e

echo "Starting server hardening..."

# 1. Update system
apt-get update && apt-get upgrade -y

# 2. Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow 2222/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow from 10.0.0.0/8 to any port 6379 proto tcp
ufw allow from 10.0.0.0/8 to any port 5432 proto tcp
ufw enable

# 3. Harden SSH
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#*Port.*/Port 2222/' /etc/ssh/sshd_config
systemctl restart ssh

# 4. Create non-root user for application
useradd -r -s /usr/sbin/nologin lms-app

# 5. Set file permissions
chown -R root:root /etc/lms/
chmod 600 /etc/lms/*.conf
chmod 644 /etc/lms/*.yaml

echo "Server hardening completed successfully."
```

**Note**: Adapt this script for your specific environment and requirements.