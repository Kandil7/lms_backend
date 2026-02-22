# CI/CD Pipeline Documentation (.github/workflows/)

## Overview

This directory contains GitHub Actions workflows for continuous integration, security scanning, and production deployment.

---

## Workflow Files

### 1. ci.yml - Continuous Integration

**Purpose**: Run tests and validation on every push and pull request.

**Triggers**:
```yaml
on:
  push:
    branches: [main, develop, feature/**, chore/**]
  pull_request:
    branches: [main, develop]
```

**Why These Triggers**:
- **feature/*** and ***chore/*** branches: Standard branch prefixes used in this project
- **main and develop**: Primary branches requiring CI validation
- **Pull requests**: Ensures code quality before merging

**Jobs**:

#### Job 1: `test` (Python 3.11 and 3.12)

```yaml
runs-on: ubuntu-latest
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
```

**Why Matrix Strategy**:
- Tests against both Python 3.11 and 3.12 for maximum compatibility
- Catches version-specific issues early

**Steps**:

1. **Checkout**
   ```yaml
   - uses: actions/checkout@v4
   ```
   - Clones the repository
   - Uses v4 for better performance

2. **Setup Python**
   ```yaml
   - uses: actions/setup-python@v5
     with:
       python-version: ${{ matrix.python-version }}
       cache: pip
   ```
   - Uses pip caching to speed up builds
   - Version 5 is latest stable

3. **Install Dependencies**
   ```yaml
   - run: |
       python -m pip install --upgrade pip
       pip install -r requirements.txt
   ```
   - Upgrades pip first for better package resolution

4. **Static Sanity Checks**
   ```yaml
   - run: |
       python -m compileall app scripts
       python -m pip check
       python scripts/generate_postman_collection.py
       python -m json.tool "postman/LMS Backend.postman_collection.json" > /dev/null
       python -m json.tool "postman/LMS Backend.postman_environment.json" > /dev/null
   ```
   - **compileall**: Checks Python syntax across app and scripts
   - **pip check**: Detects broken dependencies
   - **generate_postman_collection**: Creates API documentation
   - **json.tool**: Validates JSON output files

   **Why These Checks**:
   - Catch syntax errors without running tests
   - Validate generated files
   - Fail fast approach

5. **Run Tests with Coverage**
   ```yaml
   - run: python -m pytest -q --cov=app --cov-report=term-missing --cov-fail-under=75
   ```
   - **-q**: Quiet mode (less verbose)
   - **--cov=app**: Measure coverage for app directory
   - **--cov-fail-under=75**: Fail if coverage drops below 75%

   **Why 75% Coverage**:
   - Balances test thoroughness with development speed
   - Ensures critical paths are tested
   - Can be increased over time

#### Job 2: `test-postgres` (Python 3.12 only)

```yaml
runs-on: ubuntu-latest
services:
  postgres:
    image: postgres:16-alpine
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: lms_test
    ports:
      - 5432:5432
```

**Why Separate Postgres Job**:
- Tests with real PostgreSQL database
- Some features may not work with SQLite (foreign keys, constraints)
- Tests async database operations

**Steps**:
1. Checkout
2. Setup Python 3.12
3. Install dependencies
4. Wait for Postgres (custom Python script)
5. Run tests with TEST_DATABASE_URL

---

### 2. security.yml - Security Scanning

**Purpose**: Automated security vulnerability detection.

**Triggers**:
```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: "0 3 * * 1"  # Weekly Monday 3 AM
  workflow_dispatch:  # Manual trigger
```

**Why These Triggers**:
- **Push to main/develop**: Scan every change
- **Pull requests**: Catch issues before merge
- **Weekly schedule**: Catch new vulnerabilities in dependencies
- **workflow_dispatch**: Manual security scan

**Job**: `security-scan`

```yaml
runs-on: ubuntu-latest
```

**Steps**:

1. **Checkout**
   ```yaml
   - uses: actions/checkout@v4
   ```

2. **Setup Python**
   ```yaml
   - uses: actions/setup-python@v5
     with:
       python-version: "3.12"
       cache: pip
   ```

3. **Install Dependencies**
   ```yaml
   - run: |
       python -m pip install --upgrade pip
       pip install -r requirements.txt
       pip install pip-audit bandit[toml]
   ```

4. **Dependency Vulnerability Scan (pip-audit)**
   ```yaml
   - run: pip-audit -r requirements.txt --strict --ignore-vuln CVE-2024-23342
   ```
   - **--strict**: Exit with error if vulnerabilities found
   - **--ignore-vuln**: Exclude specific CVE (known false positive)

5. **Static Security Scan (bandit)**
   ```yaml
   - run: bandit -r app scripts -x tests -lll -ii
   ```
   - **-r**: Recursive scan
   - **-x tests**: Exclude test directory
   - **-lll**: Low severity issues reported
   - **-ii**: Confidence issues reported

6. **Secret Scanning (gitleaks)**
   ```yaml
   - uses: gitleaks/gitleaks-action@v2
   ```
   - Scans for exposed secrets in code

**Why This Security Stack**:
- **pip-audit**: Official Python security database
- **bandit**: Static analysis for common Python security issues
- **gitleaks**: Industry-standard secret detection

---

### 3. deploy-azure-vm.yml - Production Deployment

**Purpose**: Deploy to Azure VM on main branch push.

**Triggers**:
```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:  # Manual deployment
```

**Why These Triggers**:
- **main branch**: Production deployments only
- **workflow_dispatch**: Manual rollback/deployment

**Concurrency**:
```yaml
concurrency:
  group: production-deploy
  cancel-in-progress: false
```

**Why cancel-in-progress: false**:
- Prevents race conditions
- Ensures deployments complete in order

**Job**: `deploy`

```yaml
runs-on: ubuntu-latest
environment: production
```

**Why Environment**:
- Requires approval in GitHub
- Protects production from accidental deployments

**Steps**:

1. **Checkout**
   ```yaml
   - uses: actions/checkout@v4
   ```

2. **Build Release Archive**
   ```yaml
   - run: git archive --format=tar.gz -o release.tar.gz HEAD
   ```
   - Creates tar.gz of current commit
   - Excludes .git directory
   - Smaller artifact for transfer

3. **Upload to VM (SCP)**
   ```yaml
   - uses: appleboy/scp-action@v0.1.7
     with:
       host: ${{ secrets.AZURE_VM_HOST }}
       username: ${{ secrets.AZURE_VM_USER }}
       key: ${{ secrets.AZURE_VM_SSH_KEY }}
       source: release.tar.gz
       target: /tmp
   ```
   - Transfers archive to VM
   - Uses SSH key authentication
   - Stores in /tmp for extraction

4. **Deploy on VM (SSH)**
   ```yaml
   - uses: appleboy/ssh-action@v1.2.0
     env:
       PROD_DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}
       SECRET_KEY: ${{ secrets.SECRET_KEY }}
       # ... other secrets
     with:
       script: |
         set -euo pipefail
         APP_DIR=/opt/lms_backend
         mkdir -p "$APP_DIR"
         tar -xzf /tmp/release.tar.gz -C "$APP_DIR"
         cd "$APP_DIR"
         chmod +x scripts/deploy_azure_vm.sh
         APP_DIR="$APP_DIR" ./scripts/deploy_azure_vm.sh
   ```

**Environment Variables**:
| Variable | Purpose |
|----------|---------|
| PROD_DATABASE_URL | Production database connection |
| SECRET_KEY | JWT signing key |
| APP_DOMAIN | Domain for HTTPS |
| LETSENCRYPT_EMAIL | TLS certificate email |
| SMTP_* | Email configuration |
| SENTRY_DSN | Error tracking |

**Why SSH Deploy**:
- Full control over deployment process
- Can run custom scripts
- No external dependencies

---

## Decision Rationale

### Why GitHub Actions?

1. **Native Integration**: Tight GitHub integration
2. **Free Tier**: Ample free minutes for open source
3. **Mature Ecosystem**: Pre-built actions available
4. **Secret Management**: Built-in encrypted secrets

### Why Separate Jobs?

1. **Parallel Execution**: Jobs run in parallel when possible
2. **Resource Isolation**: Each job has fresh environment
3. **Failure Isolation**: One job failure doesn't affect others
4. **Cost Optimization**: PostgreSQL job only runs Python 3.12

### Why Minimum Coverage 75%?

1. **Balanced Approach**: Strict enough for quality, flexible enough for speed
2. **Industry Standard**: Common benchmark for Python projects
3. **Gradual Improvement**: Can increase over time with refactoring

### Why Weekly Security Scan?

1. **Zero-Day Protection**: Catch new vulnerabilities quickly
2. **CI Complement**: More thorough than CI-only scanning
3. **Low Overhead**: Weekly is sufficient for vulnerability discovery pace
