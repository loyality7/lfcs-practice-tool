"""
Unit and property-based tests for configuration management
"""

import os
import tempfile
import yaml
import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path

from src.utils.config import (
    Config,
    DockerConfig,
    ValidationConfig,
    ScoringConfig,
    AIConfig,
    ConfigLoader,
    load_config
)


# Hypothesis strategies for generating test data
@st.composite
def config_value_strategy(draw):
    """Generate various configuration values"""
    return draw(st.one_of(
        st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=['\x00', '\n', '\r'])),
        st.integers(min_value=1, max_value=10000),
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        st.booleans()
    ))


@st.composite
def env_var_name_strategy(draw):
    """Generate valid environment variable names"""
    # Use a subset of actual config env vars
    return draw(st.sampled_from([
        'DB_PATH',
        'LOGS_PATH',
        'LOG_LEVEL',
        'CONTAINER_TIMEOUT',
        'CONTAINER_NETWORK',
        'PASSING_THRESHOLD',
        'TIME_BONUS',
        'USE_AI_VALIDATION',
        'VALIDATION_TIMEOUT',
        'AI_ENABLED'
    ]))


class TestConfigBasics:
    """Basic unit tests for configuration"""
    
    def test_default_config_creation(self):
        """Test that default config can be created"""
        config = Config()
        assert config.project_name == "LFCS Practice Tool"
        assert config.database_path == "database/progress.db"
        assert config.docker_config.default_distribution == "ubuntu"
        assert len(config.categories) == 5
        assert len(config.difficulties) == 3
    
    def test_docker_config_defaults(self):
        """Test Docker configuration defaults"""
        docker_config = DockerConfig()
        assert docker_config.default_distribution == "ubuntu"
        assert docker_config.container_timeout == 3600
        assert docker_config.privileged is True
        assert "ubuntu" in docker_config.images
        assert "centos" in docker_config.images
        assert "rocky" in docker_config.images
    
    def test_validation_config_defaults(self):
        """Test validation configuration defaults"""
        val_config = ValidationConfig()
        assert val_config.use_rule_validation is True
        assert val_config.timeout == 300
    
    def test_scoring_config_defaults(self):
        """Test scoring configuration defaults"""
        scoring_config = ScoringConfig()
        assert scoring_config.passing_threshold == 0.70
        assert scoring_config.time_bonus is True
        assert scoring_config.difficulty_multipliers["easy"] == 1.0
        assert scoring_config.difficulty_multipliers["medium"] == 1.5
        assert scoring_config.difficulty_multipliers["hard"] == 2.0


