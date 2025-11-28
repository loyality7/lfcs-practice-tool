"""Module loader for learning content"""

import yaml
import logging
from pathlib import Path
from typing import List, Dict, Optional

from .models import LearningModule, DifficultyLevel

logger = logging.getLogger(__name__)

class ModuleLoader:
    """Loads learning modules from YAML files"""
    
    def __init__(self, modules_path: str = "learn_modules"):
        self.modules_path = Path(modules_path)
        self._modules: Dict[str, LearningModule] = {}
        self._modules_by_level: Dict[DifficultyLevel, List[LearningModule]] = {}
        self._loaded = False
        
    def load_all(self) -> Dict[str, LearningModule]:
        """Load all learning modules"""
        if self._loaded:
            return self._modules
            
        self._modules = {}
        self._modules_by_level = {level: [] for level in DifficultyLevel}
        
        if not self.modules_path.exists():
            logger.warning(f"Modules directory not found: {self.modules_path}")
            return self._modules
            
        # Walk through modules directory
        # Sort files to ensure modules are loaded in order (01_..., 02_...)
        for yaml_file in sorted(self.modules_path.rglob("*.yaml")):
            try:
                module = self._load_file(yaml_file)
                if module:
                    self._modules[module.id] = module
                    self._modules_by_level[module.level].append(module)
                    logger.info(f"Loaded module: {module.id}")
            except Exception as e:
                logger.error(f"Error loading {yaml_file}: {e}")
                
        self._loaded = True
        return self._modules
    
    def _load_file(self, file_path: Path) -> Optional[LearningModule]:
        """Load a single module file"""
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            
        if not data:
            return None
            
        return LearningModule.from_dict(data)
    
    def get_module(self, module_id: str) -> Optional[LearningModule]:
        """Get a specific module by ID"""
        if not self._loaded:
            self.load_all()
        return self._modules.get(module_id)
    
    def get_modules_by_level(self, level: DifficultyLevel) -> List[LearningModule]:
        """Get all modules for a specific level"""
        if not self._loaded:
            self.load_all()
        return self._modules_by_level.get(level, [])
    
    def get_all_levels(self) -> List[DifficultyLevel]:
        """Get all available difficulty levels"""
        return list(DifficultyLevel)
