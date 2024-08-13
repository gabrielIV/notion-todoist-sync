import logging
from datetime import datetime, timezone
from notion_handler import (update_notion_variable, create_notion_task,
                            update_notion_task, create_notion_project, update_notion_project, notion, get_notion_priority,
                            get_notion_project_by_todoist_id, get_notion_task_by_todoist_id, get_notion_project_by_id, get_notion_task_by_id
                            )
from todoist_handler import TodoistSync
from config import NOTION_TASKS_DB_ID
import json

logger = logging.getLogger(__name__)


def sync_notion_to_todoist(notion_tasks, notion_projects, todoist_api):
    """Syncs changes from Notion to Todoist."""

    projects_index = {}
    tasks_index = {}

    for project in notion_projects:
        if not project["todoist_id"]:
            project["todoist_id"] = todoist_api.add_project(project["name"],notion_id=project["notion_id"])
        else:
            todoist_project = todoist_api.get_project(project["todoist_id"])
            if not project["name"]:
                project["name"]="Unassigned"
            print(json.dumps(todoist_project, indent=2))
            print(json.dumps(project, indent=2))
            if project["name"] != todoist_project["name"]:
                todoist_api.update_project(
                    project["todoist_id"], name=project["name"])
        projects_index[project["notion_id"]] = project["todoist_id"]

    for task in notion_tasks:

        print(json.dumps(task, indent=2))
        # Ensure todoist_project_id is defined, using the index first
        if not task["todoist_project_id"]:
            task["todoist_project_id"] = projects_index.get(task["project_id"])
            if not task["todoist_project_id"]:
                task["todoist_project_id"] = get_notion_project_by_id(task["project_id"])[
                    "todoist_id"]
                projects_index[task["project_id"]] = task["todoist_project_id"]

        # Ensure todoist_parent_id is defined, using the index first
        if task["parent_id"] and not task["todoist_parent_id"]:
            task["todoist_parent_id"] = tasks_index.get(task["parent_id"])
            if not task["todoist_parent_id"]:
                task["todoist_parent_id"] = get_notion_task_by_id(task["parent_id"])[
                    "todoist_id"]
                tasks_index[task["parent_id"]] = task["todoist_parent_id"]

        if not task["todoist_id"]:
            # Create a new task in Todoist and set TodoistID
            task["todoist_id"] = todoist_api.add_task(
                content=task["title"],
                project_id=task["todoist_project_id"],
                due={"string": task["due_date"]} if task["due_date"] else None,
                priority=task["priority"],
                parent_id=task["todoist_parent_id"],
                notion_id=task["notion_id"]
            )
        else:
            # Check for changes before updating
            todoist_task = todoist_api.get_task(task["todoist_id"])
            if not todoist_task:
                logger.warning(
                    f"Task {task['title']} not found in Todoist. Skipping update.")
                continue
            
            if (task["title"] != todoist_task["content"] or
                task["due_date"] != todoist_task["due"]["date"] if todoist_task.get("due") else None or
                task["priority"] != todoist_task["priority"] or
                    task["todoist_parent_id"] != todoist_task.get("parent_id")):

                # Update the task in Todoist
                todoist_api.update_task(
                    task["todoist_id"],
                    content=task["title"],
                    due={"string": task["due_date"]
                         } if task["due_date"] else None,
                    priority=task["priority"],
                    parent_id=task["todoist_parent_id"]
                )

        tasks_index[task["notion_id"]] = task["todoist_id"]

    final_sync_results=todoist_api.sync()
    json.dump(final_sync_results, open("data/todoist_sync_result.json", "w"))


def sync_todoist_to_notion(todoist_state):
    """Syncs changes from Todoist to Notion."""

    for project in todoist_state["projects"]:
        notion_project = get_notion_project_by_todoist_id(project["id"])
        if not notion_project:
            # Create a new project in Notion and set TodoistID
            new_project_id = create_notion_project(project)
            # update_notion_project(
            #     new_project_id,  # Update the newly created project
            #     {"TodoistID": {"rich_text": [
            #         {"text": {"content": project["id"]}}]}}
            # )
        else:
            # Check for changes before updating
            if project["name"] != notion_project["name"]:
                update_notion_project(
                    page_id=notion_project["notion_id"],
                    properties={"Project name": {
                        "title": [{"text": {"content": project["name"]}}]}}
                )

    for task in todoist_state["items"]:
        notion_task = get_notion_task_by_todoist_id(task["id"])

        project_id = None
        if task["project_id"]:
            notion_project = get_notion_project_by_todoist_id(
                task["project_id"])
            if notion_project:
                project_id = notion_project["notion_id"]

        parent_id = None
        if task.get("parent_id"):
            notion_parent_task = get_notion_task_by_todoist_id(
                task["parent_id"])
            if notion_parent_task:
                notion_parent_task = notion_parent_task["notion_id"]
                

        task_status = get_todoist_task_status(task)

        if not notion_task:
            # Create a new task in Notion
            create_notion_task(
                task, project_id, parent_id, task["project_id"])

        else:
            # Check for changes before updating
            if (task["content"] != notion_task["title"] or
                (task.get("due") and task["due"]["date"] != notion_task["due_date"]) or
                    task_status != notion_task["status"]):
                update_notion_task(
                    page_id = notion_task["notion_id"],
                    properties={
                        "Task name": {"title": [{"text": {"content": task["content"]}}]},
                        "Due": {"date": {"start": task["due"]["date"]}} if task.get("due") else None,
                        "Status": {"select": {"name": task_status}},
                        "Project": {"relation": [{"id": project_id}]} if project_id else None,
                        "Parent-task": {"relation": [{"id": parent_id}]} if parent_id else None
                    }
                )


def get_todoist_task_status(task):
    return "Done" if task["checked"] else "Not Started"
