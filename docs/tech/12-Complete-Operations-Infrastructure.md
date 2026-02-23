# Complete Operations and Infrastructure Guide

This comprehensive guide covers all operational aspects of the LMS Backend including infrastructure configuration, Docker deployment, monitoring, backup and restore procedures, security hardening, and production support workflows. This documentation is essential for DevOps engineers, system administrators, and developers responsible for maintaining the application in production environments.

---

## Infrastructure Architecture Overview

The LMS Backend employs a containerized architecture using Docker Compose for orchestration. This approach provides consistency between development and production environments while simplifying deployment and scaling operations. The infrastructure is designed around a modular monolith pattern where all application components run within a unified codebase but are logically separated into distinct services.

### Core Components

The infrastructure consists of several interconnected components that work together to provide a complete learning management system. Understanding these components and their relationships is essential for effective operations and troubleshooting.

The API service is the core FastAPI application that handles all HTTP requests. It exposes the RESTful API endpoints for client applications and handles authentication, authorization, and business logic execution. The API service is horizontally scalable and can be replicated to handle increased load. Multiple worker processes within each container utilize available CPU cores efficiently.

PostgreSQL serves as the primary data store, holding all application data including users, courses, enrollments, quiz questions, and certificates. The database is configured with connection pooling to efficiently handle concurrent requests. For production, a managed PostgreSQL service provides automatic backups, high availability, and automatic minor version upgrades.

Redis fulfills multiple roles in the architecture. It serves as the caching layer for frequently accessed data, reducing database load and improving response times. Redis also acts as the message broker for Celery, enabling asynchronous task processing. Additionally, Redis stores rate limiting counters and session data, providing distributed state across API instances.

Celery workers process background tasks asynchronously, including sending emails, updating progress metrics, generating certificates, and delivering webhooks. Using separate queues for different task types allows independent scaling of worker pools based on workload characteristics. The Celery beat scheduler handles periodic tasks like cleanup jobs and scheduled notifications.

The Caddy reverse proxy handles TLS termination, static file serving, and request routing. Caddy's automatic HTTPS configuration simplifies certificate management by obtaining and renewing certificates from Let's Encrypt. The reverse proxy also adds security headers and provides gzip compression for improved performance.

### Service Communication

Services communicate through well-defined interfaces over the Docker internal network. The API service connects to PostgreSQL and Redis using service names as hostnames. Celery workers connect to Redis for message consumption and PostgreSQL for data access. Caddy forwards external HTTP traffic to the API service.

External connections are limited to the Caddy reverse proxy on ports 80 and 443. Database and Redis services are not exposed externally, preventing direct external access to sensitive data stores. This network architecture provides security through network isolation while maintaining necessary connectivity.

---

## Docker Configuration Files

The project includes multiple Docker Compose configuration files optimized for different deployment scenarios. Each file includes specific configurations for the target environment while maintaining consistency in the overall architecture.

### Development Configuration (docker-compose.yml)

The development configuration provides a complete development environment with all services needed for local development. This configuration prioritizes developer productivity with features like hot reload, verbose logging, and convenient service exposure.

The API service uses the local source code through volume mounting, enabling hot reload when files change. The command includes --reload flag for uvicorn, automatically restarting the server on code changes. Debug logging is enabled to aid troubleshooting during development.

The PostgreSQL service uses the postgres:16-alpine image for a lightweight database instance. Environment variables configure the default database, user, and password. A volume mount persists database data between restarts, preserving development data.

The Redis service uses redis:7-alpine for a minimal Redis footprint. The redis-server command includes persistence configuration with periodic snapshots for data safety.

Celery services (worker and beat) include the --reload flag in development, automatically restarting when code changes. All Celery task modules are imported at startup, enabling auto-discovery of tasks defined in the application.

### Production Configuration (docker-compose.prod.yml)

The production configuration optimizes for reliability, security, and performance. Several key differences distinguish it from the development configuration.

Security hardening includes running containers as non-root users (nobody). The API container drops all capabilities and runs with minimal privileges. File system read-only mounts are used where possible to prevent container compromise.

Health checks are configured for all services, enabling container orchestration to detect failures and replace unhealthy containers automatically. The API service health check verifies the readiness endpoint returns successfully. Database and Redis services use built-in health check commands.

