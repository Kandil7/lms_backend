"""Secrets management module for production environments.

This module provides secure secret retrieval from multiple sources:
- HashiCorp Vault (primary for production)
- Environment variables (fallback/development)
- Azure Key Vault (optional)
- GCP Secret Manager (optional)

The implementation follows the principle of least privilege and secure secret handling.
"""

import os
import logging
from typing import Optional, Dict, Any, Union
from enum import Enum

# Try to import vault client - will be None if not available
try:
    import hvac
    HAS_VAULT = True
except ImportError:
    HAS_VAULT = False
    hvac = None

logger = logging.getLogger(__name__)


class SecretSource(Enum):
    """Enumeration of supported secret sources."""
    ENV_VAR = "env_var"
    VAULT = "vault"
    AZURE_KEY_VAULT = "azure_key_vault"
    GCP_SECRET_MANAGER = "gcp_secret_manager"


class SecretsManager:
    """Centralized secrets manager for secure secret retrieval."""
    
    def __init__(self):
        self._vault_client = None
        self._source = None
        self._initialized = False
        
    def initialize(self, source: str = "env_var", **kwargs) -> bool:
        """Initialize the secrets manager with the specified source.

        Args:
            source: Source type ('env_var', 'vault', 'azure_key_vault', 'gcp_secret_manager')
            kwargs: Configuration parameters for the source

        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self._source = SecretSource(source)

            if self._source == SecretSource.VAULT and HAS_VAULT:
                # Initialize Vault client
                vault_url = kwargs.get('vault_url') or os.getenv('VAULT_ADDR')
                vault_token = kwargs.get('vault_token') or os.getenv('VAULT_TOKEN')
                vault_namespace = kwargs.get('vault_namespace') or os.getenv('VAULT_NAMESPACE')

                if not vault_url:
                    raise ValueError("Vault URL must be provided for Vault source")

                self._vault_client = hvac.Client(
                    url=vault_url,
                    token=vault_token,
                    namespace=vault_namespace
                )

                # Test connection
                if not self._vault_client.is_authenticated():
                    raise ValueError("Failed to authenticate with Vault")

            elif self._source == SecretSource.AZURE_KEY_VAULT:
                # Initialize Azure Key Vault client
                vault_url = kwargs.get('vault_url') or os.getenv('AZURE_KEYVAULT_URL')
                if not vault_url:
                    raise ValueError("Azure Key Vault URL must be provided for Azure source")

                try:
                    from azure.identity import DefaultAzureCredential, EnvironmentCredential, ManagedIdentityCredential
                    from azure.keyvault.secrets import SecretClient
                    
                    # Try different authentication methods in order of preference
                    credential = None
                    auth_methods = []
                    
                    # 1. Managed Identity (for Azure VMs, App Services, etc.)
                    try:
                        credential = ManagedIdentityCredential()
                        # Test credential by getting a secret
                        test_client = SecretClient(vault_url=vault_url, credential=credential)
                        test_client.get_secret("test-secret")
                        auth_methods.append("Managed Identity")
                    except Exception as mi_error:
                        logger.debug(f"Managed Identity authentication failed: {mi_error}")
                    
                    # 2. Environment variables (AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)
                    if credential is None:
                        try:
                            credential = EnvironmentCredential()
                            # Test credential
                            test_client = SecretClient(vault_url=vault_url, credential=credential)
                            test_client.get_secret("test-secret")
                            auth_methods.append("Environment Variables")
                        except Exception as env_error:
                            logger.debug(f"Environment variables authentication failed: {env_error}")
                    
                    # 3. DefaultAzureCredential (fallback that tries multiple methods)
                    if credential is None:
                        try:
                            credential = DefaultAzureCredential()
                            # Test credential
                            test_client = SecretClient(vault_url=vault_url, credential=credential)
                            test_client.get_secret("test-secret")
                            auth_methods.append("DefaultAzureCredential")
                        except Exception as default_error:
                            logger.warning(f"All Azure authentication methods failed: {default_error}")
                            raise ValueError("Failed to authenticate with Azure Key Vault using any available method")
                    
                    self._azure_client = SecretClient(vault_url=vault_url, credential=credential)
                    logger.info(f"Azure Key Vault authenticated via: {', '.join(auth_methods)}")
                except ImportError:
                    raise ValueError(
                        "Azure Key Vault dependencies not installed. "
                        "Install with: pip install azure-identity azure-keyvault-secrets"
                    )
                except Exception as azure_init_error:
                    raise ValueError(f"Failed to initialize Azure Key Vault client: {azure_init_error}")

            elif self._source == SecretSource.GCP_SECRET_MANAGER:
                # Initialize GCP Secret Manager client
                try:
                    from google.cloud import secretmanager
                    self._gcp_client = secretmanager.SecretManagerServiceClient()
                except ImportError:
                    raise ValueError("GCP Secret Manager dependencies not installed. Install with: pip install google-cloud-secret-manager")

            self._initialized = True
            logger.info(f"Secrets manager initialized with source: {self._source.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize secrets manager: {e}")
            self._initialized = False
            return False
    
    def get_secret(self, key: str, default: Optional[str] = None,
                   path: str = "secret/data/lms",
                   mount_point: str = "secret") -> Optional[str]:
        """Retrieve a secret from the configured source.

        Args:
            key: Secret key name
            default: Default value if secret not found
            path: Vault path (for Vault source)
            mount_point: Vault mount point (for Vault source)

        Returns:
            str: Secret value or default if not found
        """
        if not self._initialized:
            raise RuntimeError("Secrets manager not initialized")

        try:
            # First try environment variables (fastest)
            env_key = f"SECRET_{key.upper()}"
            env_value = os.getenv(env_key)
            if env_value is not None:
                return env_value

            # Try direct environment variable (legacy)
            direct_env_value = os.getenv(key)
            if direct_env_value is not None:
                return direct_env_value

            # Then try configured secret source
            if self._source == SecretSource.VAULT and self._vault_client:
                # Try to get from Vault
                try:
                    response = self._vault_client.secrets.kv.v2.read_secret_version(
                        path=path,
                        mount_point=mount_point,
                        version=None
                    )
                    data = response['data']['data']
                    return data.get(key, default)
                except Exception as vault_error:
                    logger.warning(f"Vault lookup failed for '{key}': {vault_error}")
                    # Fall back to environment variables (already tried above)
                    pass

            elif self._source == SecretSource.AZURE_KEY_VAULT and hasattr(self, '_azure_client') and self._azure_client:
                # Try to get from Azure Key Vault
                try:
                    # Azure Key Vault uses different naming convention - prefix with 'lms-' for production
                    azure_key = f"lms-{key.lower()}"
                    secret = self._azure_client.get_secret(azure_key)
                    return secret.value
                except Exception as azure_error:
                    # Log detailed error but don't fail completely
                    logger.warning(f"Azure Key Vault lookup failed for '{azure_key}': {azure_error}")
                    # Fall back to environment variables (already tried above)
                    pass

            # If all else fails, return default
            return default

        except Exception as e:
            logger.error(f"Error retrieving secret '{key}': {e}")
            return default
    
    def get_all_secrets(self, path: str = "secret/data/lms", 
                        mount_point: str = "secret") -> Dict[str, str]:
        """Retrieve all secrets from a specific path (Vault only).
        
        Args:
            path: Vault path
            mount_point: Vault mount point
            
        Returns:
            Dict[str, str]: Dictionary of secret key-value pairs
        """
        if not self._initialized or self._source != SecretSource.VAULT or not self._vault_client:
            return {}
        
        try:
            response = self._vault_client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount_point,
                version=None
            )
            return response['data']['data']
        except Exception as e:
            logger.error(f"Error retrieving all secrets: {e}")
            return {}


# Global instance
_secrets_manager = SecretsManager()


def get_secret(key: str, default: Optional[str] = None, 
               path: str = "secret/data/lms", 
               mount_point: str = "secret") -> Optional[str]:
    """Convenience function to get a secret using the global manager.
    
    Args:
        key: Secret key name
        default: Default value if secret not found
        path: Vault path (for Vault source)
        mount_point: Vault mount point (for Vault source)
        
    Returns:
        str: Secret value or default if not found
    """
    return _secrets_manager.get_secret(key, default, path, mount_point)


def initialize_secrets_manager(source: str = "env_var", **kwargs) -> bool:
    """Initialize the global secrets manager.
    
    Args:
        source: Source type ('env_var', 'vault', 'azure_key_vault', 'gcp_secret_manager')
        kwargs: Configuration parameters for the source
        
    Returns:
        bool: True if initialization successful, False otherwise
    """
    return _secrets_manager.initialize(source, **kwargs)


# Backward compatibility functions for existing code
def get_secret_from_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get secret from environment variables (backward compatibility)."""
    return os.getenv(key, default)


# Initialize on import for development
if os.getenv("ENVIRONMENT") != "production":
    # In development, use environment variables directly
    initialize_secrets_manager("env_var")
