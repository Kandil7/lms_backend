# Complete GitHub Workflows Documentation

This comprehensive documentation covers all GitHub Actions workflows in the LMS Backend project. Each workflow is documented in terms of its purpose, triggers, jobs, steps, and configuration details. Understanding these workflows is essential for developers working on CI/CD pipelines, security scanning, and deployment automation.

---

## Workflows Overview

The LMS Backend project uses GitHub Actions for continuous integration, security scanning, and deployment automation. Three primary workflows handle different aspects of the development and deployment lifecycle.

The CI workflow (ci.yml) validates code changes through testing and quality gates. It runs on every push and pull request, ensuring that changes meet quality standards before merging. This workflow executes unit tests, verifies code coverage, performs static analysis, and generates API documentation artifacts.

The Security workflow (security.yml) provides continuous security monitoring. It scans for vulnerable dependencies, identifies security issues in code, and detects secret leaks. This workflow runs on pushes, pull requests, and on a weekly schedule to catch newly discovered vulnerabilities.

The Deploy workflow (deploy-azure-vm.yml) automates production deployment to Azure Virtual Machines. It triggers on merges to the main branch, provisioning infrastructure and deploying the application. This workflow provides a repeatable, audited deployment process.

---

## CI Workflow (.github/workflows/ci.yml)

### Overview

The Continuous Integration workflow is the primary quality gate for code changes. It ensures that all code changes meet the project's quality standards before being merged into protected branches. The workflow runs comprehensive checks including static analysis, testing, and documentation generation.

### Trigger Configuration