Resource limits prevent any single service from consuming excessive resources. The API service is limited to specified CPU and memory allocations. Workers have appropriate limits based on expected workload.

The migrate service runs as an init container that executes database migrations before the API service starts. This ensures the database schema is always up to date with the deployed application version.

External service dependencies configure the production stack to use managed services for database and Redis. The PROD_DATABASE_URL and PROD_REDIS_URL environment variables point to external services, allowing the Docker stack to be ephemeral and stateless.

### Staging Configuration (docker-compose.staging.yml)

The staging configuration provides a middle ground between development and production. It uses production-like architecture with staging-specific configuration values.

Debug mode may be enabled in staging to facilitate troubleshooting of issues that cannot be reproduced in development. This makes staging useful for debugging production issues in a controlled environment.

The staging configuration typically uses separate database and Redis instances from production, preventing staging activities from affecting production data or performance.

### Observability Configuration (docker-compose.observability.yml)

The observability stack provides monitoring and alerting capabilities. This separate configuration allows the observability stack to be deployed independently from the application stack.

Prometheus collects metrics from the application and other services. The configuration includes scrape targets for the API metrics endpoint and alerting rule files.

Grafana provides visualization dashboards for metrics and alerts. Default dashboards are imported at startup, providing immediate visibility into system health and performance.

Alertmanager handles alert routing, deduplication, and notification delivery. Alert configurations define conditions that trigger notifications to appropriate channels.

---

## Caddy Reverse Proxy Configuration

The Caddyfile in ops/caddy/ defines the reverse proxy configuration for production deployments. This configuration handles TLS, routing, security headers, and compression.

### TLS Configuration

Caddy automatically obtains TLS certificates from Let's Encrypt using the email address configured via LETSENCRYPT_EMAIL environment variable. The acme_ca directive specifies the production Let's Encrypt directory. For testing, this can be changed to the staging directory.

The {$APP_DOMAIN} placeholder is replaced with the APP_DOMAIN environment variable at runtime. This allows the same configuration to be used across different deployments with different domain names.

### Security Headers

The header directive adds recommended security headers to all responses. X-Content-Type-Options with nosniff prevents browsers from MIME-type sniffing. X-Frame-Options with DENY prevents clickjacking attacks. X-XSS-Protection enables XSS filtering in older browsers. Referrer-Policy controls referrer information sent with requests. Strict-Transport-Security enforces HTTPS and prevents protocol downgrade attacks.

### Request Routing

The reverse_proxy directive forwards requests to the API service. The api:8000 hostname refers to the API service on the Docker network. Health checks ensure requests are only forwarded to healthy API instances.

The encode directive enables gzip and zstd compression, reducing response sizes and improving transfer speeds. Compression is particularly beneficial for JSON API responses.

---

## Database Operations

Effective database operations are critical for application reliability and data safety. This section covers database configuration, connection management, backup and restore procedures.

### Connection Pool Configuration

The application configures SQLAlchemy with connection pooling appropriate for the workload. The DB_POOL_SIZE setting controls the number of connections maintained in the pool. The DB_MAX_OVERFLOW setting allows additional connections beyond the pool size during peak load.

For production PostgreSQL, the pool size should match the number of worker processes per API instance, multiplied by the number of API instances. Start with pool_size=20 and max_overflow=40 as reasonable defaults for moderate load.

The pool_pre_ping setting enables connection health checks before use, preventing errors from stale connections that were closed by the database server.

### Backup Procedures

Regular database backups are essential for disaster recovery. The project includes scripts for automated backup creation.

The backup_db.bat script creates a PostgreSQL backup using pg_dump. Backups are stored in the backups/db/ directory with timestamped filenames (lms_YYYYMMDD_HHMMSS.dump). The script can be run manually or scheduled using Windows Task Scheduler.

For Azure managed PostgreSQL, use the automated backup features provided by Azure Database for PostgreSQL. Configure backup retention period based on recovery point objectives. Azure provides point-in-time restore capability with configurable retention.

For cross-region disaster recovery, configure read replicas in a different region. Replica lag monitoring ensures replication is functioning correctly. In case of primary region failure, promote the replica to become the new primary.

