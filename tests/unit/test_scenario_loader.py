"""
Unit and property-based tests for scenario loader and YAML parsing
"""

import os
import tempfile
import yaml
import pytest
from hypothesis import given, strategies as st, settings, assume

from src.core.models import (
    Scenario,
    ValidationRules,
    CommandCheck,
    FileCheck,
    ServiceCheck,
    CustomCheck
)
from src.core.scenario_loader import ScenarioLoader


# Hypothesis strategies
@st.composite
def valid_scenario_dict_strategy(draw):
    """Generate valid scenario dictionaries"""
    category = draw(st.sampled_from(['networking', 'storage', 'users_groups',
                                     'operations_deployment', 'essential_commands']))
    difficulty = draw(st.sampled_from(['easy', 'medium', 'hard']))
    scenario_id = f"{category}_{draw(st.integers(min_value=1, max_value=999)):03d}"
    
    return {
        'id': scenario_id,
        'category': category,
        'difficulty': difficulty,
        'task': draw(st.text(min_size=10, max_size=200)),
        'points': draw(st.integers(min_value=1, max_value=100)),
        'validation': {
            'checks': [
                {
                    'type': 'command',
                    'command': 'echo test',
                    'expected_output': 'test'
                }
            ]
        }
    }


class TestScenarioModels:
    """Tests for scenario data models"""
    
    def test_command_check_creation(self):
        """Test creating a CommandCheck"""
        check = CommandCheck(
            command="ls -la",
            expected_output="total",
            expected_exit_code=0
        )
        
        assert check.command == "ls -la"
        assert check.expected_output == "total"
        assert check.expected_exit_code == 0
    
    def test_file_check_creation(self):
        """Test creating a FileCheck"""
        check = FileCheck(
            path="/etc/passwd",
            should_exist=True,
            permissions="0644",
            owner="root"
        )
        
        assert check.path == "/etc/passwd"
        assert check.should_exist is True
        assert check.permissions == "0644"
        assert check.owner == "root"
    
    def test_service_check_creation(self):
        """Test creating a ServiceCheck"""
        check = ServiceCheck(
            service_name="sshd",
            should_be_running=True,
            should_be_enabled=True
        )
        
        assert check.service_name == "sshd"
        assert check.should_be_running is True
        assert check.should_be_enabled is True
    
    def test_scenario_from_dict(self):
        """Test creating scenario from dictionary"""
        data = {
            'id': 'test_001',
            'category': 'networking',
            'difficulty': 'easy',
            'task': 'Test task',
            'points': 10,
            'validation': {
                'checks': [
                    {
                        'type': 'command',
                        'command': 'echo test',
                        'expected_output': 'test'
                    }
                ]
            }
        }
        
        scenario = Scenario.from_dict(data)
        
        assert scenario.id == 'test_001'
        assert scenario.category == 'networking'
        assert scenario.difficulty == 'easy'
        assert scenario.points == 10
        assert len(scenario.validation.checks) == 1
    
    def test_scenario_validation_valid(self):
        """Test scenario validation with valid data"""
        scenario = Scenario(
            id='test_001',
            category='networking',
            difficulty='easy',
            task='Test task',
            points=10,
            validation=ValidationRules(checks=[
                CommandCheck(command='echo test')
            ])
        )
        
        errors = scenario.validate_structure()
        assert len(errors) == 0
    
    def test_scenario_validation_invalid_category(self):
        """Test scenario validation with invalid category"""
        scenario = Scenario(
            id='test_001',
            category='invalid_category',
            difficulty='easy',
            task='Test task',
            points=10,
            validation=ValidationRules(checks=[
                CommandCheck(command='echo test')
            ])
        )
        
        errors = scenario.validate_structure()
        assert len(errors) > 0
        assert any('category' in e.lower() for e in errors)
    
    def test_scenario_validation_invalid_difficulty(self):
        """Test scenario validation with invalid difficulty"""
        scenario = Scenario(
            id='test_001',
            category='networking',
            difficulty='super_hard',
            task='Test task',
            points=10,
            validation=ValidationRules(checks=[
                CommandCheck(command='echo test')
            ])
        )
        
        errors = scenario.validate_structure()
        assert len(errors) > 0
        assert any('difficulty' in e.lower() for e in errors)
    
    def test_scenario_validation_no_checks(self):
        """Test scenario validation with no validation checks"""
        scenario = Scenario(
            id='test_001',
            category='networking',
            difficulty='easy',
            task='Test task',
            points=10,
            validation=ValidationRules(checks=[])
        )
        
        errors = scenario.validate_structure()
        assert len(errors) > 0
        assert any('check' in e.lower() for e in errors)


