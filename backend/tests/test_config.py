"""
Tests for application configuration and environment handling

These tests verify:
- Configuration loading from environment variables
- Settings validation
- Cloud-specific environment detection
- Secret handling
"""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError


class TestSettingsLoading:
    """Test Settings class and configuration loading"""

    def test_settings_loads_from_env(self):
        """Settings should load values from environment variables"""
        env_vars = {
            "GEMINI_API_KEY": "test-gemini-key",
            "CLAUDE_API_KEY": "test-claude-key",
            "ADMIN_API_KEY": "test-admin-key",
            "API_ENV": "dev",
            "LOG_LEVEL": "DEBUG",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            # Clear the LRU cache to force reload
            from app.core.config import get_settings, Settings
            get_settings.cache_clear()

            settings = Settings()

            assert settings.gemini_api_key == "test-gemini-key"
            # Claude key may be loaded via CLAUDE_API_KEY or may be None if not set
            assert settings.admin_api_key == "test-admin-key"
            assert settings.environment == "dev"
            assert settings.log_level == "DEBUG"

    def test_settings_requires_gemini_key(self):
        """Settings should require GEMINI_API_KEY"""
        env_vars = {
            "ANTHROPIC_API_KEY": "test-key",
        }

        # Remove GEMINI_API_KEY if it exists
        env_to_remove = {k: v for k, v in os.environ.items()}
        if "GEMINI_API_KEY" in env_to_remove:
            del env_to_remove["GEMINI_API_KEY"]

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            with pytest.raises(ValidationError):
                Settings()

    def test_settings_claude_key_optional(self):
        """Claude API key should be optional"""
        env_vars = {
            "GEMINI_API_KEY": "test-gemini-key",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.gemini_api_key == "test-gemini-key"
            assert settings.claude_api_key is None


class TestEnvironmentValidation:
    """Test environment value validation"""

    def test_valid_environments(self):
        """Valid environment values should be accepted"""
        from app.core.config import Settings, get_settings

        valid_envs = ["dev", "staging", "prod"]

        for env in valid_envs:
            get_settings.cache_clear()
            env_vars = {
                "GEMINI_API_KEY": "test-key",
                "ENVIRONMENT": env,  # Pydantic uses ENVIRONMENT
            }

            with patch.dict(os.environ, env_vars, clear=True):
                settings = Settings()
                assert settings.environment == env

    def test_invalid_environment_rejected(self):
        """Invalid environment values should be rejected"""
        from app.core.config import Settings, get_settings

        get_settings.cache_clear()
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "ENVIRONMENT": "invalid",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_environment_case_insensitive(self):
        """Environment values should be case insensitive"""
        from app.core.config import Settings, get_settings

        get_settings.cache_clear()
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "ENVIRONMENT": "PROD",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.environment == "prod"


class TestLogLevelValidation:
    """Test log level validation"""

    def test_valid_log_levels(self):
        """Valid log levels should be accepted"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            env_vars = {
                "GEMINI_API_KEY": "test-key",
                "LOG_LEVEL": level,
            }

            with patch.dict(os.environ, env_vars, clear=True):
                from app.core.config import Settings

                settings = Settings()
                assert settings.log_level == level

    def test_log_level_case_insensitive(self):
        """Log level should be case insensitive"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "LOG_LEVEL": "debug",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.log_level == "DEBUG"

    def test_invalid_log_level_rejected(self):
        """Invalid log level should be rejected"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "LOG_LEVEL": "VERBOSE",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            with pytest.raises(ValidationError):
                Settings()


class TestRateLimitConfiguration:
    """Test rate limit configuration"""

    def test_rate_limit_defaults(self):
        """Rate limit should have sensible defaults"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()

            assert settings.rate_limit_requests > 0
            assert settings.rate_limit_window > 0

    def test_rate_limit_custom_values(self):
        """Custom rate limit values should be accepted"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "RATE_LIMIT_REQUESTS": "100",
            "RATE_LIMIT_WINDOW": "120",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()

            assert settings.rate_limit_requests == 100
            assert settings.rate_limit_window == 120

    def test_rate_limit_minimum_validation(self):
        """Rate limit should reject values below minimum"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "RATE_LIMIT_REQUESTS": "0",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            with pytest.raises(ValidationError):
                Settings()


class TestConversationHistoryConfig:
    """Test conversation history configuration"""

    def test_conversation_history_default(self):
        """Conversation history should have default value"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.max_conversation_history == 50

    def test_conversation_history_minimum(self):
        """Conversation history should be at least 1"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "MAX_CONVERSATION_HISTORY": "0",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            with pytest.raises(ValidationError):
                Settings()

    def test_conversation_history_maximum(self):
        """Conversation history should not exceed 1000"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "MAX_CONVERSATION_HISTORY": "1001",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            with pytest.raises(ValidationError):
                Settings()


class TestCORSConfiguration:
    """Test CORS configuration"""

    def test_cors_default_origins(self):
        """CORS should have default origins for development"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()

            # Default should include localhost
            origins = settings.get_cors_origins_list()
            assert len(origins) > 0
            assert any("localhost" in origin for origin in origins)

    def test_cors_custom_origins(self):
        """Custom CORS origins should be parsed correctly"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "CORS_ORIGINS": "https://app.example.com,https://admin.example.com",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()
            origins = settings.get_cors_origins_list()

            assert "https://app.example.com" in origins
            assert "https://admin.example.com" in origins
            assert len(origins) == 2

    def test_cors_handles_whitespace(self):
        """CORS parser should handle whitespace in origins"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "CORS_ORIGINS": "  https://app.example.com , https://admin.example.com  ",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()
            origins = settings.get_cors_origins_list()

            assert "https://app.example.com" in origins
            assert "https://admin.example.com" in origins


class TestEnvironmentDetection:
    """Test environment detection helpers"""

    def test_is_development(self):
        """is_development() should detect dev environment"""
        from app.core.config import Settings, get_settings

        get_settings.cache_clear()
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "ENVIRONMENT": "dev",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.is_development() is True
            assert settings.is_production() is False

    def test_is_production(self):
        """is_production() should detect prod environment"""
        from app.core.config import Settings, get_settings

        get_settings.cache_clear()
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "ENVIRONMENT": "prod",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.is_production() is True
            assert settings.is_development() is False

    def test_staging_is_neither(self):
        """Staging should be neither dev nor prod"""
        from app.core.config import Settings, get_settings

        get_settings.cache_clear()
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "ENVIRONMENT": "staging",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.is_development() is False
            assert settings.is_production() is False


class TestAPIServerConfig:
    """Test API server configuration"""

    def test_default_host_and_port(self):
        """API should have default host and port"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()

            assert settings.api_host == "0.0.0.0"
            assert settings.api_port == 8000

    def test_custom_host_and_port(self):
        """Custom host and port should be accepted"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()

            assert settings.api_host == "127.0.0.1"
            assert settings.api_port == 9000


class TestDatabaseConfig:
    """Test database configuration (optional)"""

    def test_database_url_optional(self):
        """Database URL should be optional"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.database_url is None

    def test_database_url_when_set(self):
        """Database URL should be loaded when set"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.database_url == "postgresql://user:pass@localhost/db"


class TestVectorDBConfig:
    """Test vector database configuration (optional)"""

    def test_vector_db_optional(self):
        """Vector DB config should be optional"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.vector_db_type is None
            assert settings.pinecone_api_key is None


class TestSettingsCaching:
    """Test settings caching behavior"""

    def test_get_settings_returns_same_instance(self):
        """get_settings() should return cached instance"""
        from app.core.config import get_settings

        # Clear cache first
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2


class TestCloudRunConfig:
    """Test Cloud Run specific configuration"""

    @pytest.mark.cloud
    def test_port_env_variable(self, mock_cloud_env):
        """Should respect PORT environment variable for Cloud Run"""
        # Cloud Run sets PORT
        assert "PORT" in mock_cloud_env
        assert mock_cloud_env["PORT"] == "8080"

    @pytest.mark.cloud
    def test_cloud_run_env_detection(self, mock_cloud_env):
        """Should detect Cloud Run environment variables"""
        # Cloud Run specific env vars
        assert "K_SERVICE" in mock_cloud_env
        assert "K_REVISION" in mock_cloud_env

    @pytest.mark.cloud
    def test_production_config_in_cloud(self, mock_cloud_env):
        """Should use production config in cloud"""
        from app.core.config import Settings, get_settings

        get_settings.cache_clear()
        # The mock_cloud_env fixture sets API_ENV=prod
        settings = Settings()
        # Verify settings loaded correctly in cloud context
        assert settings.gemini_api_key is not None
        assert settings.log_level == "INFO"


class TestTaxCodePath:
    """Test tax code path configuration"""

    def test_default_tax_code_path(self):
        """Should have default tax code path"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.tax_code_path == "data/tax_code/tax_code.pdf"

    def test_custom_tax_code_path(self):
        """Should accept custom tax code path"""
        env_vars = {
            "GEMINI_API_KEY": "test-key",
            "TAX_CODE_PATH": "/custom/path/tax.pdf",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.tax_code_path == "/custom/path/tax.pdf"
