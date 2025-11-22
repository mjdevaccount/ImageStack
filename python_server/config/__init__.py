# python_server/config/__init__.py

"""Configuration modules for PhotoBrain / ImageStack"""

# Import settings from the parent config.py file
import sys
from pathlib import Path

# Add parent directory to path to import config.py
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Now we can import from the config.py file at python_server/config.py
# But to avoid circular imports, we'll do this differently
# We need to import the actual config module

# The real solution: directly load settings from ../config.py
import importlib.util
spec = importlib.util.spec_from_file_location("_config", Path(__file__).parent.parent / "config.py")
_config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_config_module)
settings = _config_module.settings
Settings = _config_module.Settings

__all__ = ['settings', 'Settings']