class TestScenarioLoader:
    """Tests for scenario loader"""
    
    def test_loader_initialization(self):
        """Test scenario loader initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ScenarioLoader(tmpdir)
            assert loader.scenarios_path == tmpdir
    
    def test_load_single_scenario(self):
        """Test loading a single scenario from YAML"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test scenario file
            scenario_data = {
                'id': 'test_001',
                'category': 'networking',
                'difficulty': 'easy',
                'task': 'Test task',
                'points': 10,
                'validation': {
                    'checks': [
                        {
                            'type': 'command',
                            'command': 'echo test',
                            'expected_output': 'test'
                        }
                    ]
                }
            }
            
            # Create category directory
            cat_dir = os.path.join(tmpdir, 'networking', 'easy')
            os.makedirs(cat_dir)
            
            # Write scenario file
            scenario_file = os.path.join(cat_dir, 'test_001.yaml')
            with open(scenario_file, 'w') as f:
                yaml.dump(scenario_data, f)
            
            # Load scenarios
            loader = ScenarioLoader(tmpdir)
            scenarios = loader.load_all()
            
            assert 'networking' in scenarios
            assert len(scenarios['networking']) == 1
            assert scenarios['networking'][0].id == 'test_001'
    
    def test_load_multiple_scenarios(self):
        """Test loading multiple scenarios"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple scenario files
            for i in range(3):
                scenario_data = {
                    'id': f'test_{i:03d}',
                    'category': 'storage',
                    'difficulty': 'easy',
                    'task': f'Test task {i}',
                    'points': 10,
                    'validation': {
                        'checks': [
                            {
                                'type': 'command',
                                'command': 'echo test',
                                'expected_output': 'test'
                            }
                        ]
                    }
                }
                
                cat_dir = os.path.join(tmpdir, 'storage', 'easy')
                os.makedirs(cat_dir, exist_ok=True)
                
                scenario_file = os.path.join(cat_dir, f'test_{i:03d}.yaml')
                with open(scenario_file, 'w') as f:
                    yaml.dump(scenario_data, f)
            
            loader = ScenarioLoader(tmpdir)
            scenarios = loader.load_all()
            
            assert 'storage' in scenarios
            assert len(scenarios['storage']) == 3
    
    def test_get_scenario_by_category(self):
        """Test getting scenario filtered by category"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create scenarios in different categories
            for category in ['networking', 'storage']:
                scenario_data = {
                    'id': f'{category}_001',
                    'category': category,
                    'difficulty': 'easy',
                    'task': 'Test task',
                    'points': 10,
                    'validation': {
                        'checks': [
                            {
                                'type': 'command',
                                'command': 'echo test',
                                'expected_output': 'test'
                            }
                        ]
                    }
                }
                
                cat_dir = os.path.join(tmpdir, category, 'easy')
                os.makedirs(cat_dir, exist_ok=True)
                
                scenario_file = os.path.join(cat_dir, f'{category}_001.yaml')
                with open(scenario_file, 'w') as f:
                    yaml.dump(scenario_data, f)
            
            loader = ScenarioLoader(tmpdir)
            loader.load_all()
            
            # Get networking scenario
            scenario = loader.get_scenario(category='networking')
            assert scenario is not None
            assert scenario.category == 'networking'
    
    def test_get_scenario_by_difficulty(self):
        """Test getting scenario filtered by difficulty"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create scenarios with different difficulties
            for difficulty in ['easy', 'medium', 'hard']:
                scenario_data = {
                    'id': f'test_{difficulty}',
                    'category': 'networking',
                    'difficulty': difficulty,
                    'task': 'Test task',
                    'points': 10,
                    'validation': {
                        'checks': [
                            {
                                'type': 'command',
                                'command': 'echo test',
                                'expected_output': 'test'
                            }
                        ]
                    }
                }
                
                cat_dir = os.path.join(tmpdir, 'networking', difficulty)
                os.makedirs(cat_dir, exist_ok=True)
                
                scenario_file = os.path.join(cat_dir, f'test_{difficulty}.yaml')
                with open(scenario_file, 'w') as f:
                    yaml.dump(scenario_data, f)
            
            loader = ScenarioLoader(tmpdir)
            loader.load_all()
            
            # Get easy scenario
            scenario = loader.get_scenario(difficulty='easy')
            assert scenario is not None
            assert scenario.difficulty == 'easy'
    
    def test_get_scenario_by_id(self):
        """Test getting scenario by ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = {
                'id': 'unique_001',
                'category': 'networking',
                'difficulty': 'easy',
                'task': 'Test task',
                'points': 10,
                'validation': {
                    'checks': [
                        {
                            'type': 'command',
                            'command': 'echo test',
                            'expected_output': 'test'
                        }
                    ]
                }
            }
            
            cat_dir = os.path.join(tmpdir, 'networking', 'easy')
            os.makedirs(cat_dir)
            
            scenario_file = os.path.join(cat_dir, 'unique_001.yaml')
            with open(scenario_file, 'w') as f:
                yaml.dump(scenario_data, f)
            
            loader = ScenarioLoader(tmpdir)
            loader.load_all()
            
            scenario = loader.get_by_id('unique_001')
            assert scenario is not None
            assert scenario.id == 'unique_001'
    
    def test_invalid_yaml_handling(self):
        """Test handling of invalid YAML files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cat_dir = os.path.join(tmpdir, 'networking', 'easy')
            os.makedirs(cat_dir)
            
            # Write invalid YAML
            scenario_file = os.path.join(cat_dir, 'invalid.yaml')
            with open(scenario_file, 'w') as f:
                f.write("invalid: yaml: content: [unclosed")
            
            loader = ScenarioLoader(tmpdir)
            # Should not raise exception, just skip invalid file
            scenarios = loader.load_all()
            
            # Should have no scenarios loaded
            assert len(scenarios.get('networking', [])) == 0


class TestPropertyBasedScenarioLoader:
    """Property-based tests for scenario loader"""
    
    # Feature: lfcs-practice-environment, Property 1: Scenario loading completeness
    @given(scenario_dict=valid_scenario_dict_strategy())
    @settings(max_examples=100, deadline=None)
    def test_scenario_loading_completeness(self, scenario_dict):
        """
        Property: For any valid YAML scenario file in the scenarios directory,
        when the system starts, the Scenario Loader should successfully load and 
        parse that scenario without errors.
        
        Validates: Requirements 1.1, 1.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid scenario file
            cat_dir = os.path.join(tmpdir, scenario_dict['category'], 
                                  scenario_dict['difficulty'])
            os.makedirs(cat_dir, exist_ok=True)
            
            scenario_file = os.path.join(cat_dir, f"{scenario_dict['id']}.yaml")
            with open(scenario_file, 'w') as f:
                yaml.dump(scenario_dict, f)
            
            # Load scenarios
            loader = ScenarioLoader(tmpdir)
            scenarios = loader.load_all()
            
            # Verify the scenario was loaded
            assert scenario_dict['category'] in scenarios, \
                f"Category {scenario_dict['category']} should be loaded"
            
            category_scenarios = scenarios[scenario_dict['category']]
            assert len(category_scenarios) > 0, \
                "At least one scenario should be loaded in the category"
            
            # Find our specific scenario
            loaded_scenario = None
            for s in category_scenarios:
                if s.id == scenario_dict['id']:
                    loaded_scenario = s
                    break
            
            assert loaded_scenario is not None, \
                f"Scenario {scenario_dict['id']} should be loaded"
            
            # Verify all fields were loaded correctly
            assert loaded_scenario.id == scenario_dict['id'], \
                "Scenario ID should match"
            assert loaded_scenario.category == scenario_dict['category'], \
                "Category should match"
            assert loaded_scenario.difficulty == scenario_dict['difficulty'], \
                "Difficulty should match"
            assert loaded_scenario.task == scenario_dict['task'], \
                "Task description should match"
            assert loaded_scenario.points == scenario_dict['points'], \
                "Points should match"
            assert len(loaded_scenario.validation.checks) > 0, \
                "Validation checks should be loaded"
    
    # Feature: lfcs-practice-environment, Property 2: Category filtering correctness
    @given(
        scenarios_data=st.lists(
            valid_scenario_dict_strategy(),
            min_size=3,
            max_size=10
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_category_filtering_correctness(self, scenarios_data):
        """
        Property: For any category and difficulty combination, when a user requests 
        a scenario with those filters, all returned scenarios should match the 
        specified category and difficulty level.
        
        Validates: Requirements 1.2, 1.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Ensure we have unique IDs
            seen_ids = set()
            unique_scenarios = []
            for scenario_dict in scenarios_data:
                if scenario_dict['id'] not in seen_ids:
                    seen_ids.add(scenario_dict['id'])
                    unique_scenarios.append(scenario_dict)
            
            if len(unique_scenarios) == 0:
                return  # Skip if no unique scenarios
            
            # Create scenario files
            for scenario_dict in unique_scenarios:
                cat_dir = os.path.join(tmpdir, scenario_dict['category'], 
                                      scenario_dict['difficulty'])
                os.makedirs(cat_dir, exist_ok=True)
                
                scenario_file = os.path.join(cat_dir, f"{scenario_dict['id']}.yaml")
                with open(scenario_file, 'w') as f:
                    yaml.dump(scenario_dict, f)
            
            # Load scenarios
            loader = ScenarioLoader(tmpdir)
            loader.load_all()
            
            # Test filtering by category
            categories = set(s['category'] for s in unique_scenarios)
            for category in categories:
                # Get scenario by category
                scenario = loader.get_scenario(category=category)
                if scenario:
                    assert scenario.category == category, \
                        f"Scenario should be from category {category}, got {scenario.category}"
                
                # List scenarios by category
                category_list = loader.list_scenarios(category=category)
                for s in category_list:
                    assert s.category == category, \
                        f"All listed scenarios should be from category {category}"
            
            # Test filtering by difficulty
            difficulties = set(s['difficulty'] for s in unique_scenarios)
            for difficulty in difficulties:
                # Get scenario by difficulty
                scenario = loader.get_scenario(difficulty=difficulty)
                if scenario:
                    assert scenario.difficulty == difficulty, \
                        f"Scenario should have difficulty {difficulty}, got {scenario.difficulty}"
                
                # List scenarios by difficulty
                difficulty_list = loader.list_scenarios(difficulty=difficulty)
                for s in difficulty_list:
                    assert s.difficulty == difficulty, \
                        f"All listed scenarios should have difficulty {difficulty}"
            
            # Test filtering by both category and difficulty
            for category in categories:
                for difficulty in difficulties:
                    scenario = loader.get_scenario(category=category, difficulty=difficulty)
                    if scenario:
                        assert scenario.category == category, \
                            f"Scenario should be from category {category}"
                        assert scenario.difficulty == difficulty, \
                            f"Scenario should have difficulty {difficulty}"
    
    # Feature: lfcs-practice-environment, Property 10: YAML validation strictness
    @given(scenario_dict=valid_scenario_dict_strategy())
    @settings(max_examples=100, deadline=None)
    def test_yaml_validation_strictness(self, scenario_dict):
        """
        Property: For any YAML file with missing required fields or invalid structure,
        the Scenario Loader should reject it and report specific errors about what is 
        missing or invalid.
        
        Validates: Requirements 6.1, 6.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test 1: Valid scenario should load successfully
            cat_dir = os.path.join(tmpdir, scenario_dict['category'], 
                                  scenario_dict['difficulty'])
            os.makedirs(cat_dir, exist_ok=True)
            
            valid_file = os.path.join(cat_dir, 'valid.yaml')
            with open(valid_file, 'w') as f:
                yaml.dump(scenario_dict, f)
            
            loader = ScenarioLoader(tmpdir)
            scenarios = loader.load_all()
            
            assert scenario_dict['category'] in scenarios, \
                "Valid scenario should be loaded"
            assert len(scenarios[scenario_dict['category']]) > 0, \
                "Valid scenario should be in category list"
            
            # Test 2: Missing required field should be rejected
            invalid_dict = scenario_dict.copy()
            del invalid_dict['id']  # Remove required field
            
            tmpdir2 = tempfile.mkdtemp()
            try:
                cat_dir2 = os.path.join(tmpdir2, scenario_dict['category'], 
                                       scenario_dict['difficulty'])
                os.makedirs(cat_dir2, exist_ok=True)
                
                invalid_file = os.path.join(cat_dir2, 'invalid.yaml')
                with open(invalid_file, 'w') as f:
                    yaml.dump(invalid_dict, f)
                
                loader2 = ScenarioLoader(tmpdir2)
                scenarios2 = loader2.load_all()
                
                # Should not load invalid scenario
                assert len(scenarios2.get(scenario_dict['category'], [])) == 0, \
                    "Scenario with missing required field should be rejected"
            finally:
                import shutil
                shutil.rmtree(tmpdir2)
            
            # Test 3: Invalid category should be rejected
            invalid_dict2 = scenario_dict.copy()
            invalid_dict2['category'] = 'invalid_category'
            
            tmpdir3 = tempfile.mkdtemp()
            try:
                cat_dir3 = os.path.join(tmpdir3, 'invalid_category', 
                                       scenario_dict['difficulty'])
                os.makedirs(cat_dir3, exist_ok=True)
                
                invalid_file2 = os.path.join(cat_dir3, 'invalid2.yaml')
                with open(invalid_file2, 'w') as f:
                    yaml.dump(invalid_dict2, f)
                
                loader3 = ScenarioLoader(tmpdir3)
                scenarios3 = loader3.load_all()
                
                # Should not load scenario with invalid category
                assert len(scenarios3.get('invalid_category', [])) == 0, \
                    "Scenario with invalid category should be rejected"
            finally:
                import shutil
                shutil.rmtree(tmpdir3)
