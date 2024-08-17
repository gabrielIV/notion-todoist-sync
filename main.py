from datetime import datetime, timezone
from notion_handler import get_notion_variable, get_notion_tasks, get_notion_projects, update_notion_variable
from todoist_handler import TodoistSync
from sync_logic import sync_notion_to_todoist, sync_todoist_to_notion
from config import TODOIST_TOKEN, logger
import json


def main():
    logger.info("Starting Notion-Todoist synchronization")

    try:
        # Initialize TodoistSync object
        todoist_api = TodoistSync(TODOIST_TOKEN)

        # get the sync token from Notion variables
        todoist_api.sync_token = get_notion_variable(
            "todoist_sync_token") or "*"  # "*" means full sync

        # Initial sync to get projects and items
        initial_sync_result = todoist_api.sync()

        json.dump(initial_sync_result, open(
            "data/todoist_sync_result.json", "w"))

        logger.info("Fetching Notion variables")
        notion_task_last_updated = get_notion_variable(
            "notion_task_last_updated") or datetime.min.isoformat()
        notion_project_last_updated = get_notion_variable(
            "notion_project_last_updated") or datetime.min.isoformat()

        logger.info("Fetching Notion tasks")
        notion_tasks = get_notion_tasks(notion_task_last_updated)
        logger.info(f"Retrieved {len(notion_tasks)} Notion tasks")

        logger.info("Fetching Notion projects")
        notion_projects = get_notion_projects(notion_project_last_updated)
        logger.info(f"Retrieved {len(notion_projects)} Notion projects")

        logger.info("Syncing Notion to Todoist")
        sync_notion_to_todoist(notion_tasks, notion_projects, todoist_api)
        logger.info("Notion to Todoist sync completed")

        logger.info("Syncing Todoist to Notion")
        sync_todoist_to_notion(initial_sync_result)
        logger.info("Todoist to Notion sync completed")

        # Update Notion variables with new timestamps and sync_token
        update_notion_variable("notion_task_last_updated",
                               datetime.now(timezone.utc).isoformat())
        update_notion_variable("notion_project_last_updated",
                               datetime.now(timezone.utc).isoformat())
        update_notion_variable("todoist_sync_token", todoist_api.sync_token)

        logger.info("Synchronization completed successfully")
    except Exception as e:
        logger.error(
            f"An error occurred during synchronization: {str(e)}", exc_info=True)
    finally:
        logger.info("Synchronization process ended")


if __name__ == "__main__":
    main()
