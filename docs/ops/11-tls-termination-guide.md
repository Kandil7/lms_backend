# TLS Termination Guide

This document outlines the TLS termination strategy for the LMS backend in production environments.

## 1. Overview

The LMS backend application runs on HTTP (port 8000) and relies on a reverse proxy for TLS termination. This approach provides:

- Centralized SSL/TLS management
- Modern cipher suite support
- HSTS header enforcement
- Load balancing capabilities
- DDoS protection

## 2. Recommended Reverse Proxy Solutions

### 2.1 Nginx (Self-hosted)

**Docker Compose Configuration:**
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "443:443"
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
    - ./certs:/etc/nginx/certs
  depends_on:
    - api
```

**nginx.conf example:**
```nginx
server {
    listen 80;
    server_name api.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    
    # Modern TLS settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers (reinforces app-level headers)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer" always;
    add_header Content-Security-Policy "frame-ancestors 'none'; object-src 'none'; base-uri 'self'" always;

    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 2.2 Traefik (Cloud-native)

**docker-compose.yml addition:**
```yaml
traefik:
  image: traefik:v3.0
  command:
    - --api.insecure=true
    - --providers.docker=true
    - --entrypoints.web.address=:80
    - --entrypoints.websecure.address=:443
    - --certificatesresolvers.myresolver.acme.tlschallenge=true
    - --certificatesresolvers.myresolver.acme.email=admin@example.com
    - --certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json
  ports:
    - "443:443"
    - "80:80"
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - ./letsencrypt:/letsencrypt
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.api.rule=Host(`api.example.com`)"
    - "traefik.http.routers.api.entrypoints=websecure"
    - "traefik.http.routers.api.tls.certresolver=myresolver"
    - "traefik.http.routers.api.middlewares=security-headers"
    - "traefik.http.middlewares.security-headers.headers.customresponseheaders.Strict-Transport-Security=max-age=31536000; includeSubDomains; preload"
    - "traefik.http.middlewares.security-headers.headers.customresponseheaders.X-Frame-Options=DENY"
    - "traefik.http.middlewares.security-headers.headers.customresponseheaders.X-Content-Type-Options=nosniff"
```

### 2.3 Cloud Load Balancer (Azure Front Door, GCP HTTPS LB, or equivalent)

Configure TLS termination at the load balancer level with:
- Azure Key Vault certificates (or equivalent managed certificates)
- Modern TLS policies (TLS 1.2+ only)
- HSTS header injection
- WAF integration for additional security

## 3. Certificate Management

### 3.1 Let's Encrypt (Recommended for self-hosted)
- Use Certbot for automated certificate renewal
- Configure DNS challenge for wildcard certificates
- Set up automatic renewal cron jobs

### 3.2 Commercial Certificates
- DigiCert, Sectigo, or other trusted CAs
- Wildcard certificates for multiple subdomains
- Extended Validation (EV) for maximum trust

## 4. Security Best Practices

### 4.1 Cipher Suites
Use modern cipher suites that prioritize:
- Forward secrecy (ECDHE, DHE)
- AEAD ciphers (AES-GCM, ChaCha20-Poly1305)
- Strong key exchange algorithms

### 4.2 HSTS Implementation
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- Submit to HSTS preload list for maximum browser protection
- Test with `curl -I https://api.example.com`

### 4.3 Vulnerability Scanning
- Regular SSL Labs testing (https://www.ssllabs.com/ssltest/)
- Monitor for vulnerabilities like Heartbleed, POODLE, etc.
- Keep OpenSSL and TLS libraries updated

## 5. Production Deployment Steps

1. **Certificate Acquisition**: Obtain TLS certificates
2. **Reverse Proxy Setup**: Configure Nginx/Traefik/cloud LB
3. **Security Headers**: Verify all security headers are present
4. **Testing**: Validate with SSL Labs and security scanners
5. **Monitoring**: Set up alerts for certificate expiration

## 6. Verification Commands

```bash
# Test TLS configuration
openssl s_client -connect api.example.com:443 -servername api.example.com | openssl x509 -text -noout

# Check security headers
curl -I https://api.example.com

# SSL Labs test
# Visit https://www.ssllabs.com/ssltest/analyze.html?d=api.example.com
```

## 7. Troubleshooting

### Common Issues:
- **Mixed content warnings**: Ensure all resources use HTTPS
- **Certificate errors**: Verify certificate chain and domain names
- **HSTS preload issues**: Test with `curl -I -H "Host: api.example.com" https://localhost` (with hosts file entry)

### Debugging:
- Enable detailed logging in reverse proxy
- Use Wireshark/tcpdump for TLS handshake analysis
- Check browser developer tools for security warnings
