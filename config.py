import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
TODOIST_TOKEN = os.environ["TODOIST_API_TOKEN"]

NOTION_TASKS_DB_ID = os.environ["NOTION_TASKS_DB_ID"]
NOTION_PROJECTS_DB_ID = os.environ["NOTION_PROJECTS_DB_ID"]
NOTION_VARIABLES_DB_ID = os.environ["NOTION_VARIABLES_DB_ID"]