"""
Configuration Management Module
Handles loading configuration from YAML files and environment variables
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from pathlib import Path


@dataclass
class DockerConfig:
    """Docker-related configuration"""
    base_image_prefix: str = "lfcs-practice"
    default_distribution: str = "ubuntu"
    container_timeout: int = 3600  # 1 hour in seconds
    privileged: bool = True
    network_mode: str = "bridge"
    cleanup_on_exit: bool = True
    local_mode: bool = False  # Practice on host system without Docker
    images: Dict[str, str] = field(default_factory=lambda: {
        "ubuntu": "lfcs-practice-ubuntu:latest",
        "centos": "lfcs-practice-centos:latest",
        "rocky": "lfcs-practice-rocky:latest"
    })


@dataclass
class ValidationConfig:
    """Validation-related configuration"""
    use_ai_validation: bool = False
    use_rule_validation: bool = True
    hybrid_mode: bool = False
    timeout: int = 300  # 5 minutes


@dataclass
class ScoringConfig:
    """Scoring-related configuration"""
    passing_threshold: float = 0.70
    time_bonus: bool = True
    partial_credit: bool = True
    difficulty_multipliers: Dict[str, float] = field(default_factory=lambda: {
        "easy": 1.0,
        "medium": 1.5,
        "hard": 2.0
    })


@dataclass
class AIConfig:
    """AI-related configuration (optional)"""
    provider: str = "anthropic"
    api_key: Optional[str] = None
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 2000
    generate_on_demand: bool = True
    fallback_to_static: bool = True


@dataclass
class Config:
    """Main configuration class"""
    # Paths
    scenarios_path: str = "scenarios"
    database_path: str = "database/progress.db"
    logs_path: str = "logs"
    validation_scripts_path: str = "docker/validation_scripts"
    
    # Component configurations
    docker_config: DockerConfig = field(default_factory=DockerConfig)
    validation_config: ValidationConfig = field(default_factory=ValidationConfig)
    scoring_config: ScoringConfig = field(default_factory=ScoringConfig)
    
    # AI configuration (optional)
    ai_enabled: bool = False
    ai_config: Optional[AIConfig] = None
    
    # General settings
    project_name: str = "LFCS Practice Tool"
    version: str = "1.0.0"
    default_user: str = "student"
    log_level: str = "INFO"
    
    # Scenario settings
    categories: List[str] = field(default_factory=lambda: [
        "operations_deployment",
        "networking",
        "storage",
        "essential_commands",
        "users_groups"
    ])
    difficulties: List[str] = field(default_factory=lambda: ["easy", "medium", "hard"])


class ConfigLoader:
    """Loads and manages configuration from multiple sources"""
    
    def __init__(self, config_path: str = "config/config.yaml", 
                 ai_config_path: str = "config/ai_config.yaml"):
        self.config_path = config_path
        self.ai_config_path = ai_config_path
    
    def load(self) -> Config:
        """
        Load configuration with precedence: defaults < config file < environment variables
        """
        # Start with default config
        config = Config()
        
        # Load from YAML file if it exists
        if os.path.exists(self.config_path):
            config = self._load_from_yaml(config)
        
        # Override with environment variables
        config = self._override_from_env(config)
        
        # Load AI config if enabled
        if config.ai_enabled:
            config.ai_config = self._load_ai_config()
        
        # Validate configuration
        self._validate_config(config)
        
        return config
    
    def _load_from_yaml(self, config: Config) -> Config:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                yaml_data = yaml.safe_load(f)
            
            if not yaml_data:
                return config
            
            # General settings
            if 'general' in yaml_data:
                general = yaml_data['general']
                config.project_name = general.get('project_name', config.project_name)
                config.version = general.get('version', config.version)
                config.default_user = general.get('default_user', config.default_user)
            
            # Docker configuration
            if 'docker' in yaml_data:
                docker = yaml_data['docker']
                # Extract distribution name from default_image
                default_image = docker.get('default_image', config.docker_config.default_distribution)
                # If it's a full image name like "lfcs-practice-ubuntu:latest", extract just "ubuntu"
                if 'ubuntu' in default_image.lower():
                    config.docker_config.default_distribution = 'ubuntu'
                elif 'centos' in default_image.lower():
                    config.docker_config.default_distribution = 'centos'
                elif 'rocky' in default_image.lower():
                    config.docker_config.default_distribution = 'rocky'
                
                config.docker_config.network_mode = docker.get('network_mode', 
                    config.docker_config.network_mode)
                config.docker_config.cleanup_on_exit = docker.get('cleanup_on_exit', 
                    config.docker_config.cleanup_on_exit)
                config.docker_config.local_mode = docker.get('local_mode',
                    config.docker_config.local_mode)
                if 'images' in docker:
                    config.docker_config.images = docker['images']
            
            # Scenarios configuration
            if 'scenarios' in yaml_data:
                scenarios = yaml_data['scenarios']
                if 'categories' in scenarios:
                    config.categories = scenarios['categories']
                if 'difficulties' in scenarios:
                    config.difficulties = scenarios['difficulties']
            
            # Scoring configuration
            if 'scoring' in yaml_data:
                scoring = yaml_data['scoring']
                config.scoring_config.passing_threshold = scoring.get('passing_threshold',
                    config.scoring_config.passing_threshold)
                config.scoring_config.time_bonus = scoring.get('time_bonus',
                    config.scoring_config.time_bonus)
                config.scoring_config.partial_credit = scoring.get('partial_credit',
                    config.scoring_config.partial_credit)
            
            # Validation configuration
            if 'validation' in yaml_data:
                validation = yaml_data['validation']
                config.validation_config.use_ai_validation = validation.get('use_ai_validation',
                    config.validation_config.use_ai_validation)
                config.validation_config.use_rule_validation = validation.get('use_rule_validation',
                    config.validation_config.use_rule_validation)
                config.validation_config.hybrid_mode = validation.get('hybrid_mode',
                    config.validation_config.hybrid_mode)
            
            # AI configuration
            if 'ai' in yaml_data:
                ai = yaml_data['ai']
                config.ai_enabled = ai.get('generate_on_demand', False) or ai.get('use_ai_validation', False)
                if config.ai_config is None:
                    config.ai_config = AIConfig()
                config.ai_config.model = ai.get('model', config.ai_config.model)
                config.ai_config.max_tokens = ai.get('max_tokens', config.ai_config.max_tokens)
                config.ai_config.generate_on_demand = ai.get('generate_on_demand',
                    config.ai_config.generate_on_demand)
                config.ai_config.fallback_to_static = ai.get('fallback_to_static',
                    config.ai_config.fallback_to_static)
            
            return config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration file: {e}")
    
    def _load_ai_config(self) -> AIConfig:
        """Load AI-specific configuration"""
        ai_config = AIConfig()
        
        # Try to load from ai_config.yaml if it exists
        if os.path.exists(self.ai_config_path):
            try:
                with open(self.ai_config_path, 'r') as f:
                    yaml_data = yaml.safe_load(f)
                
                if yaml_data:
                    ai_config.provider = yaml_data.get('provider', ai_config.provider)
                    ai_config.model = yaml_data.get('model', ai_config.model)
                    ai_config.temperature = yaml_data.get('temperature', ai_config.temperature)
                    ai_config.max_tokens = yaml_data.get('max_tokens', ai_config.max_tokens)
                    # Don't load API key from file for security
            except Exception as e:
                print(f"Warning: Could not load AI config file: {e}")
        
        # Override with environment variable (takes precedence)
        if 'ANTHROPIC_API_KEY' in os.environ:
            ai_config.api_key = os.environ['ANTHROPIC_API_KEY']
            ai_config.provider = 'anthropic'
        elif 'OPENAI_API_KEY' in os.environ:
            ai_config.api_key = os.environ['OPENAI_API_KEY']
            ai_config.provider = 'openai'
        
        return ai_config
    
    def _override_from_env(self, config: Config) -> Config:
        """Override configuration with environment variables"""
        # Database path
        if 'DB_PATH' in os.environ:
            config.database_path = os.environ['DB_PATH']
        
        # Logs path
        if 'LOGS_PATH' in os.environ:
            config.logs_path = os.environ['LOGS_PATH']
        
        # Log level
        if 'LOG_LEVEL' in os.environ:
            config.log_level = os.environ['LOG_LEVEL']
        
        # Docker configuration
        if 'DEFAULT_IMAGE' in os.environ:
            default_image = os.environ['DEFAULT_IMAGE']
            # Extract distribution name from image
            if 'ubuntu' in default_image.lower():
                config.docker_config.default_distribution = 'ubuntu'
            elif 'centos' in default_image.lower():
                config.docker_config.default_distribution = 'centos'
            elif 'rocky' in default_image.lower():
                config.docker_config.default_distribution = 'rocky'
        
        if 'CONTAINER_NETWORK' in os.environ:
            config.docker_config.network_mode = os.environ['CONTAINER_NETWORK']
        
        if 'CONTAINER_TIMEOUT' in os.environ:
            try:
                config.docker_config.container_timeout = int(os.environ['CONTAINER_TIMEOUT'])
            except ValueError:
                print(f"Warning: Invalid CONTAINER_TIMEOUT value, using default")
        
        if 'DOCKER_PRIVILEGED' in os.environ:
            config.docker_config.privileged = os.environ['DOCKER_PRIVILEGED'].lower() in ('true', '1', 'yes')
        
        if 'LOCAL_MODE' in os.environ:
            config.docker_config.local_mode = os.environ['LOCAL_MODE'].lower() in ('true', '1', 'yes')
        
        # Validation configuration
        if 'USE_AI_VALIDATION' in os.environ:
            config.validation_config.use_ai_validation = os.environ['USE_AI_VALIDATION'].lower() in ('true', '1', 'yes')
        
        if 'VALIDATION_TIMEOUT' in os.environ:
            try:
                config.validation_config.timeout = int(os.environ['VALIDATION_TIMEOUT'])
            except ValueError:
                print(f"Warning: Invalid VALIDATION_TIMEOUT value, using default")
        
        # Scoring configuration
        if 'PASSING_THRESHOLD' in os.environ:
            try:
                config.scoring_config.passing_threshold = float(os.environ['PASSING_THRESHOLD'])
            except ValueError:
                print(f"Warning: Invalid PASSING_THRESHOLD value, using default")
        
        if 'TIME_BONUS' in os.environ:
            config.scoring_config.time_bonus = os.environ['TIME_BONUS'].lower() in ('true', '1', 'yes')
        
        # AI enabled flag
        if 'AI_ENABLED' in os.environ:
            config.ai_enabled = os.environ['AI_ENABLED'].lower() in ('true', '1', 'yes')
        
        # Enable AI if API key is present
        if 'ANTHROPIC_API_KEY' in os.environ or 'OPENAI_API_KEY' in os.environ:
            config.ai_enabled = True
        
        return config
    
    def _validate_config(self, config: Config) -> None:
        """Validate configuration values"""
        # Validate paths exist or can be created
        for path_attr in ['scenarios_path', 'logs_path']:
            path = getattr(config, path_attr)
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except Exception as e:
                    raise ValueError(f"Cannot create directory {path}: {e}")
        
        # Validate database path directory exists
        db_dir = os.path.dirname(config.database_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Cannot create database directory {db_dir}: {e}")
        
        # Validate scoring threshold
        if not 0.0 <= config.scoring_config.passing_threshold <= 1.0:
            raise ValueError(f"Passing threshold must be between 0.0 and 1.0, got {config.scoring_config.passing_threshold}")
        
        # Validate difficulty multipliers
        for difficulty in config.difficulties:
            if difficulty not in config.scoring_config.difficulty_multipliers:
                print(f"Warning: No difficulty multiplier for '{difficulty}', using 1.0")
                config.scoring_config.difficulty_multipliers[difficulty] = 1.0
        
        # Validate AI configuration if enabled
        if config.ai_enabled:
            if config.ai_config is None:
                config.ai_config = AIConfig()
            
            if not config.ai_config.api_key:
                print("Warning: AI enabled but no API key provided. AI features will be disabled.")
                config.ai_enabled = False
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if config.log_level.upper() not in valid_log_levels:
            print(f"Warning: Invalid log level '{config.log_level}', using INFO")
            config.log_level = 'INFO'


def load_config(config_path: str = "config/config.yaml",
                ai_config_path: str = "config/ai_config.yaml") -> Config:
    """
    Convenience function to load configuration
    
    Args:
        config_path: Path to main configuration file
        ai_config_path: Path to AI configuration file
    
    Returns:
        Loaded and validated Config object
    """
    loader = ConfigLoader(config_path, ai_config_path)
    return loader.load()
