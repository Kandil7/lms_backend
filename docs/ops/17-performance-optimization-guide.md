# Performance Optimization Guide

This document outlines the performance optimization strategy for the LMS backend in production environments.

## 1. Overview

The LMS backend uses a comprehensive performance testing and optimization approach with:
- **Realistic load testing**: k6 scripts simulating student, instructor, and admin journeys
- **Capacity planning**: Baseline metrics for scaling decisions
- **Database optimization**: Indexing and query optimization
- **Caching strategy**: Redis-based caching for high-frequency data

## 2. Current Performance Infrastructure

### 2.1 Load Testing Scripts
- `tests/perf/k6_realistic.js`: Realistic user journey simulation
- `tests/perf/k6_smoke.js`: Basic smoke tests
- `run_load_test_realistic.bat`: Windows wrapper for realistic testing
- `run_load_test.bat`: Basic load test wrapper

### 2.2 Key Performance Metrics
- **API Response Time**: P95, P99 latency targets
- **Throughput**: Requests per second (RPS)
- **Error Rate**: HTTP 5xx errors percentage
- **Resource Utilization**: CPU, memory, database connections

## 3. Performance Baselines

### 3.1 Target SLAs
- **P95 Latency**: < 800ms for API endpoints
- **P99 Latency**: < 2s for API endpoints
- **Error Rate**: < 2% for all requests
- **Throughput**: 100+ RPS per API instance
- **Database Connection Pool**: < 80% utilization

### 3.2 Capacity Estimates
| Metric | Small (100 users) | Medium (1,000 users) | Large (10,000 users) |
|--------|------------------|----------------------|-----------------------|
| API Instances | 2 | 4 | 8 |
| Database | 1 PostgreSQL | 1 PostgreSQL + Read Replica | 2 PostgreSQL + Read Replicas |
| Redis | 1 instance | 1 instance | 2 instances (sharded) |
| Celery Workers | 2 | 4 | 8 |

## 4. Database Optimization

### 4.1 Critical Indexes
```sql
-- Courses table
CREATE INDEX idx_courses_instructor ON courses(instructor_id);
CREATE INDEX idx_courses_published ON courses(is_published) WHERE is_published = true;
CREATE INDEX idx_courses_category ON courses(category) WHERE is_published = true;

-- Enrollments table
CREATE INDEX idx_enrollments_student ON enrollments(student_id, status);
CREATE INDEX idx_enrollments_course ON enrollments(course_id, status);
CREATE INDEX idx_enrollments_progress ON enrollments(progress_percentage) WHERE status = 'active';

-- Lesson Progress table
CREATE INDEX idx_lesson_progress_enrollment ON lesson_progress(enrollment_id);
CREATE INDEX idx_lesson_progress_lesson ON lesson_progress(lesson_id, status);

-- Quizzes table
CREATE INDEX idx_quizzes_lesson ON quizzes(lesson_id);
```

### 4.2 Query Optimization
- Use `EXPLAIN ANALYZE` for slow queries
- Avoid N+1 queries in ORM relationships
- Implement pagination for large result sets
- Use materialized views for complex analytics queries

### 4.3 Connection Pool Tuning
- **PostgreSQL**: `DB_POOL_SIZE=20`, `DB_MAX_OVERFLOW=40`
- Monitor connection pool usage: `lms_database_connection_pool_usage`
- Set appropriate timeouts: `statement_timeout=30s`, `idle_in_transaction_session_timeout=60s`

## 5. Caching Strategy

### 5.1 Cache Layers
- **Redis**: Primary cache for high-frequency data
- **Application-level**: In-memory cache for computed values
- **CDN**: For static assets (uploads, certificates)

### 5.2 Cache Keys and TTLs
| Data Type | Cache Key Pattern | TTL | Strategy |
|-----------|-------------------|-----|----------|
| Course data | `course:{id}` | 120s | Write-through |
| Lesson data | `lesson:{id}` | 120s | Write-through |
| Quiz data | `quiz:{id}` | 120s | Write-through |
| User profiles | `user:{id}` | 120s | Write-through |
| Analytics data | `analytics:course:{id}` | 300s | Write-behind |
| Leaderboards | `leaderboard:course:{id}` | 3600s | Write-behind |