### Restore Procedures

Database restore procedures should be tested regularly to ensure backups are valid and recovery processes work correctly.

The restore_db.bat script restores from a backup file. The --yes flag enables non-interactive mode for automation. Restore operations require exclusive access to the database, so ensure the application is stopped before restoring.

Restore drills validate backup integrity and recovery procedures. Schedule regular restore drills (recommended weekly) to practice recovery and verify backup quality. Use the setup_restore_drill_task.ps1 script to schedule automated weekly restore drills.

### Point-in-Time Recovery

For Azure Database for PostgreSQL, point-in-time recovery allows restoring to any point within the retention period. This is valuable for recovering from accidental data deletion or application bugs that corrupt data.

To perform point-in-time recovery, create a new database server restored from the source server at the desired point in time. Then migrate applications to point to the restored server.

---

## Redis Operations

Redis serves multiple purposes in the architecture, requiring appropriate configuration for each use case.

### Persistence Configuration

Redis persistence ensures data survives restarts. The redis-server command in docker-compose files includes --save 60 1, creating an RDB snapshot every 60 seconds if at least one key changed. This provides reasonable durability with minimal performance impact.

For production with critical data like rate limiting, consider enabling AOF (Append-Only File) persistence in addition to RDB snapshots. Configure appendonly yes and appendfsync everysec for good durability with acceptable performance.

### Memory Management

Monitor Redis memory usage to prevent memory exhaustion. The maxmemory setting limits Redis memory usage. The maxmemory-policy setting determines eviction policy when memory limit is reached.

For rate limiting data, eviction is acceptable as lost data simply requires users to wait before retrying. For session data, consider persistence requirements and appropriate eviction policies.

### Clustering Considerations

For production with high availability requirements, Redis Cluster or managed Redis with replication provides automatic failover. Azure Cache for Redis Premium tier provides built-in clustering and replication.

When using Redis Cluster, the application must use cluster-aware client libraries. The current application uses redis-py which supports cluster mode with appropriate connection configuration.

---

## Background Task Processing

Celery provides asynchronous task processing for operations that do not require immediate completion. Proper configuration and monitoring of Celery ensures reliable background job execution.

### Task Queue Architecture

The application defines multiple queues for different task types, enabling independent scaling and priority handling. The emails queue handles transactional emails including welcome messages, password resets, and notifications. The progress queue handles enrollment progress updates and completion tracking. The certificates queue handles PDF certificate generation. The webhooks queue handles external event notifications.

The task_routes configuration in celery_app.py maps task modules to specific queues. This separation ensures email delivery is not affected by certificate generation load, and vice versa.

### Worker Configuration

Celery workers are configured for reliability and performance. The worker_prefetch_multiplier=1 setting ensures workers fetch one task at a time, providing fair distribution across multiple workers. This setting prevents a single worker from grabbing many tasks while others remain idle.

Task acknowledgment (task_acks_late=True) ensures tasks are acknowledged only after processing completes. This prevents task loss if workers crash during processing. The task_reject_on_worker_lost=True setting ensures tasks are requeued if workers crash.

Time limits prevent stuck tasks from blocking workers indefinitely. The task_time_limit=300 setting (hard limit) kills tasks exceeding 5 minutes. The task_soft_time_limit=240 setting (soft limit) allows tasks to handle cleanup before the hard limit.

### Monitoring Celery

Monitor Celery workers to ensure tasks are processing correctly. Flower provides a web-based monitor for Celery. The flower package can be added to the observability stack for task monitoring.

Key metrics to monitor include queue length (growing queues indicate processing delays), task success and failure rates, task execution duration, and worker status (active workers should match configured count).

---

## Monitoring and Observability

Comprehensive monitoring enables proactive identification and faster resolution of issues. The observability stack provides metrics, logs, and alerts for the entire system.

### Metrics Collection

The application exposes Prometheus-compatible metrics at the /metrics endpoint (configurable via METRICS_PATH). Metrics include HTTP request counts by endpoint and status code, HTTP request duration histograms, Celery task counts by type and status, and custom application metrics for business events.

