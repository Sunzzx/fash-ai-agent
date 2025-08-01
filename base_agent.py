"""
Base agent class for all agents in the system
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path

from settings import Settings


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the base agent"""
        self.settings = Settings(config_path=config_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Set up logging for the agent"""
        log_level = getattr(logging, self.settings.log_level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Create logs directory if it doesn't exist
        log_file = Path(self.settings.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file handler if not already exists
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """Process method that must be implemented by subclasses"""
        pass
    
    def log_info(self, message: str) -> None:
        """Log an info message"""
        self.logger.info(message)
    
    def log_warning(self, message: str) -> None:
        """Log a warning message"""
        self.logger.warning(message)
    
    def log_error(self, message: str, exception: Optional[Exception] = None) -> None:
        """Log an error message"""
        if exception:
            self.logger.error(f"{message}: {exception}", exc_info=True)
        else:
            self.logger.error(message)
    
    def log_debug(self, message: str) -> None:
        """Log a debug message"""
        self.logger.debug(message)
    
    def validate_required_settings(self, required_keys: List[str]) -> None:
        """Validate that required settings are present"""
        missing_keys = []
        
        for key in required_keys:
            if hasattr(self.settings, key):
                value = getattr(self.settings, key)
                if not value or (isinstance(value, str) and value.strip() == ""):
                    missing_keys.append(key)
            else:
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(
                f"Missing required configuration keys: {', '.join(missing_keys)}"
            )
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value with optional default"""
        return getattr(self.settings, key, default)
    
    async def cleanup(self) -> None:
        """Cleanup method called when agent is shutting down"""
        self.log_info(f"{self.__class__.__name__} cleanup completed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        import asyncio
        if asyncio.iscoroutinefunction(self.cleanup):
            # If we're in an async context, this should be handled differently
            # For now, we'll just log that cleanup is needed
            self.log_info("Cleanup needed - call cleanup() method explicitly in async context")
        else:
            asyncio.run(self.cleanup())
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
