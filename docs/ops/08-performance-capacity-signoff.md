# Performance and Capacity Sign-off

## 1. Goal
- Validate production-like load behavior.
- Define explicit capacity baseline for launch.

## 2. Test Scenario
- Script: `tests/perf/k6_realistic.js`
- Runner: `run_load_test_realistic.bat`
- Journeys:
  - student: login + dashboard + enrolled courses
  - instructor: login + course listing
  - admin: login + users listing
  - background readiness probe

## 3. Run Command
```bat
run_load_test_realistic.bat http://localhost:8001 10m localhost 8 3 1
```
Arguments:
1. base URL
2. duration
3. host header
4. student arrival rate / sec
5. instructor arrival rate / sec
6. admin arrival rate / sec

## 4. Sign-off Thresholds
- `http_req_failed < 2%`
- `p95 latency < 800ms`
- `checks pass rate > 98%`
- No sustained error alerts in Grafana/Alertmanager.

## 5. Capacity Baseline Template
Record and approve before launch:

| Metric | Value | Notes |
|---|---|---|
| Peak tested requests/sec | `<fill>` | from k6 report |
| Safe sustained requests/sec | `<fill>` | with headroom |
| Max concurrent active users | `<fill>` | assumption-based |
| API p95 latency | `<fill>` | target < 800ms |
| DB CPU at peak | `<fill>` | infra metric |
| Redis CPU at peak | `<fill>` | infra metric |

## 6. Decision Rule
- Go if thresholds pass with >= 20% capacity headroom.
- No-go if thresholds fail or if observability indicates instability.