### 5.3 Cache Invalidation
- **Write operations**: Invalidate related cache keys
- **Time-based**: Automatic expiration
- **Event-driven**: Pub/Sub for distributed invalidation

## 6. Application-Level Optimizations

### 6.1 Async Operations
- Use async/await for I/O-bound operations
- Offload heavy processing to Celery workers
- Implement request batching for bulk operations

### 6.2 Response Optimization
- Enable gzip compression
- Optimize JSON serialization
- Implement response envelope optimization
- Use streaming for large responses

### 6.3 Rate Limiting
- **Global**: 100 requests/minute per IP
- **Auth endpoints**: 5 requests/minute per IP
- **File uploads**: 10 requests/hour per IP
- Use Redis for distributed rate limiting

## 7. Load Testing Procedure

### 7.1 Pre-Testing Checklist
- [ ] Verify staging environment matches production specs
- [ ] Ensure monitoring is enabled
- [ ] Prepare test data (users, courses, enrollments)
- [ ] Configure k6 script parameters

### 7.2 Test Scenarios
1. **Baseline**: 10 users, 5 minutes
2. **Stress**: 100 users, 15 minutes
3. **Soak**: 50 users, 60 minutes
4. **Spike**: 200 users, 5 minutes (ramp up/down)
5. **Realistic**: Student (80%), Instructor (15%), Admin (5%) mix

### 7.3 Analysis Criteria
- **Green**: All thresholds met, no errors
- **Yellow**: Some thresholds exceeded, but system stable
- **Red**: Critical failures, system unstable

## 8. Performance Monitoring

### 8.1 Key Metrics to Monitor
- **API**: Request rate, error rate, latency percentiles
- **Database**: Connection pool usage, query latency, lock waits
- **Redis**: Memory usage, hit ratio, client connections
- **Celery**: Worker queue length, task duration, failure rate

### 8.2 Alert Thresholds
- **Critical**: P99 > 2s, Error rate > 5%, CPU > 90%
- **Warning**: P95 > 1s, Error rate > 2%, CPU > 70%
- **Info**: P95 > 800ms, Error rate > 1%

## 9. Optimization Roadmap

### 9.1 Immediate (Pre-production)
- Implement missing indexes
- Tune connection pools
- Optimize critical API endpoints
- Configure proper caching

### 9.2 Short-term (Post-launch)
- Add read replicas for database
- Implement CDN for static assets
- Optimize analytics queries
- Add horizontal scaling for API instances

### 9.3 Long-term (Scale phase)
- Database sharding
- Microservices decomposition
- Advanced caching strategies
- AI-powered performance optimization

## 10. Verification and Validation

### 10.1 Performance Sign-off Checklist
- [ ] Load test results meet SLA targets
- [ ] Database queries optimized with proper indexes
- [ ] Caching strategy implemented and effective
- [ ] Resource utilization within safe limits
- [ ] Error rates below threshold
- [ ] Recovery from failures tested

### 10.2 Tools and Commands
```bash
# Run realistic load test
.\run_load_test_realistic.bat http://localhost:8001 10m localhost 8 3 1

# Analyze database queries
psql -U lms -d lms -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Check cache hit ratio
redis-cli info stats | grep -E "(keyspace|hit)"

# Monitor system resources
docker stats --no-stream
```

## 11. Troubleshooting

### Common Performance Issues:
- **High latency**: Check database queries, network latency, Redis connectivity
- **Connection pool exhaustion**: Increase pool size or optimize queries
- **Cache misses**: Review cache key patterns, TTL settings
- **CPU spikes**: Profile application code, check for inefficient algorithms
- **Memory leaks**: Monitor memory usage over time, check for unclosed resources

### Debugging Steps:
1. Identify bottleneck (API, DB, Redis, network)
2. Use profiling tools (cProfile, py-spy, pg_stat_statements)
3. Optimize the identified bottleneck
4. Retest and validate improvements
5. Document changes and performance impact

## 12. Documentation Requirements

- Performance test results and analysis
- Database optimization report
- Caching strategy documentation
- Capacity planning document
- Performance monitoring dashboard configurations