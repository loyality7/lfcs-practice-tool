"""
Scenario Loader - Loads and manages scenarios from YAML files
"""

import os
import yaml
import random
import logging
from typing import List, Dict, Optional
from pathlib import Path

from .models import Scenario, ValidationRules
from ..utils.error_handler import ErrorHandler, ErrorContext
from .context_generator import ContextGenerator
from jinja2 import Template


logger = logging.getLogger(__name__)


class ScenarioLoader:
    """
    Loads, parses, and manages scenario definitions from YAML files
    """
    
    def __init__(self, scenarios_path: str = "scenarios"):
        self.scenarios_path = scenarios_path
        self._scenarios: Dict[str, List[Scenario]] = {}
        self._scenarios_by_id: Dict[str, Scenario] = {}
        self._loaded = False
        self.error_handler = ErrorHandler()
        self.context_generator = ContextGenerator()
    
    def load_all(self) -> Dict[str, List[Scenario]]:
        """
        Load all scenarios from YAML files organized by category
        
        Returns:
            Dictionary mapping category names to lists of scenarios
        """
        if self._loaded:
            return self._scenarios
        
        self._scenarios = {}
        self._scenarios_by_id = {}
        
        if not os.path.exists(self.scenarios_path):
            raise FileNotFoundError(f"Scenarios directory not found: {self.scenarios_path}")
        
        # Walk through scenarios directory
        for root, dirs, files in os.walk(self.scenarios_path):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml'):
                    file_path = os.path.join(root, file)
                    try:
                        scenarios = self._load_file(file_path)
                        for scenario in scenarios:
                            # Add to category dict
                            if scenario.category not in self._scenarios:
                                self._scenarios[scenario.category] = []
                            self._scenarios[scenario.category].append(scenario)
                            
                            # Add to ID lookup
                            if scenario.id in self._scenarios_by_id:
                                print(f"Warning: Duplicate scenario ID '{scenario.id}' in {file_path}")
                            self._scenarios_by_id[scenario.id] = scenario
                    
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {e}")
                        
                        # Use error handler for better error reporting
                        context = ErrorContext(
                            user_action="load_scenario_file",
                            additional_info={'file_path': file_path}
                        )
                        response = self.error_handler.handle_error(e, context)
                        print(f"Warning: {response.user_message}")
                        # Continue loading other files
        
        self._loaded = True
        return self._scenarios
    
    def _load_file(self, file_path: str) -> List[Scenario]:
        """
        Load scenarios from a single YAML file
        
        Args:
            file_path: Path to YAML file
        
        Returns:
            List of Scenario objects
        """
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Generate context and render template
        context = self.context_generator.generate()
        template = Template(content)
        rendered_content = template.render(**context)
        
        data = yaml.safe_load(rendered_content)
        
        if not data:
            return []
        
        scenarios = []
        
        # Handle both single scenario and list of scenarios
        if isinstance(data, dict):
            # Single scenario
            scenario = self._parse_scenario(data, file_path)
            if scenario:
                scenarios.append(scenario)
        elif isinstance(data, list):
            # Multiple scenarios
            for item in data:
                scenario = self._parse_scenario(item, file_path)
                if scenario:
                    scenarios.append(scenario)
        else:
            raise ValueError(f"Invalid YAML structure in {file_path}")
        
        return scenarios
    
    def _parse_scenario(self, data: Dict, file_path: str) -> Optional[Scenario]:
        """
        Parse a scenario from dictionary data
        
        Args:
            data: Dictionary containing scenario data
            file_path: Path to source file (for error messages)
        
        Returns:
            Scenario object or None if parsing fails
        """
        try:
            scenario = Scenario.from_dict(data)
            
            # Validate structure
            errors = scenario.validate_structure()
            if errors:
                print(f"Validation errors in {file_path}:")
                for error in errors:
                    print(f"  - {error}")
                return None
            
            return scenario
        
        except Exception as e:
            print(f"Error parsing scenario in {file_path}: {e}")
            return None
    
    def get_scenario(self, category: Optional[str] = None, 
                    difficulty: Optional[str] = None,
                    distribution: Optional[str] = None) -> Optional[Scenario]:
        """
        Get a random scenario matching the specified criteria
        
        Args:
            category: Optional category filter
            difficulty: Optional difficulty filter
            distribution: Optional distribution filter
        
        Returns:
            Random matching scenario or None if no matches
        """
        # Ensure scenarios are loaded
        if not self._loaded:
            self.load_all()
        
        # Get all scenarios
        all_scenarios = []
        if category:
            all_scenarios = self._scenarios.get(category, [])
        else:
            for scenarios in self._scenarios.values():
                all_scenarios.extend(scenarios)
        
        # Filter by difficulty
        if difficulty:
            all_scenarios = [s for s in all_scenarios if s.difficulty == difficulty]
        
        # Filter by distribution (None means compatible with all)
        if distribution:
            all_scenarios = [
                s for s in all_scenarios 
                if s.distribution is None or s.distribution == distribution
            ]
        
        # Return random scenario
        if all_scenarios:
            return random.choice(all_scenarios)
        
        return None
    
    def get_by_id(self, scenario_id: str) -> Optional[Scenario]:
        """
        Get a specific scenario by ID
        
        Args:
            scenario_id: Scenario ID
        
        Returns:
            Scenario object or None if not found
        """
        # Ensure scenarios are loaded
        if not self._loaded:
            self.load_all()
        
        return self._scenarios_by_id.get(scenario_id)
    
    def list_scenarios(self, category: Optional[str] = None,
                      difficulty: Optional[str] = None) -> List[Scenario]:
        """
        List all scenarios matching criteria
        
        Args:
            category: Optional category filter
            difficulty: Optional difficulty filter
        
        Returns:
            List of matching scenarios
        """
        # Ensure scenarios are loaded
        if not self._loaded:
            self.load_all()
        
        # Get scenarios
        if category:
            scenarios = self._scenarios.get(category, [])
        else:
            scenarios = []
            for cat_scenarios in self._scenarios.values():
                scenarios.extend(cat_scenarios)
        
        # Filter by difficulty
        if difficulty:
            scenarios = [s for s in scenarios if s.difficulty == difficulty]
        
        return scenarios
    
    def get_categories(self) -> List[str]:
        """
        Get list of all available categories
        
        Returns:
            List of category names
        """
        if not self._loaded:
            self.load_all()
        
        return list(self._scenarios.keys())
    
    def get_scenario_count(self, category: Optional[str] = None) -> int:
        """
        Get count of scenarios, optionally filtered by category
        
        Args:
            category: Optional category filter
        
        Returns:
            Number of scenarios
        """
        if not self._loaded:
            self.load_all()
        
        if category:
            return len(self._scenarios.get(category, []))
        else:
            return sum(len(scenarios) for scenarios in self._scenarios.values())
    
    def validate_scenario_file(self, file_path: str) -> List[str]:
        """
        Validate a scenario YAML file without loading it into the system
        
        Args:
            file_path: Path to YAML file
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                errors.append("File is empty")
                return errors
            
            # Handle both single and multiple scenarios
            scenarios_data = data if isinstance(data, list) else [data]
            
            for idx, scenario_data in enumerate(scenarios_data):
                try:
                    scenario = Scenario.from_dict(scenario_data)
                    validation_errors = scenario.validate_structure()
                    if validation_errors:
                        errors.append(f"Scenario {idx + 1}:")
                        errors.extend([f"  - {e}" for e in validation_errors])
                except Exception as e:
                    errors.append(f"Scenario {idx + 1}: {str(e)}")
        
        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error: {e}")
        except Exception as e:
            errors.append(f"Error: {e}")
        
        return errors
