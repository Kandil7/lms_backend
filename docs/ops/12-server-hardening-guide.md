# Server Hardening Guide

This document outlines the server hardening requirements for LMS backend production environments.

## 1. Overview

Server hardening is essential for protecting the LMS infrastructure from unauthorized access and attacks. This guide covers OS-level, network-level, and service-level hardening.

## 2. Operating System Hardening

### 2.1 Patch Management
- Enable automatic security updates
- Schedule weekly patch reviews
- Test patches in staging before production deployment
- Maintain patch inventory and change logs

### 2.2 User Account Management
- Disable root login via SSH
- Use sudo for administrative tasks
- Implement least privilege principle
- Regularly review user accounts and permissions
- Enforce strong password policies (12+ characters, complexity requirements)

### 2.3 File System Security
- Set proper file permissions (644 for files, 755 for directories)
- Remove world-writable files and directories
- Use SELinux or AppArmor for mandatory access control
- Encrypt sensitive data at rest

## 3. Network Security

### 3.1 Firewall Configuration
**UFW (Ubuntu/Debian) Example:**
```bash
# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow essential services
sudo ufw allow ssh
sudo ufw allow 80/tcp    # HTTP (for redirect to HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 22/tcp    # SSH (restrict to admin IPs if possible)

# Rate limiting for SSH
sudo ufw limit ssh
```

**iptables (Advanced):**
```bash
# Rate limiting for SSH
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m limit --limit 3/min --limit-burst 3 -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -j DROP
```

### 3.2 SSH Hardening
**/etc/ssh/sshd_config:**
```conf
# Disable root login
PermitRootLogin no

# Use key-based authentication only
PasswordAuthentication no
PubkeyAuthentication yes

# Restrict protocols
Protocol 2

# Timeout settings
ClientAliveInterval 300
ClientAliveCountMax 3

# Limit users
AllowGroups ssh-users
# Or: AllowUsers deploy,admin

# Disable unused features
X11Forwarding no
TCPKeepAlive yes
UseDNS no
```

### 3.3 Fail2Ban Configuration
**/etc/fail2ban/jail.local:**
```ini
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 1h
findtime = 10m
```

## 4. Service Hardening

### 4.1 Docker Security
- Run containers as non-root users (already implemented in docker-compose.prod.yml)
- Use read-only filesystems where possible
- Limit container capabilities
- Regularly scan images for vulnerabilities
- Use Docker content trust for image signing

### 4.2 PostgreSQL Hardening
- Use strong passwords and rotate regularly
- Restrict database access to application servers only
- Enable SSL for database connections
- Configure pg_hba.conf for host-based authentication
- Monitor for suspicious queries and connections

### 4.3 Redis Hardening
- Set strong requirepass in redis.conf
- Bind to localhost only (or specific internal IPs)
- Disable dangerous commands (FLUSHDB, CONFIG, etc.)
- Use Redis ACL for fine-grained permissions
- Enable TLS for Redis connections

## 5. Monitoring and Logging

### 5.1 Log Collection
- Centralize logs using ELK stack, Loki, or cloud logging
- Retain logs for at least 90 days
- Monitor for security events (failed logins, unusual activity)
- Set up alerts for critical security events

### 5.2 Security Monitoring
- Install and configure OSSEC or Wazuh for intrusion detection
- Enable auditd for system call monitoring
- Monitor file integrity with AIDE or Tripwire
- Regular security scans with OpenVAS or Nessus

## 6. Production Deployment Checklist

### 6.1 Pre-deployment
- [ ] Verify firewall rules are configured correctly
- [ ] Confirm SSH hardening settings
- [ ] Validate fail2ban is running and configured
- [ ] Check OS patch levels
- [ ] Verify container security settings

### 6.2 Post-deployment
- [ ] Test security configurations
- [ ] Verify logging and monitoring setup
- [ ] Run vulnerability scan
- [ ] Document security configuration

## 7. Compliance Requirements

### 7.1 GDPR/Privacy Compliance
- Data encryption at rest and in transit
- Access controls and audit logging
- Data retention policies
- Right to be forgotten implementation

### 7.2 ISO 27001 Controls
- A.9.2.3: Manage privileged access rights
- A.12.4.1: Event logging
- A.13.1.1: Network controls
- A.14.2.1: Secure development policy

## 8. Verification Commands

```bash
# Check firewall status
sudo ufw status verbose

# Verify SSH configuration
sudo sshd -t

# Check fail2ban status
sudo systemctl status fail2ban
sudo fail2ban-client status

# Check running processes
ps aux | grep -E "(postgres|redis|uvicorn)"

# Verify file permissions
find /app -type f ! -perm 644 -exec ls -la {} \;
find /app -type d ! -perm 755 -exec ls -la {} \;
```

## 9. Emergency Response

### 9.1 Incident Response Plan
- Immediate containment procedures
- Forensic data collection
- Communication protocols
- Recovery procedures

### 9.2 Backup Security
- Encrypt backup files
- Store backups offsite
- Test restore procedures quarterly
- Verify backup integrity

## 10. Documentation Requirements

- Server hardening checklist completed and signed off
- Security configuration documentation
- Incident response procedures
- Regular security audit reports