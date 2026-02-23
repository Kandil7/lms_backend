# Logging Guide

This document outlines the logging strategy for the LMS backend in production environments.

## 1. Overview

The LMS backend uses structured JSON logging with the following requirements:
- **Format**: JSON format for machine readability
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Fields**: timestamp, level, message, module, function, line, request_id, user_id, correlation_id
- **Retention**: 90 days minimum for production

## 2. Current Logging Configuration

The application uses Python's built-in `logging` module with custom JSON formatter. Key configuration points:
- `app/core/logging.py` (if exists) or standard Python logging
- Structured logging for API requests and background tasks
- Request ID correlation for distributed tracing

## 3. Centralized Logging Solutions

### 3.1 ELK Stack (Elasticsearch, Logstash, Kibana)
**Architecture:**
```
LMS App → Filebeat → Logstash → Elasticsearch → Kibana
```

**Docker Compose Example:**
```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
  ports:
    - "9200:9200"

logstash:
  image: docker.elastic.co/logstash/logstash:8.12.0
  volumes:
    - ./ops/logging/logstash/pipeline:/usr/share/logstash/pipeline
  depends_on:
    - elasticsearch

kibana:
  image: docker.elastic.co/kibana/kibana:8.12.0
  ports:
    - "5601:5601"
  depends_on:
    - elasticsearch
```

### 3.2 Loki + Promtail + Grafana
**Architecture:**
```
LMS App → Promtail → Loki → Grafana
```

**Advantages:**
- Lightweight compared to ELK
- Native Grafana integration
- Cost-effective for large volumes
- Excellent for Kubernetes environments

### 3.3 Cloud Solutions
- **Azure Monitor Logs**: Integrated with Azure infrastructure
- **GCP Cloud Logging**: Integrated with GCP infrastructure  
- **Datadog**: Commercial solution with advanced analytics

## 4. Log Structure Requirements

### 4.1 Required Fields
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "message": "User logged in successfully",
  "module": "app.modules.auth.service",
  "function": "login_user",
  "line": 127,
  "request_id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
  "user_id": "uuid-123456",
  "correlation_id": "corr-abc123",
  "http_method": "POST",
  "http_path": "/api/v1/auth/login",
  "http_status": 200,
  "duration_ms": 125,
  "client_ip": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

### 4.2 Sensitive Data Handling
- Mask PII fields (emails, names, IDs) in logs
- Never log passwords, tokens, or secrets
- Use data scrubbing middleware
- Configure log redaction rules

## 5. Retention Policy

### 5.1 Production Retention
- **Critical logs** (errors, security events): 365 days
- **Application logs**: 90 days
- **Debug logs**: 7 days
- **Audit logs**: 365 days (compliance requirement)

### 5.2 Storage Optimization
- Index optimization for frequently queried fields
- Cold storage for older logs
- Automatic deletion policies
- Compression for archived logs

## 6. Implementation Steps

### 6.1 Application Configuration
1. Update logging configuration to include required fields
2. Add request ID correlation middleware
3. Implement structured JSON logging
4. Configure log levels per environment

### 6.2 Infrastructure Setup
1. Deploy centralized logging infrastructure
2. Configure log shipping agents (Filebeat, Promtail, etc.)
3. Set up index patterns and dashboards
4. Configure retention policies

### 6.3 Verification
1. Test log ingestion from LMS application
2. Verify structured fields are properly parsed
3. Test search and filtering capabilities
4. Validate retention policies

## 7. Security Considerations

### 7.1 Access Control
- Role-based access to log data
- Audit log access attempts
- Encryption at rest and in transit
- Network segmentation for logging infrastructure

### 7.2 Compliance Requirements
- GDPR: Right to be forgotten for user logs
- HIPAA: If handling health data
- PCI-DSS: If handling payment information
- SOC 2: Logging and monitoring requirements

## 8. Monitoring and Alerting

### 8.1 Log-Based Alerts
- High error rates (> 5% of requests)
- Security events (failed logins, unauthorized access)
- Performance issues (high latency, timeouts)
- System events (restarts, crashes)

### 8.2 Integration with Existing Systems
- Correlate logs with metrics and traces
- Unified alerting across observability stack
- Automated incident creation from critical logs

## 9. Documentation Requirements

- Logging architecture diagram
- Log field definitions and schema
- Retention policy documentation
- Access control procedures
- Incident response procedures for log analysis

## 10. Verification Commands

```bash
# Test log output format
curl -v http://localhost:8000/api/v1/health

# Check log shipping status
docker ps | grep filebeat
docker logs lms-filebeat

# Verify log indexing
curl -XGET 'http://localhost:9200/_cat/indices?v'
```

## 11. Troubleshooting

### Common Issues:
- **Logs not appearing**: Verify log shipper configuration and network connectivity
- **Structured parsing failed**: Check JSON format and field mappings
- **High disk usage**: Review retention policies and index optimization
- **Performance impact**: Reduce log verbosity or use async logging

### Debugging Steps:
- Check application logs for logging errors
- Verify log shipper connectivity to central system
- Test with sample log files
- Review parsing configurations and field mappings