Prometheus scrapes these metrics at regular intervals (default 15 seconds). The prometheus.yml configuration defines scrape targets and intervals. Configure longer scrape intervals (30-60 seconds) for smaller deployments to reduce overhead.

### Grafana Dashboards

Grafana dashboards provide visual representation of system health and performance. Key dashboards include API performance showing request rates, response times, and error rates. Database performance displays query times, connection usage, and replication lag. Redis performance shows memory usage, commands per second, and keyspace metrics. Celery performance displays queue depths, task processing rates, and worker status.

Import dashboards from the ops/observability/grafana directory or create custom dashboards based on available metrics.

### Alerting Configuration

Prometheus alerting rules define conditions that should trigger notifications. The alerts.yml file includes alerts for high error rates (more than 5% errors in 5 minutes), high latency (p99 response time exceeds 5 seconds), service down (API or database health checks fail), and queue backlog (queue length exceeds threshold for extended period).

Alertmanager handles alert routing and notification. Configure receivers for email, Slack, PagerDuty, or other notification channels. Use alert routing to ensure relevant teams receive appropriate alerts.

---

## Security Hardening

Production deployments require security hardening to protect against common threats. This section covers essential security configurations and best practices.

### Network Security

Restrict network access to production services. The production Docker configuration does not expose database or Redis ports externally. All external traffic routes through Caddy on ports 80 and 443.

Configure firewall rules to allow only necessary traffic. If deploying on cloud infrastructure, use security groups or network ACLs to restrict access to management ports (SSH) and the application ports (80, 443).

Enable TLS for all external connections. Caddy automatically handles TLS certificate management. Ensure strong TLS configurations (TLS 1.2 minimum, TLS 1.3 preferred) and disable weak cipher suites.

### Application Security

Disable debug mode in production (DEBUG=false). Debug mode exposes sensitive information in error responses and can provide attackers with valuable system information.

Configure strong JWT secrets (SECRET_KEY with 64+ random characters). Rotate secrets periodically and have a plan for secret rotation without service interruption.

Implement rate limiting to prevent abuse. The application includes rate limiting with configurable thresholds. Adjust limits based on expected traffic patterns and acceptable latency.

Enable security headers through the SecurityHeadersMiddleware. These headers protect against common web vulnerabilities including XSS, clickjacking, and MIME sniffing.

### Data Security

Encrypt data at rest for database and file storage. Azure Database for PostgreSQL provides transparent data encryption. Use Azure Storage encryption for blob storage.

Encrypt data in transit using TLS for all connections. The application configuration should enforce TLS 1.2 or higher for all external communications.

Implement proper access controls for database credentials. Use strong passwords or service principals. Rotate credentials regularly and after any potential compromise.

---

## Scaling Considerations

Planning for scaling ensures the application can handle growth in users and traffic. This section covers horizontal and vertical scaling strategies.

### Horizontal Scaling

The API service is horizontally scalable. Add more API containers by increasing the replica count in Docker Compose or orchestrator configuration. A load balancer distributes requests across instances.

Session state is stored in Redis, enabling sticky sessions or round-robin load balancing without session loss. Rate limiting state is also Redis-backed, maintaining consistent limits across instances.

Database connection pooling should be configured to handle the total number of connections from all API instances. With N API instances each with pool_size=M, the database must support N×M connections.

### Vertical Scaling

Vertical scaling involves increasing resource allocation to existing services. Monitor resource utilization to identify scaling needs. Common vertical scaling actions include increasing API container memory for larger caches, adding vCPUs to database server for faster query processing, and increasing Redis memory for larger caches.

### Database Scaling

For read-heavy workloads, implement read replicas to distribute query load. The application can be configured to send read queries to replicas. For write-heavy workloads, consider partitioning strategies or sharding.

Connection poolers like PgBouncer can reduce database connection overhead when scaling horizontally. PgBouncer maintains a pool of database connections shared across application instances.

---

## Disaster Recovery

Disaster recovery planning ensures business continuity in case of catastrophic failures. This section outlines recovery procedures and testing requirements.

### Recovery Objectives

Define recovery objectives based on business requirements. The Recovery Time Objective (RTO) defines the maximum acceptable downtime. The Recovery Point Objective (RPO) defines the maximum acceptable data loss measured in time.

