from notion_handler import (create_notion_task,
                            update_notion_task, create_notion_project, update_notion_project,
                            get_notion_project_by_todoist_id, get_notion_task_by_todoist_id, get_notion_project_by_id, get_notion_task_by_id
                            )
from config import logger
import json
import copy


def sync_notion_to_todoist(notion_tasks, notion_projects, todoist_api):
    """Syncs changes from Notion to Todoist."""

    projects_index = {}  # Index to store Notion project ID and corresponding Todoist project ID
    tasks_index = {}  # Index to store Notion task ID and corresponding Todoist task ID

    for project in notion_projects:
        if not project["todoist_id"]:
            # Create a new project in Todoist if it doesn't exist
            project["todoist_id"] = todoist_api.add_project(
                project["name"], notion_id=project["notion_id"])
        else:
            # Get the project from Todoist
            todoist_project = todoist_api.get_project(project["todoist_id"])

            # if project not found in Todoist, skip update
            if not todoist_project:
                logger.warning(
                    f"Project {project['name']} not found in Todoist. Skipping update.")
                continue

            # Update the project name in Todoist if it has changed
            if project["name"] != todoist_project["name"]:
                todoist_api.update_project(
                    project["todoist_id"], name=project["name"])

        # Update the projects index
        projects_index[project["notion_id"]] = project["todoist_id"]

    for task in notion_tasks:

        # deep copy the task object
        _task = copy.deepcopy(task)

        # skip if project_id is not defined
        if not task["project_id"]:
            logger.warning(
                f"Project not found for task {task['title']}. Skipping update. Please move the task to a project.")
            continue

        # Ensure todoist_project_id is defined, get it if not
        if not task["todoist_project_id"]:
            # Get the Todoist project ID from the Notion project ID
            task["todoist_project_id"] = get_notion_project_by_id(task["project_id"])[
                "todoist_id"]
            # Update the projects index
            projects_index[task["project_id"]] = task["todoist_project_id"]

        # check if project_id is not found in projects_index and get the project_id
        if not projects_index.get(task["project_id"]):
            projects_index[task["project_id"]] = get_notion_project_by_id(task["project_id"])[
                "todoist_id"]

        # Ensure todoist_parent_id is defined, fetch it if not
        if task["parent_id"] and not task["todoist_parent_id"]:
            # check if parent_id is not found in tasks_index and get the parent_id
            task["todoist_parent_id"] = tasks_index.get(task["parent_id"])

            if not task["todoist_parent_id"]:
                # Get the Todoist parent task ID from the Notion parent task ID
                task["todoist_parent_id"] = get_notion_task_by_id(task["parent_id"])[
                    "todoist_id"]
                # Update the tasks index
                tasks_index[task["parent_id"]] = task["todoist_parent_id"]

        # check if parent_id is not found in tasks_index and get the parent_id
        if task["parent_id"] and not tasks_index.get(task["parent_id"]):
            tasks_index[task["parent_id"]] = get_notion_task_by_id(task["parent_id"])[
                "todoist_id"]

        if not task["todoist_id"]:
            # Create a new task in Todoist if it doesn't exist
            task["todoist_id"] = todoist_api.add_task(
                content=task["title"],
                project_id=task["todoist_project_id"],
                due={"string": task["due_date"]} if task["due_date"] else None,
                priority=task["priority"],
                parent_id=task["todoist_parent_id"],
                notion_id=task["notion_id"]
            )
        else:
            # Get the task from Todoist
            todoist_task = todoist_api.get_task(task["todoist_id"])

            # Handle cases where the task is not found in Todoist
            if not todoist_task:
                logger.warning(
                    f"Task {task['title']} not found in Todoist. Skipping update.")
                continue

            # Separate status check
            if task["status"] != get_todoist_task_status(todoist_task):
                if task["status"] == "Done":
                    todoist_api.complete_task(task["todoist_id"])
                # Only uncomplete if the task was previously completed in Todoist
                elif get_todoist_task_status(todoist_task) == "Done":
                    todoist_api.uncomplete_task(task["todoist_id"])

            print("")
            print("projects", _task["todoist_id"], _task["todoist_parent_id"],
                  projects_index.get(_task["project_id"]))
            print("parents", _task["todoist_id"], _task["todoist_parent_id"],
                  tasks_index.get(_task["parent_id"]))

            # Move an item if the project or parent has changed
            if _task["todoist_project_id"] != projects_index.get(_task["project_id"]) or _task["todoist_parent_id"] != tasks_index.get(_task["parent_id"]):
                new_project_id = None
                new_parent_id = None

                if _task["todoist_project_id"] != projects_index.get(_task["project_id"]):
                    new_project_id = projects_index.get(task["project_id"])

                if _task["todoist_parent_id"] != tasks_index.get(_task["parent_id"]):
                    new_parent_id = tasks_index.get(task["parent_id"])

                todoist_api.move_task(
                    task["todoist_id"],
                    project_id=new_project_id,
                    parent_id=new_parent_id,
                    notion_id=task["notion_id"]
                )

            # Update properties if they have changed
            if (task["title"] != todoist_task["content"] or
                task["due_date"] != (todoist_task["due"]["date"] if todoist_task.get("due") else None) or
                    task["priority"] != todoist_task["priority"]):

                # Update the task in Todoist
                todoist_api.update_task(
                    task["todoist_id"],
                    content=task["title"],
                    due={"date": task["due_date"]
                         } if task["due_date"] else None,
                    priority=task["priority"],
                )

        # Update the tasks index
        tasks_index[task["notion_id"]] = task["todoist_id"]

    # Final sync to execute commands and get updated data
    final_sync_results = todoist_api.sync()
    # Save the sync results to a JSON file for debugging
    json.dump(final_sync_results, open("data/todoist_sync_result.json", "w"))


def sync_todoist_to_notion(todoist_state):
    """Syncs changes from Todoist to Notion."""

    for project in todoist_state["projects"]:
        try:
            notion_project = get_notion_project_by_todoist_id(project["id"])
            if not notion_project:
                # Create a new project in Notion and set TodoistID
                create_notion_project(project)

            else:
                # Check for changes before updating
                if project["name"] != notion_project["name"]:
                    update_notion_project(
                        page_id=notion_project["notion_id"],
                        properties={"Project name": {
                            "title": [{"text": {"content": project["name"]}}]}}
                    )
        except Exception as e:
            logger.error(f"Error syncing project {project['name']}: {e}")

    for task in todoist_state["items"]:
        try:
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
                    parent_id = notion_parent_task["notion_id"]

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
                    properties = {
                        "Task name": {"title": [{"text": {"content": task["content"]}}]},
                    }
                    if task.get("due"):
                        properties["Due"] = {
                            "date": {"start": task["due"]["date"]}}
                    if project_id:
                        properties["Project"] = {
                            "relation": [{"id": project_id}]}
                    if parent_id:
                        properties["Parent-task"] = {
                            "relation": [{"id": parent_id}]}

                    if task_status == "Done":
                        properties["Status"] = {
                            "status": {"name": task_status}
                        }

                    update_notion_task(
                        page_id=notion_task["notion_id"],
                        properties=properties
                    )
        except Exception as e:
            logger.error(f"Error syncing task {task['content']}: {e}")


def get_todoist_task_status(task):
    return "Done" if task["checked"] else "Not Started"
