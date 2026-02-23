"""Unit tests for secrets management module."""

import os
import pytest
from unittest.mock import MagicMock
from app.core.secrets import SecretSource, SecretsManager, get_secret, initialize_secrets_manager


@pytest.fixture(autouse=True)
def reset_secret_env(monkeypatch):
    keys = [
        "SECRET_TEST_KEY",
        "TEST_KEY",
        "VAULT_ADDR",
        "VAULT_TOKEN",
        "VAULT_NAMESPACE",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    yield
    for key in keys:
        monkeypatch.delenv(key, raising=False)


class TestSecretsManager:
    def test_initialization_env_var(self):
        """Test initialization with environment variable source."""
        # Set up environment variables
        os.environ["SECRET_TEST_KEY"] = "test_value"
        
        manager = SecretsManager()
        success = manager.initialize("env_var")
        
        assert success is True
        assert manager._source == SecretSource.ENV_VAR
        assert manager._initialized is True
    
    def test_initialization_vault_success(self, monkeypatch):
        """Test successful Vault initialization."""
        # Mock hvac import and client
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        
        monkeypatch.setattr("app.core.secrets.hvac", MagicMock(Client=lambda **kwargs: mock_client))
        monkeypatch.setattr("app.core.secrets.HAS_VAULT", True)
        
        # Set environment variables
        os.environ["VAULT_ADDR"] = "http://localhost:8200"
        os.environ["VAULT_TOKEN"] = "test-token"
        
        manager = SecretsManager()
        success = manager.initialize("vault")
        
        assert success is True
        assert manager._source == SecretSource.VAULT
        assert manager._initialized is True
    
    def test_initialization_vault_failure(self, monkeypatch):
        """Test Vault initialization failure."""
        # Mock hvac import and client that fails authentication
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = False
        
        monkeypatch.setattr("app.core.secrets.hvac", MagicMock(Client=lambda **kwargs: mock_client))
        monkeypatch.setattr("app.core.secrets.HAS_VAULT", True)
        
        # Set environment variables
        os.environ["VAULT_ADDR"] = "http://localhost:8200"
        os.environ["VAULT_TOKEN"] = "test-token"
        
        manager = SecretsManager()
        success = manager.initialize("vault")
        
        assert success is False
        assert manager._initialized is False
    
    def test_initialization_vault_no_url(self, monkeypatch):
        """Test Vault initialization without URL."""
        monkeypatch.setattr("app.core.secrets.HAS_VAULT", True)
        monkeypatch.setattr("app.core.secrets.hvac", MagicMock())
        monkeypatch.delenv("VAULT_ADDR", raising=False)
        monkeypatch.delenv("VAULT_TOKEN", raising=False)
        monkeypatch.delenv("VAULT_NAMESPACE", raising=False)
        manager = SecretsManager()
        success = manager.initialize("vault")
        
        assert success is False
        assert manager._initialized is False
    
    def test_get_secret_env_var(self):
        """Test getting secret from environment variables."""
        os.environ["SECRET_TEST_KEY"] = "test_value"
        
        manager = SecretsManager()
        manager._initialized = True
        manager._source = SecretSource.ENV_VAR
        
        result = manager.get_secret("TEST_KEY")
        assert result == "test_value"
    
    def test_get_secret_env_var_fallback(self):
        """Test getting secret with default fallback."""
        # No environment variable set
        manager = SecretsManager()
        manager._initialized = True
        manager._source = SecretSource.ENV_VAR
        
        result = manager.get_secret("NON_EXISTENT_KEY", default="fallback_value")
        assert result == "fallback_value"
    
    def test_get_secret_vault_success(self, monkeypatch):
        """Test getting secret from Vault."""
        # Mock vault client
        mock_response = {"data": {"data": {"TEST_KEY": "vault_value"}}}
        mock_client = MagicMock()
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_response
        
        monkeypatch.setattr("app.core.secrets.hvac", MagicMock(Client=lambda **kwargs: mock_client))
        monkeypatch.setattr("app.core.secrets.HAS_VAULT", True)
        
        manager = SecretsManager()
        manager._initialized = True
        manager._source = SecretSource.VAULT
        manager._vault_client = mock_client
        
        result = manager.get_secret("TEST_KEY")
        assert result == "vault_value"
    
    def test_get_secret_vault_failure_fallback(self, monkeypatch):
        """Test Vault lookup failure with environment variable fallback."""
        # Mock vault client that raises exception
        mock_client = MagicMock()
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception("Vault error")
        
        monkeypatch.setattr("app.core.secrets.hvac", MagicMock(Client=lambda **kwargs: mock_client))
        monkeypatch.setattr("app.core.secrets.HAS_VAULT", True)
        
        # Set environment variable fallback
        os.environ["SECRET_TEST_KEY"] = "env_fallback"
        
        manager = SecretsManager()
        manager._initialized = True
        manager._source = SecretSource.VAULT
        manager._vault_client = mock_client
        
        result = manager.get_secret("TEST_KEY", default="default_fallback")
        assert result == "env_fallback"  # Should fall back to environment variable
    
    def test_get_secret_not_initialized(self):
        """Test getting secret when manager is not initialized."""
        manager = SecretsManager()
        
        with pytest.raises(RuntimeError, match="Secrets manager not initialized"):
            manager.get_secret("TEST_KEY")

    def test_get_secret_azure_key_vault_name_normalization(self):
        """Azure Key Vault secret names should map underscores to hyphens."""
        manager = SecretsManager()
        manager._initialized = True
        manager._source = SecretSource.AZURE_KEY_VAULT
        manager._azure_client = MagicMock()
        manager._azure_client.get_secret.return_value = MagicMock(value="azure-secret-value")

        result = manager.get_secret("AZURE_STORAGE_CONNECTION_STRING")

        assert result == "azure-secret-value"
        manager._azure_client.get_secret.assert_called_once_with(
            "lms-azure-storage-connection-string"
        )

    def test_get_secret_azure_key_vault_fallback_default(self):
        """Azure Key Vault lookup errors should return default."""
        manager = SecretsManager()
        manager._initialized = True
        manager._source = SecretSource.AZURE_KEY_VAULT
        manager._azure_client = MagicMock()
        manager._azure_client.get_secret.side_effect = Exception("kv lookup failed")

        result = manager.get_secret("AZURE_STORAGE_ACCOUNT_KEY", default="fallback")

        assert result == "fallback"


class TestGlobalFunctions:
    def test_get_secret_global(self, monkeypatch):
        """Test global get_secret function."""
        # Mock the manager
        mock_manager = MagicMock()
        mock_manager.get_secret.return_value = "global_value"
        
        monkeypatch.setattr("app.core.secrets._secrets_manager", mock_manager)
        
        result = get_secret("TEST_KEY")
        assert result == "global_value"
        mock_manager.get_secret.assert_called_once_with("TEST_KEY", None, "secret/data/lms", "secret")
    
    def test_initialize_secrets_manager_global(self, monkeypatch):
        """Test global initialize_secrets_manager function."""
        mock_manager = MagicMock()
        mock_manager.initialize.return_value = True
        
        monkeypatch.setattr("app.core.secrets._secrets_manager", mock_manager)
        
        success = initialize_secrets_manager("env_var")
        assert success is True
        mock_manager.initialize.assert_called_once_with("env_var")
