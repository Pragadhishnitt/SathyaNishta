import logging
import os

def setup_logger(name):
    # Retrieve log level from environment variable, default to DEBUG
    log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Create console handler and set level
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add formatter to ch
    ch.setFormatter(formatter)
    
    # Add ch to logger
    if not logger.handlers:
        logger.addHandler(ch)
        
    return logger
