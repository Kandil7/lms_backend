#!/usr/bin/env python3
"""
Environment Validation Script for LMS Production Deployment

This script validates that the production environment is properly configured
for security and operational readiness.
"""

import os
import sys
import logging
from typing import List, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnvironmentValidator:
    """Validate production environment configuration."""

    def __init__(self):
        self.results: List[Dict[str, str]] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_required_env_vars(self) -> None:
        """Validate required environment variables for production."""
        required_vars = [
            ("ENVIRONMENT", "production"),
            ("DEBUG", "false"),
            ("STRICT_ROUTER_IMPORTS", "true"),
            ("TASKS_FORCE_INLINE", "false"),
            ("ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED", "true"),
        ]
        
        for var_name, expected_value in required_vars:
            actual_value = os.getenv(var_name)
            if actual_value is None:
                self.errors.append(f"Missing required environment variable: {var_name}")
            elif actual_value.lower() != expected_value.lower():
                self.errors.append(f"Invalid value for {var_name}: expected '{expected_value}', got '{actual_value}'")

    def validate_secret_sources(self) -> None:
        """Validate secret management configuration."""
        # Check for Azure Key Vault configuration (preferred)
        azure_keyvault_url = os.getenv("AZURE_KEYVAULT_URL")
        vault_addr = os.getenv("VAULT_ADDR")
        
        if not azure_keyvault_url and not vault_addr:
            self.warnings.append("No secret manager configured (Azure Key Vault or Vault). Using environment variables as fallback.")
        else:
            if azure_keyvault_url:
                logger.info(f"Azure Key Vault configured: {azure_keyvault_url}")
            if vault_addr:
                logger.info(f"HashiCorp Vault configured: {vault_addr}")

    def validate_security_headers(self) -> None:
        """Validate security-related configuration."""
        # Check for security-sensitive settings
        insecure_values = [
            ("SECRET_KEY", ["change-me", "change-this-in-production-with-64-random-chars-minimum"]),
            ("POSTGRES_PASSWORD", ["lms"]),
            ("SMTP_PASSWORD", ["", None]),
        ]
        
        for var_name, insecure_patterns in insecure_values:
            value = os.getenv(var_name)
            if value is None:
                self.errors.append(f"Missing security-sensitive variable: {var_name}")
            else:
                for pattern in insecure_patterns:
                    if pattern == value or (isinstance(pattern, str) and pattern in value):
                        self.errors.append(f"Insecure value for {var_name}: '{value}'")

    def validate_database_config(self) -> None:
        """Validate database configuration."""
        db_url = os.getenv("DATABASE_URL")
        if db_url and "localhost" in db_url and os.getenv("ENVIRONMENT") == "production":
            self.warnings.append("Database URL contains 'localhost' in production environment")

    def validate_tls_config(self) -> None:
        """Validate TLS/SSL configuration."""
        app_domain = os.getenv("APP_DOMAIN")
        if not app_domain:
            self.errors.append("APP_DOMAIN not set for TLS configuration")
        else:
            logger.info(f"TLS domain configured: {app_domain}")

    def run_validation(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validation checks."""
        logger.info("Starting environment validation...")
        
        self.validate_required_env_vars()
        self.validate_secret_sources()
        self.validate_security_headers()
        self.validate_database_config()
        self.validate_tls_config()
        
        logger.info(f"Validation completed: {len(self.errors)} errors, {len(self.warnings)} warnings")
        
        return len(self.errors) == 0, self.errors, self.warnings

    def print_results(self) -> None:
        """Print validation results."""
        print("\n" + "="*60)
        print("ENVIRONMENT VALIDATION RESULTS")
        print("="*60)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All validations passed!")
        
        print(f"\nStatus: {'PASS' if not self.errors else 'FAIL'}")
        print("="*60)

def main() -> int:
    """Main function."""
    validator = EnvironmentValidator()
    
    try:
        success, errors, warnings = validator.run_validation()
        validator.print_results()
        
        if not success:
            return 1
        return 0
        
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())