The CI workflow triggers on multiple event types to provide comprehensive validation. Push events to main, develop, feature/*, and chore/* branches trigger the workflow. Pull requests targeting main and develop branches also trigger the workflow. This ensures that both direct pushes and pull request changes are validated.

The workflow uses a matrix strategy to test against multiple Python versions. This ensures compatibility with Python 3.11 and 3.12, allowing the project to support multiple Python versions while ensuring each version passes validation.

### Jobs Structure

The workflow defines two jobs that run in parallel for efficiency. The test job runs on Ubuntu Latest with both Python versions. The test-postgres job specifically tests against PostgreSQL to validate database compatibility beyond the default SQLite.

#### Test Job

The test job performs comprehensive validation using the following steps.

The checkout step uses actions/checkout@v4 to fetch the repository code. This provides the working directory for subsequent steps.

The setup Python step uses actions/setup-python@v5 with Python version matrix from the strategy. It also enables pip caching to speed up dependency installation. Caching significantly reduces workflow execution time by reusing installed packages between runs.

The install dependencies step upgrades pip and installs all project dependencies from requirements.txt. This ensures the exact dependencies used in production are installed for testing.

The static sanity checks step performs several validation tasks. It runs python -m compileall to verify all Python files compile without syntax errors. It runs python -m pip check to verify no dependencies have conflicting requirements. It generates the Postman collection using the generate_postman_collection.py script. It validates the generated JSON files are properly formatted using python -m json.tool. These checks catch issues early before running the full test suite.

The run tests step executes pytest with coverage reporting. The command pytest -q --cov=app --cov-report=term-missing --cov-fail-under=75 runs all tests quietly (one line per test), generates coverage reports, and fails if coverage falls below 75%. This coverage threshold ensures reasonable test coverage while allowing for practical considerations.

#### Test-Postgres Job

The test-postgres job specifically tests database functionality against PostgreSQL. This is important because SQLite, used in the default test configuration, does not support all PostgreSQL features like certain JSON operations and advanced indexing.

The job defines a PostgreSQL service container. It uses the postgres:16-alpine image and configures environment variables for user, password, and database name. The service exposes port 5432 for the test container to connect.

The steps include standard checkout, Python setup, and dependency installation. The wait for Postgres step implements a connection retry loop that waits up to 60 seconds for PostgreSQL to become available. This prevents test failures due to timing issues with service startup.

The run tests on Postgres step sets the TEST_DATABASE_URL environment variable to point to the PostgreSQL service and runs pytest. This validates that database operations work correctly with PostgreSQL.

### Environment Variables

The workflow uses several environment variables for configuration. Actions/cache@v4 handles caching of pip packages. The matrix strategy defines Python versions [3.11, 3.12]. Secrets are used for any protected resources accessed during testing.

### Failure Handling

If any step fails, the workflow fails and blocks merging through branch protection rules. The workflow must pass before code can be merged to protected branches. Notifications are sent to the repository maintainers through GitHub's standard notification system.

### Performance Considerations

The workflow is optimized for speed through several mechanisms. Pip caching reduces dependency installation time significantly. Parallel job execution reduces total workflow time. The matrix strategy runs both Python versions simultaneously rather than sequentially.

Typical workflow execution time is 3-5 minutes when caching is effective. Without caching, execution may take 5-8 minutes depending on network and system load.

---

## Security Workflow (.github/workflows/security.yml)

### Overview

The Security workflow provides continuous security monitoring for the project. It scans for vulnerable dependencies, identifies code security issues, and detects accidental secret commits. This workflow is critical for maintaining a secure codebase and preventing security incidents.

### Trigger Configuration

The security workflow triggers on multiple events to provide comprehensive security coverage. Push events to all branches trigger the workflow, ensuring new code is always scanned. Pull request events trigger scans for changes being reviewed. A weekly schedule (Saturday at 00:00 UTC) runs full scans even without code changes, catching newly discovered vulnerabilities in dependencies.

### Jobs Structure

The workflow runs a single comprehensive security scan job. This job uses an array of security tools to provide layered security validation.

#### Security Scan Job

The job runs on Ubuntu Latest and performs multiple security scans in sequence.

The checkout step fetches the repository code.

The security scan step runs a comprehensive set of security tools. The specific commands and tools are defined in the workflow file. The scan includes dependency vulnerability scanning, static code analysis for security issues, and secret detection.

Pip-audit scans for known vulnerabilities in Python dependencies. It compares installed packages against the Python Packaging Advisory Database and reports any known vulnerabilities. Critical and high severity vulnerabilities should be addressed immediately.

Bandit analyzes Python code for common security issues. It detects problems like hardcoded credentials, use of insecure cryptographic functions, and potential injection vulnerabilities. Bandit findings should be reviewed and addressed based on severity.

Gitleaks scans the repository for secrets and sensitive information. It detects API keys, passwords, tokens, and other credentials that should not be committed. Any detected secrets should be rotated immediately and the secrets management approach should be reviewed.

### Severity Handling

The security workflow should be configured to fail on critical findings while allowing warnings for lower severity issues. This ensures that serious security issues block deployment while allowing development to proceed with awareness of less critical findings.

Configure severity thresholds based on project needs. Critical vulnerabilities in dependencies should always fail the build. Code security issues may be acceptable at lower severity levels with appropriate justification.

### Weekly Scanning

The weekly scheduled run provides several benefits beyond push-based scanning. It catches vulnerabilities discovered after the last code change. It ensures dependency databases are checked for newly disclosed vulnerabilities. It provides regular security reporting without requiring code changes.

Review weekly scan results regularly to address emerging vulnerabilities. Set up alerts for critical findings to ensure prompt attention.

---

## Deploy Workflow (.github/workflows/deploy-azure-vm.yml)

### Overview

The Deploy workflow automates production deployment to Azure Virtual Machines. It provides a repeatable, auditable deployment process that reduces manual errors and enables rapid, reliable releases.

### Trigger Configuration

The deployment workflow triggers on push events to the main branch. This ensures that only verified, merged code is deployed to production. The workflow can be manually triggered through the GitHub interface for special circumstances.

### Prerequisites

Before the workflow can run, several prerequisites must be configured.

Azure credentials must be stored as GitHub secrets. This includes the Azure subscription ID, tenant ID, client ID, and client secret. These credentials should have contributor access to the target resource group but not owner access for security.

Environment variables should be configured for the deployment. This includes the Azure resource group name, VM name, location, and other deployment-specific settings.

The workflow uses the azure/login action for authentication. It accepts Azure credentials through GitHub secrets and connects to the specified Azure subscription.

### Jobs Structure

The deployment workflow consists of multiple jobs that execute in sequence. Each job handles a specific aspect of the deployment process.

#### Deployment Job

The deployment job performs the actual deployment using the following approach.

The checkout step fetches the repository code including the deployment scripts.

The Azure login step authenticates to Azure using the provided credentials. It uses the azure/login action with service principal credentials.

The Azure VM deployment step runs the deploy_azure_vm.ps1 script with appropriate parameters. This script handles VM provisioning, Docker installation, and application deployment.

The deployment script performs several operations. It creates the resource group if it does not exist. It provisions a virtual machine with the specified size. It installs Docker and Docker Compose on the VM. It configures the application through environment variables. It deploys the Docker Compose stack. Finally, it verifies the deployment through health checks.

### Configuration Parameters

The workflow accepts several configuration parameters.

Azure subscription details include the subscription ID, tenant ID, client ID, and client secret. These are stored as GitHub secrets for security.

Deployment parameters include the resource group name, VM name, Azure region, and VM size. These can be set as environment variables or workflow inputs.

Application configuration includes the database connection string, Redis URL, and other environment-specific settings. These are passed to the deployment script as environment variables.

### Post-Deployment Verification

After deployment completes, verification steps should confirm successful deployment. The workflow includes health check verification through the readiness endpoint. Additional manual verification steps may include checking application logs, verifying database connectivity, and testing key functionality.

### Rollback Procedures

If deployment fails or issues are discovered post-deployment, rollback procedures should be executed. The deployment process should preserve the previous deployment state where possible. Documentation should specify rollback steps including reverting to the previous GitHub deployment or redeploying the previous version.

---

## Workflow Configuration Best Practices

### Secrets Management

GitHub secrets should be used for all sensitive values including credentials, API keys, and connection strings. Never hardcode secrets in workflow files. Use the secrets interface in GitHub repository settings to configure protected values.

Rotate secrets regularly, especially after any suspected compromise. Azure service principal credentials should be rotated at least quarterly. Token-based credentials should have appropriate expiration periods.

### Branch Protection

Configure branch protection rules to require workflow success before merging. This ensures all quality and security checks pass before code reaches protected branches.

Require status checks to pass before merging. Configure the required checks to include all critical workflows. Allow administrators to bypass in exceptional circumstances only.

### Notification and Alerts

Configure notifications for workflow failures. Ensure the appropriate team members receive alerts when workflows fail. Set up separate notification channels for critical production deployments versus routine development workflows.

### Performance Optimization

Optimize workflow execution time through caching strategies. Cache pip packages, node modules, and other build dependencies. Use actions/cache for reusable caching across workflow runs.

Run independent jobs in parallel where possible. The CI workflow demonstrates this by running test jobs for different Python versions in parallel.

---

## Monitoring Workflows

### Viewing Workflow Runs

Access workflow runs through the Actions tab in the GitHub repository. Each run shows the trigger, status, duration, and individual job results. Click into a run to see detailed logs for each step.

### Troubleshooting Failures

When a workflow fails, examine the logs to identify the specific failure point. Common failure causes include test failures, coverage below threshold, security vulnerabilities detected, and deployment connectivity issues.

For test failures, examine the test output to identify failing tests. For security failures, review the security scan output for finding details. For deployment failures, check Azure activity logs and VM console output.

### Workflow Metrics

Track workflow performance over time. Monitor average execution time, failure rates, and trends. Use this data to identify optimization opportunities and potential quality issues.

---

## Extending Workflows

### Adding New Checks

To add new validation checks to the CI workflow, add new steps in the appropriate job. Steps can run additional tools, execute tests, or generate additional artifacts.

### Custom Triggers

Modify trigger configuration to change when workflows run. Common customizations include adding scheduled runs, restricting triggers to specific paths, or adding manual trigger options.

### Environment-Specific Deployments

Create additional deployment workflows for staging or other environments. Copy the existing deploy workflow and modify parameters for the target environment. Use GitHub environments to configure approval workflows for production deployments.

---

This comprehensive documentation covers all GitHub Actions workflows used in the LMS Backend project. Each workflow is designed for specific purposes and can be customized as needs evolve. Understanding these workflows enables effective CI/CD pipeline management and facilitates troubleshooting when issues arise.