class TestConfigLoading:
    """Tests for loading configuration from files"""
    
    def test_load_from_yaml(self):
        """Test loading configuration from YAML file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            
            # Create a test config file
            test_config = {
                'general': {
                    'project_name': 'Test Project',
                    'version': '2.0.0'
                },
                'docker': {
                    'network_mode': 'host',
                    'cleanup_on_exit': False
                },
                'scoring': {
                    'passing_threshold': 0.80,
                    'time_bonus': False
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            # Load config
            loader = ConfigLoader(config_path=config_path)
            config = loader.load()
            
            assert config.project_name == 'Test Project'
            assert config.version == '2.0.0'
            assert config.docker_config.network_mode == 'host'
            assert config.docker_config.cleanup_on_exit is False
            assert config.scoring_config.passing_threshold == 0.80
            assert config.scoring_config.time_bonus is False
    
    def test_load_with_missing_file(self):
        """Test loading when config file doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "nonexistent.yaml")
            loader = ConfigLoader(config_path=config_path)
            config = loader.load()
            
            # Should use defaults
            assert config.project_name == "LFCS Practice Tool"
            assert config.docker_config.default_distribution == "ubuntu"
    
    def test_invalid_yaml_raises_error(self):
        """Test that invalid YAML raises an error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "invalid.yaml")
            
            # Write invalid YAML
            with open(config_path, 'w') as f:
                f.write("invalid: yaml: content: [unclosed")
            
            loader = ConfigLoader(config_path=config_path)
            with pytest.raises(ValueError, match="Error parsing YAML"):
                loader.load()


class TestEnvironmentOverrides:
    """Tests for environment variable overrides"""
    
    def test_env_override_db_path(self):
        """Test that DB_PATH environment variable overrides config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            db_path = os.path.join(tmpdir, "custom_db", "path.db")
            
            # Create config file with different db_path
            test_config = {'general': {'project_name': 'Test'}}
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            # Set environment variable
            old_env = os.environ.get('DB_PATH')
            try:
                os.environ['DB_PATH'] = db_path
                
                loader = ConfigLoader(config_path=config_path)
                config = loader.load()
                
                assert config.database_path == db_path
            finally:
                if old_env:
                    os.environ['DB_PATH'] = old_env
                else:
                    os.environ.pop('DB_PATH', None)
    
    def test_env_override_log_level(self):
        """Test that LOG_LEVEL environment variable overrides config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            
            test_config = {'general': {'project_name': 'Test'}}
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            old_env = os.environ.get('LOG_LEVEL')
            try:
                os.environ['LOG_LEVEL'] = 'DEBUG'
                
                loader = ConfigLoader(config_path=config_path)
                config = loader.load()
                
                assert config.log_level == 'DEBUG'
            finally:
                if old_env:
                    os.environ['LOG_LEVEL'] = old_env
                else:
                    os.environ.pop('LOG_LEVEL', None)
    
    def test_env_override_container_timeout(self):
        """Test that CONTAINER_TIMEOUT environment variable overrides config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            
            test_config = {
                'docker': {
                    'default_image': 'ubuntu:22.04'
                }
            }
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            old_env = os.environ.get('CONTAINER_TIMEOUT')
            try:
                os.environ['CONTAINER_TIMEOUT'] = '7200'
                
                loader = ConfigLoader(config_path=config_path)
                config = loader.load()
                
                assert config.docker_config.container_timeout == 7200
            finally:
                if old_env:
                    os.environ['CONTAINER_TIMEOUT'] = old_env
                else:
                    os.environ.pop('CONTAINER_TIMEOUT', None)
    
    def test_env_override_boolean_values(self):
        """Test that boolean environment variables work correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            
            test_config = {
                'scoring': {
                    'time_bonus': True
                }
            }
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            old_env = os.environ.get('TIME_BONUS')
            try:
                # Test various boolean representations
                for false_value in ['false', '0', 'no', 'False']:
                    os.environ['TIME_BONUS'] = false_value
                    loader = ConfigLoader(config_path=config_path)
                    config = loader.load()
                    assert config.scoring_config.time_bonus is False
                
                for true_value in ['true', '1', 'yes', 'True']:
                    os.environ['TIME_BONUS'] = true_value
                    loader = ConfigLoader(config_path=config_path)
                    config = loader.load()
                    assert config.scoring_config.time_bonus is True
            finally:
                if old_env:
                    os.environ['TIME_BONUS'] = old_env
                else:
                    os.environ.pop('TIME_BONUS', None)


class TestPropertyBasedConfigOverride:
    """Property-based tests for configuration override precedence"""
    
    # Feature: lfcs-practice-environment, Property 12: Configuration override precedence
    @given(
        db_path=st.text(min_size=5, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            blacklist_characters=['\x00', '\n', '\r', '|', '<', '>', '"', '?', '*']
        )).map(lambda s: f"/tmp/test_{s}.db"),
        log_level=st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
        timeout=st.integers(min_value=60, max_value=7200),
        threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=None)
    def test_env_always_overrides_yaml(self, db_path, log_level, timeout, threshold):
        """
        Property: For any configuration setting, when both a config file value 
        and an environment variable are present, the environment variable value 
        should take precedence.
        
        Validates: Requirements 10.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            
            # Create YAML config with different values
            yaml_config = {
                'general': {
                    'project_name': 'YAML Project'
                },
                'docker': {
                    'network_mode': 'bridge'
                },
                'scoring': {
                    'passing_threshold': 0.5  # Different from env value
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(yaml_config, f)
            
            # Store old environment values
            old_env = {
                'DB_PATH': os.environ.get('DB_PATH'),
                'LOG_LEVEL': os.environ.get('LOG_LEVEL'),
                'CONTAINER_TIMEOUT': os.environ.get('CONTAINER_TIMEOUT'),
                'PASSING_THRESHOLD': os.environ.get('PASSING_THRESHOLD')
            }
            
            try:
                # Set environment variables
                os.environ['DB_PATH'] = db_path
                os.environ['LOG_LEVEL'] = log_level
                os.environ['CONTAINER_TIMEOUT'] = str(timeout)
                os.environ['PASSING_THRESHOLD'] = str(threshold)
                
                # Load config
                loader = ConfigLoader(config_path=config_path)
                config = loader.load()
                
                # Verify environment variables take precedence
                assert config.database_path == db_path, \
                    f"DB_PATH should be {db_path} from env, not from YAML"
                assert config.log_level == log_level, \
                    f"LOG_LEVEL should be {log_level} from env, not from YAML"
                assert config.docker_config.container_timeout == timeout, \
                    f"CONTAINER_TIMEOUT should be {timeout} from env, not from YAML"
                assert abs(config.scoring_config.passing_threshold - threshold) < 0.001, \
                    f"PASSING_THRESHOLD should be {threshold} from env, not 0.5 from YAML"
                
                # Verify YAML values that weren't overridden are still present
                assert config.project_name == 'YAML Project', \
                    "Non-overridden YAML values should still be loaded"
                
            finally:
                # Restore environment
                for key, value in old_env.items():
                    if value is not None:
                        os.environ[key] = value
                    else:
                        os.environ.pop(key, None)
    
    # Feature: lfcs-practice-environment, Property 12: Configuration override precedence
    @given(
        network_mode=st.sampled_from(['bridge', 'host', 'none']),
        time_bonus=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_env_override_with_defaults(self, network_mode, time_bonus):
        """
        Property: When only environment variables are set (no config file),
        environment variables should override default values.
        
        Validates: Requirements 10.3, 10.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use non-existent config file to test defaults
            config_path = os.path.join(tmpdir, "nonexistent.yaml")
            
            old_env = {
                'CONTAINER_NETWORK': os.environ.get('CONTAINER_NETWORK'),
                'TIME_BONUS': os.environ.get('TIME_BONUS')
            }
            
            try:
                # Set environment variables
                os.environ['CONTAINER_NETWORK'] = network_mode
                os.environ['TIME_BONUS'] = 'true' if time_bonus else 'false'
                
                # Load config
                loader = ConfigLoader(config_path=config_path)
                config = loader.load()
                
                # Verify environment variables override defaults
                assert config.docker_config.network_mode == network_mode, \
                    f"Network mode should be {network_mode} from env, not default 'bridge'"
                assert config.scoring_config.time_bonus == time_bonus, \
                    f"Time bonus should be {time_bonus} from env, not default True"
                
            finally:
                # Restore environment
                for key, value in old_env.items():
                    if value is not None:
                        os.environ[key] = value
                    else:
                        os.environ.pop(key, None)


class TestConfigValidation:
    """Tests for configuration validation"""
    
    def test_invalid_passing_threshold_raises_error(self):
        """Test that invalid passing threshold raises error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            
            test_config = {
                'scoring': {
                    'passing_threshold': 1.5  # Invalid: > 1.0
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            loader = ConfigLoader(config_path=config_path)
            with pytest.raises(ValueError, match="Passing threshold must be between"):
                loader.load()
    
    def test_directories_created_if_missing(self):
        """Test that missing directories are created during validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            logs_path = os.path.join(tmpdir, "custom_logs")
            scenarios_path = os.path.join(tmpdir, "custom_scenarios")
            
            test_config = {
                'general': {
                    'project_name': 'Test'
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            old_env = {
                'LOGS_PATH': os.environ.get('LOGS_PATH'),
            }
            
            try:
                os.environ['LOGS_PATH'] = logs_path
                
                loader = ConfigLoader(config_path=config_path)
                config = loader.load()
                
                # Verify directories were created
                assert os.path.exists(logs_path)
                
            finally:
                for key, value in old_env.items():
                    if value is not None:
                        os.environ[key] = value
                    else:
                        os.environ.pop(key, None)


class TestAIConfig:
    """Tests for AI configuration"""
    
    def test_ai_config_from_env(self):
        """Test AI configuration from environment variables"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            
            test_config = {'general': {'project_name': 'Test'}}
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            old_env = os.environ.get('ANTHROPIC_API_KEY')
            try:
                os.environ['ANTHROPIC_API_KEY'] = 'test-api-key-12345'
                
                loader = ConfigLoader(config_path=config_path)
                config = loader.load()
                
                assert config.ai_enabled is True
                assert config.ai_config is not None
                assert config.ai_config.api_key == 'test-api-key-12345'
                assert config.ai_config.provider == 'anthropic'
                
            finally:
                if old_env:
                    os.environ['ANTHROPIC_API_KEY'] = old_env
                else:
                    os.environ.pop('ANTHROPIC_API_KEY', None)
    
    def test_ai_disabled_without_api_key(self):
        """Test that AI is disabled when no API key is provided"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            
            test_config = {
                'ai': {
                    'generate_on_demand': True
                }
            }
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            # Ensure no API keys in environment
            old_env = {
                'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY'),
                'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY')
            }
            
            try:
                os.environ.pop('ANTHROPIC_API_KEY', None)
                os.environ.pop('OPENAI_API_KEY', None)
                
                loader = ConfigLoader(config_path=config_path)
                config = loader.load()
                
                # AI should be disabled without API key
                assert config.ai_enabled is False
                
            finally:
                for key, value in old_env.items():
                    if value is not None:
                        os.environ[key] = value