For the LMS Backend, typical objectives might include RTO of 4 hours and RPO of 1 hour. This means the system should be restored within 4 hours of failure, with maximum 1 hour of data loss.

### Backup Strategy

Implement a layered backup strategy for comprehensive protection. Daily automated backups using pg_dump or managed service backups provide baseline protection. Transaction log shipping enables point-in-time recovery within the retention period. Cross-region backups ensure survival of regional failures.

Store backups securely with appropriate access controls. Encrypt backup files and store encryption keys separately from backup data. Test backup restoration regularly to verify backup integrity.

### Failover Procedures

Document and test failover procedures for each component. Database failover procedures should include promotion of read replica to primary or restoration from backup. Redis failover procedures should include promotion of replica or recreation from application state. Application failover should include deployment of new instances and DNS/load balancer updates.

Automate failover where possible to minimize recovery time. Use health checks and orchestrator features to automatically detect failures and trigger failover.

---

## Maintenance Procedures

Regular maintenance ensures system reliability and performance. This section covers common maintenance tasks and schedules.

### Database Maintenance

Schedule regular database maintenance including vacuuming to reclaim storage and update statistics, index rebuilding to improve query performance, and statistics updates for query planner accuracy. Use the pg_stat_statements extension to identify slow queries requiring optimization.

Run maintenance during low-traffic periods to minimize user impact. Monitor query performance and adjust maintenance schedules based on traffic patterns.

### Application Updates

Follow a structured process for application updates. Test updates in staging before production deployment. Use blue-green deployment or rolling updates to minimize downtime. Have rollback procedures ready in case issues are discovered after deployment.

Monitor application logs and metrics during and after updates. Set up alerts for error rate increases that might indicate deployment issues.

### Security Updates

Monitor security advisories for all dependencies. Apply security updates promptly, prioritizing critical and high severity vulnerabilities. Test updates in development before deploying to production.

Keep base Docker images updated with security patches. Use minimal base images to reduce attack surface. Scan images for vulnerabilities using tools like Trivy or Docker Scout.

---

## Troubleshooting Guide

This section provides guidance for diagnosing and resolving common operational issues.

### High API Latency

If API responses are slow, first identify whether the issue is in the application or downstream services. Check application metrics for response time trends. Examine database query times using PostgreSQL's query statistics. Review Redis operation times for caching issues.

Common causes include database query inefficiency (missing indexes or unoptimized queries), cache misses causing repeated database queries, network latency between application and database, and resource exhaustion (CPU, memory, or connections).

### High Error Rates

Monitor error rates through application metrics and logs. Check Sentry for detailed error information including stack traces and request context. Review recent deployments or configuration changes that might have introduced errors.

Common causes include database connection exhaustion, Redis connection issues, invalid configuration in updated environment variables, and migration failures or database schema mismatches.

### Celery Task Backlog

If task queues grow excessively, check worker status and resource availability. Verify workers are running and processing tasks. Check for errors in worker logs causing task failures and requeuing.

Common causes include insufficient worker count for the workload, workers stuck on long-running tasks, workers crashed and not restarted, and task time limits too restrictive for workload.

---

## Operational Checklists

Use these checklists for routine operational activities.

### Pre-Deployment Checklist

Before deploying to production, verify the following items are complete. All tests pass in the staging environment. New database migrations have been tested. Configuration changes have been documented. Rollback plan is ready. Stakeholders are notified of deployment window. Monitoring and alerting are functional.

### Daily Operations Checklist

Review the following items daily. Check system health via monitoring dashboards. Review error rates and investigate any anomalies. Verify backup jobs completed successfully. Check disk space utilization. Review application logs for warnings or errors.

### Weekly Operations Checklist

Perform the following items weekly. Review capacity trends and plan scaling if needed. Analyze slow queries and optimize as needed. Test alert notifications are working. Review security advisories and apply updates. Conduct restore drill to verify backup viability.

---

This operations and infrastructure guide provides comprehensive coverage of operational concerns for the LMS Backend. For additional details on specific topics, refer to related documentation files in the docs/tech/ directory or examine the configuration files and scripts in the project.
