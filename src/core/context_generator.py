import random
import string
import uuid
from typing import Dict, Any

class ContextGenerator:
    """Generates random context variables for scenarios"""
    
    def generate(self) -> Dict[str, Any]:
        """Generate a dictionary of random values"""
        return {
            "random_file": self._random_filename(),
            "random_dir": self._random_dirname(),
            "random_user": self._random_username(),
            "random_group": self._random_groupname(),
            "random_ip": self._random_ip(),
            "random_port": self._random_port(),
            "random_text": self._random_text(),
            "uuid": str(uuid.uuid4())
        }
    
    def _random_filename(self) -> str:
        exts = ['txt', 'conf', 'log', 'sh', 'py']
        name = ''.join(random.choices(string.ascii_lowercase, k=8))
        ext = random.choice(exts)
        return f"{name}.{ext}"
        
    def _random_dirname(self) -> str:
        return ''.join(random.choices(string.ascii_lowercase, k=6))
        
    def _random_username(self) -> str:
        return 'user_' + ''.join(random.choices(string.ascii_lowercase, k=4))
        
    def _random_groupname(self) -> str:
        return 'group_' + ''.join(random.choices(string.ascii_lowercase, k=4))
        
    def _random_ip(self) -> str:
        return f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
        
    def _random_port(self) -> int:
        return random.randint(1024, 65535)
        
    def _random_text(self) -> str:
        words = ["linux", "system", "kernel", "bash", "shell", "terminal", "process", "daemon"]
        return ' '.join(random.choices(words, k=5))
