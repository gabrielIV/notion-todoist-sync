import os
from dotenv import load_dotenv
import logging
import colorlog

# Load environment variables from .env file if it exists
load_dotenv()

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
TODOIST_TOKEN = os.environ["TODOIST_API_TOKEN"]

NOTION_TASKS_DB_ID = os.environ["NOTION_TASKS_DB_ID"]
NOTION_PROJECTS_DB_ID = os.environ["NOTION_PROJECTS_DB_ID"]
NOTION_VARIABLES_DB_ID = os.environ["NOTION_VARIABLES_DB_ID"]

# Set up logging
# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler
file_handler = logging.FileHandler(
    "logs/sync_log.txt")  # Specify the filename here
file_handler.setLevel(logging.DEBUG)  # Set the desired logging level

# Create a formatter for the file handler
file_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
file_handler.setFormatter(file_formatter)

# Create a console handler (optional, for colored output in the console)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create a formatter with colors for the console handler
console_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)s:%(name)s:%(message)s",
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)
console_handler.setFormatter(console_formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)  # Optional, for colored console output
