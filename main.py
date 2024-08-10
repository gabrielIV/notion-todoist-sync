import logging
from datetime import datetime
from notion_handler import get_notion_variable, get_notion_tasks, get_notion_projects, update_notion_variable
from todoist_handler import sync_todoist
from sync_logic import sync_notion_to_todoist, sync_todoist_to_notion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Notion-Todoist synchronization")
    
    try:
        logger.info("Fetching Notion variables")
        notion_task_last_updated = get_notion_variable("notion_task_last_updated") or datetime.min.isoformat()
        notion_project_last_updated = get_notion_variable("notion_project_last_updated") or datetime.min.isoformat()
        todoist_sync_token = get_notion_variable("todoist_sync_token") or "*"
        logger.info(f"Last task sync: {notion_task_last_updated}")
        logger.info(f"Last project sync: {notion_project_last_updated}")

        logger.info("Fetching Notion tasks")
        notion_tasks = get_notion_tasks(notion_task_last_updated)
        logger.info(f"Retrieved {len(notion_tasks)} Notion tasks")

        logger.info("Fetching Notion projects")
        notion_projects = get_notion_projects(notion_project_last_updated)
        logger.info(f"Retrieved {len(notion_projects)} Notion projects")

        logger.info("Syncing Todoist state")
        todoist_state, new_sync_token = sync_todoist(todoist_sync_token)
        logger.info(f"Retrieved Todoist state with {len(todoist_state['items'])} tasks and {len(todoist_state['projects'])} projects")

        logger.info("Syncing Notion to Todoist")
        sync_notion_to_todoist(notion_tasks, notion_projects, todoist_state)
        logger.info("Notion to Todoist sync completed")

        logger.info("Syncing Todoist to Notion")
        sync_todoist_to_notion(todoist_state, notion_projects)
        logger.info("Todoist to Notion sync completed")

        logger.info("Updating Todoist sync token")
        update_notion_variable("todoist_sync_token", new_sync_token)
        logger.info("Todoist sync token updated successfully")

        logger.info("Synchronization completed successfully")
    except Exception as e:
        logger.error(f"An error occurred during synchronization: {str(e)}", exc_info=True)
    finally:
        logger.info("Synchronization process ended")

if __name__ == "__main__":
    main()