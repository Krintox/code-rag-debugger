import logging
import sys
from typing import Optional
from pathlib import Path
import json
from datetime import datetime

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> None:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        console_output: Whether to output logs to console
    """
    # Convert string level to logging level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Clear any existing handlers
    logging.getLogger().handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logging.getLogger().addHandler(console_handler)
    
    # Create file handler if log file is specified
    if log_file:
        # Create directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logging.getLogger().addHandler(file_handler)
    
    # Set the root logger level
    logging.getLogger().setLevel(level)
    
    # Set levels for specific noisy loggers
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("git").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logging.info(f"Logging setup complete. Level: {log_level}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def setup_json_logging(
    log_file: str,
    log_level: str = "INFO"
) -> None:
    """
    Set up JSON logging to a file.
    
    Args:
        log_file: Path to JSON log file
        log_level: Logging level
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create JSON file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(JsonFormatter())
    file_handler.setLevel(level)
    
    # Add to root logger
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().setLevel(level)