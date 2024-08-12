## notion_handler.py

```python
from notion_client import Client as NotionClient
from datetime import datetime, timezone
from config import NOTION_TOKEN, NOTION_TASKS_DB_ID, NOTION_PROJECTS_DB_ID, NOTION_VARIABLES_DB_ID

notion = NotionClient(auth=NOTION_TOKEN)


def get_notion_variable(variable_name):
    """Retrieves a variable from the Notion variables database."""
    response = notion.databases.query(
        database_id=NOTION_VARIABLES_DB_ID,
        filter={"property": "Name", "title": {"equals": variable_name}}
    )

    if response["results"]:
        return response["results"][0]["properties"]["Value"]["rich_text"][0]["plain_text"]
    return None


def update_notion_variable(variable_name, value):
    """Updates or creates a variable in the Notion variables database."""
    response = notion.databases.query(
        database_id=NOTION_VARIABLES_DB_ID,
        filter={"property": "Name", "title": {"equals": variable_name}}
    )
    if response["results"]:
        page_id = response["results"][0]["id"]
        notion.pages.update(
            page_id=page_id,
            properties={"Value": {"rich_text": [{"text": {"content": value}}]}}
        )
    else:
        notion.pages.create(
            parent={"database_id": NOTION_VARIABLES_DB_ID},
            properties={
                "Name": {"title": [{"text": {"content": variable_name}}]},
                "Value": {"rich_text": [{"text": {"content": value}}]}
            }
        )


def create_notion_task(todoist_task, project_id=None, parent_id=None, todoist_project_id=None):
    """Creates a new task in the Notion tasks database."""
    new_page = notion.pages.create(
        parent={"database_id": NOTION_TASKS_DB_ID},
        properties={
            "Task name": {"title": [{"text": {"content": todoist_task["content"]}}]},
            "Status": {"status": {"name": "Done" if todoist_task["checked"] else "Not Started"}},
            "TodoistID": {"rich_text": [{"text": {"content": todoist_task["id"]}}]},
            "TodoistProjectID": {"rich_text": [{"text": {"content": str(todoist_project_id)}}]} if todoist_project_id else None,
            "Due": {"date": {"start": todoist_task["due"]["date"]}} if todoist_task.get("due") else None,
            "Project": {"relation": [{"id": project_id}]} if project_id else None,
            "Parent-task": {"relation": [{"id": parent_id}]} if parent_id else None
        }
    )
    return new_page["id"]


def update_notion_task(page_id, properties):
    """Updates an existing task in the Notion tasks database."""
    notion.pages.update(page_id=page_id, properties=properties)


def get_notion_tasks(last_updated_date):
    """Retrieves tasks from the Notion tasks database that have been modified since the given date."""
    results = notion.databases.query(
        database_id=NOTION_TASKS_DB_ID,
        filter={
            "property": "Last edited time",
            "last_edited_time": {"on_or_after": last_updated_date}
        }
    )
    tasks = []
    for page in results["results"]:
        task = {
            "notion_id": page["id"],
            "title": page["properties"]["Task name"]["title"][0]["plain_text"] if page["properties"]["Task name"]["title"] else "",
            "status": page["properties"]["Status"]["status"]["name"] if page["properties"]["Status"]["status"] else "Not Started",
            "todoist_id": page["properties"]["TodoistID"]["rich_text"][0]["plain_text"] if page["properties"]["TodoistID"]["rich_text"] else None,
            "due_date": page["properties"]["Due"]["date"]["start"] if page["properties"]["Due"]["date"] else None,
            "project_id": page["properties"]["Project"]["relation"][0]["id"] if page["properties"]["Project"]["relation"] else None,
            "todoist_project_id": page["properties"]["TodoistProjectID"]["rich_text"][0]["plain_text"] if page["properties"]["TodoistProjectID"]["rich_text"] else None,
            "todoist_parent_id": page["properties"]["TodoistParentID"]["rich_text"][0]["plain_text"] if page["properties"]["TodoistParentID"]["rich_text"] else None,
            "parent_id": page["properties"]["Parent-task"]["relation"][0]["id"] if page["properties"]["Parent-task"]["relation"] else None,
            "priority": get_notion_priority(page["properties"]["Priority"]["select"]["name"] if page["properties"]["Priority"]["select"] else None),
            "last_edited_time": page["last_edited_time"],
        }
        tasks.append(task)
    return tasks


def create_notion_project(todoist_project):
    """Creates a new project in the Notion projects database."""
    new_page = notion.pages.create(
        parent={"database_id": NOTION_PROJECTS_DB_ID},
        properties={
            "Name": {"title": [{"text": {"content": todoist_project["name"]}}]},
            "TodoistID": {"rich_text": [{"text": {"content": todoist_project["id"]}}]}
        }
    )
    return new_page["id"]


def update_notion_project(todoist_project_id, properties):
    """Updates an existing project in the Notion projects database."""
    page_id = get_notion_project_by_todoist_id(todoist_project_id)["notion_id"]
    notion.pages.update(page_id=page_id, properties=properties)


def get_notion_projects(last_updated_date):
    """Retrieves projects from the Notion projects database that have been modified since the given date."""
    results = notion.databases.query(
        database_id=NOTION_PROJECTS_DB_ID,
        filter={
            "property": "Last edited time",
            "date": {"on_or_after": last_updated_date}
        }
    )
    projects = []
    for page in results["results"]:
        todoist_id = None
        todoist_id_property = page["properties"].get(
            "TodoistID", {}).get("rich_text", [])
        if todoist_id_property and todoist_id_property[0].get("plain_text"):
            todoist_id = todoist_id_property[0]["plain_text"]

        project = {
            "notion_id": page["id"],
            "name": page["properties"]["Project name"]["title"][0]["text"]["content"],
            "todoist_id": todoist_id
        }
        projects.append(project)
    return projects


def get_notion_project_by_id(id):
    """Retrieves a project from the Notion projects database by its ID."""
    project = notion.pages.retrieve(page_id=id)
    return {
        "notion_id": project["id"],
        "name": project["properties"]["Project name"]["title"][0]["text"]["content"],
        "todoist_id": project["properties"]["TodoistID"]["rich_text"][0]["plain_text"] if project["properties"]["TodoistID"]["rich_text"] else None
    }


def get_notion_task_by_id(id):
    """Retrieves a task from the Notion tasks database by its ID."""
    task = notion.pages.retrieve(page_id=id)
    return {
        "notion_id": task["id"],
        "title": task["properties"]["Task name"]["title"][0]["plain_text"] if task["properties"]["Task name"]["title"] else "",
        "status": task["properties"]["Status"]["status"]["name"] if task["properties"]["Status"]["status"] else "Not Started",
        "todoist_id": task["properties"]["TodoistID"]["rich_text"][0]["plain_text"] if task["properties"]["TodoistID"]["rich_text"] else None,
        "due_date": task["properties"]["Due"]["date"]["start"] if task["properties"]["Due"]["date"] else None,
        "project_id": task["properties"]["Project"]["relation"][0]["id"] if task["properties"]["Project"]["relation"] else None,
        "todoist_project_id": task["properties"]["TodoistProjectID"]["rich_text"][0]["plain_text"] if task["properties"]["TodoistProjectID"]["rich_text"] else None,
        "todoist_parent_id": task["properties"]["TodoistParentID"]["rich_text"][0]["plain_text"] if task["properties"]["TodoistParentID"]["rich_text"] else None,
        "parent_id": task["properties"]["Parent-task"]["relation"][0]["id"] if task["properties"]["Parent-task"]["relation"] else None,
        "priority": get_notion_priority(task["properties"]["Priority"]["select"]["name"] if task["properties"]["Priority"]["select"] else None),
        "last_edited_time": task["last_edited_time"],
    }


def get_notion_priority(priority):
    """Converts a Todoist priority to a Notion priority."""
    if priority:
        if priority == "High":
            return 4
        elif priority == "Medium":
            return 3
        elif priority == "Low":
            return 2
    return 1

# Helper function to get project using todoist project id


def get_notion_project_by_todoist_id(todoist_id):
    """Retrieves a project from the Notion projects database by its Todoist ID."""
    results = notion.databases.query(
        database_id=NOTION_PROJECTS_DB_ID,
        filter={
            "property": "TodoistID",
            "rich_text": {"equals": todoist_id}
        }
    )
    if results["results"]:
        return {
            "notion_id": results["results"][0]["id"],
            "name": results["results"][0]["properties"]["Project name"]["title"][0]["text"]["content"],
            "todoist_id": results["results"][0]["properties"]["TodoistID"]["rich_text"][0]["plain_text"]
        }
    return None

```

## config.py

```python
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
TODOIST_TOKEN = os.environ["TODOIST_API_TOKEN"]

NOTION_TASKS_DB_ID = os.environ["NOTION_TASKS_DB_ID"]
NOTION_PROJECTS_DB_ID = os.environ["NOTION_PROJECTS_DB_ID"]
NOTION_VARIABLES_DB_ID = os.environ["NOTION_VARIABLES_DB_ID"]
```

## sync_logic.py

```python
import logging
from datetime import datetime, timezone
from notion_handler import (update_notion_variable, create_notion_task,
                            update_notion_task, create_notion_project, update_notion_project, notion, get_notion_priority,
                            get_notion_project_by_todoist_id, get_notion_task_by_todoist_id)
from todoist_handler import TodoistSync
from config import NOTION_TASKS_DB_ID

logger = logging.getLogger(__name__)


def sync_notion_to_todoist(notion_tasks, notion_projects, todoist_api):
    """Syncs changes from Notion to Todoist."""

    projects_index = {}
    tasks_index = {}

    for project in notion_projects:
        if not project["todoist_id"]:
            project["todoist_id"] = todoist_api.add_project(project["name"])
        else:
            todoist_project = todoist_api.get_project(project["todoist_id"])
            if project["name"] != todoist_project["name"]:
                todoist_api.update_project(
                    project["todoist_id"], name=project["name"])
        projects_index[project["notion_id"]] = project["todoist_id"]

    for task in notion_tasks:
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
            task["todoist_id"] = todoist_api.add_task(
                content=task["title"],
                project_id=task["todoist_project_id"],
                due={"string": task["due_date"]} if task["due_date"] else None,
                priority=task["priority"],
                parent_id=task["todoist_parent_id"]
            )
        else:
            todoist_task = todoist_api.get_task(task["todoist_id"])
            if (task["title"] != todoist_task["content"] or
                task["due_date"] != todoist_task["due"].get("date") or
                task["priority"] != todoist_task["priority"] or
                    task["todoist_parent_id"] != todoist_task.get("parent_id")):
                todoist_api.update_task(
                    task["todoist_id"],
                    content=task["title"],
                    due={"string": task["due_date"]
                         } if task["due_date"] else None,
                    priority=task["priority"],
                    parent_id=task["todoist_parent_id"]
                )

        tasks_index[task["notion_id"]] = task["todoist_id"]

    todoist_api.sync()


def sync_todoist_to_notion(todoist_state):
    """Syncs changes from Todoist to Notion."""

    for project in todoist_state["projects"]:
        notion_project = get_notion_project_by_todoist_id(project["id"])
        if not notion_project:
            # Create a new project in Notion and set TodoistID
            new_project_id = create_notion_project(project)
            update_notion_project(
                new_project_id,  # Update the newly created project
                {"TodoistID": {"rich_text": [
                    {"text": {"content": project["id"]}}]}}
            )
        else:
            # Check for changes before updating
            if project["name"] != notion_project["name"]:
                update_notion_project(
                    notion_project["notion_id"],
                    {"Name": {
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
                parent_id = notion_parent_task["notion_id"]

        task_status = get_todoist_task_status(task)

        if not notion_task:
            # Create a new task in Notion
            new_task_id = create_notion_task(
                task, project_id, parent_id, task["project_id"])

        else:
            # Check for changes before updating
            if (task["content"] != notion_task["title"] or
                (task.get("due") and task["due"]["date"] != notion_task["due_date"]) or
                    task_status != notion_task["status"]):
                update_notion_task(
                    notion_task["notion_id"],
                    {
                        "Name": {"title": [{"text": {"content": task["content"]}}]},
                        "Due Date": {"date": {"start": task["due"]["date"]}} if task.get("due") else None,
                        "Status": {"select": {"name": task_status}},
                        "Project": {"relation": [{"id": project_id}]} if project_id else None,
                        "Parent": {"relation": [{"id": parent_id}]} if parent_id else None
                    }
                )


def get_todoist_task_status(task):
    return "Done" if task["checked"] else "Not Started"

```

## main.py

```python
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
        # Initialize TodoistSync object
        todoist_api = TodoistSync("YOUR_TODOIST_API_TOKEN")

        # Initial sync to get projects and items
        initial_sync_result = todoist_api.sync()

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
        sync_todoist_to_notion(initial_sync_result, notion_projects)
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

```

## combine.py

```python
import os

def combine_files_into_md(directory, output_file):
    """
    Combines all .py files in a directory into a single .md file,
    excluding the script itself, adding file names and relative paths as headers.

    Args:
        directory (str): The path to the directory containing the Python files.
        output_file (str): The path to the output .md file.
    """
    script_path = os.path.abspath(__file__)

    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.endswith(".py") and os.path.join(root, filename) != script_path:
                    filepath = os.path.join(root, filename)
                    relative_path = os.path.relpath(filepath, os.getcwd())

                    outfile.write(f"## {relative_path}\n\n")  # Markdown header for file name
                    outfile.write("```python\n")  # Start Python code block
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                    outfile.write("\n```\n\n")  # End Python code block

# Example usage:
project_directory = "."
combined_file = "combined_code.md"
combine_files_into_md(project_directory, combined_file)
```

## TodoistSync.py

```python
import requests
import json
from config import TODOIST_TOKEN


class TodoistSync:
    def __init__(self, api_token):
        self.api_token = api_token
        self.sync_token = "*"  # Initial sync token
        self.commands = []  # List to store commands

    def sync(self, resource_types=["projects", "items"]):
        """
        Synchronizes with Todoist API.

        Args:
            resource_types (list): List of resource types to sync.

        Returns:
            dict: A dictionary containing lists of created/updated and newly added projects and items.
        """
        headers = {"Authorization": f"Bearer {self.api_token}"}
        data = {
            "sync_token": self.sync_token,
            "resource_types": json.dumps(resource_types),
            "commands": json.dumps(self.commands),
        }

        response = requests.post(
            "https://api.todoist.com/sync/v9/sync", headers=headers, data=data
        )

        if response.status_code == 200:
            response_data = response.json()
            self.sync_token = response_data["sync_token"]  # Update sync token
            self.commands = []  # Clear commands after successful sync

            # Process the response to separate created/updated and new items
            created_updated_projects = response_data.get("projects", [])
            created_updated_items = response_data.get("items", [])
            new_projects = [
                project for project in created_updated_projects if project.get("is_new", False)
            ]
            new_items = [
                item for item in created_updated_items if item.get("is_new", False)
            ]

            return {
                "created_updated_projects": created_updated_projects,
                "created_updated_items": created_updated_items,
                "new_projects": new_projects,
                "new_items": new_items,
            }
        else:
            raise Exception(
                f"Sync failed with status code: {response.status_code}")

    def add_project(self, name):
        """Adds a new project."""
        temp_id = generate_uuid()
        command = {
            "type": "project_add",
            "temp_id": temp_id,
            "uuid": generate_uuid(),
            "args": {"name": name},
        }
        self.commands.append(command)
        return temp_id

    def add_task(self, content, project_id=None, due=None, priority=None, parent_id=None,
                 child_order=None, section_id=None, day_order=None, collapsed=None, labels=None,
                 assigned_by_uid=None, responsible_uid=None, auto_reminder=None, auto_parse_labels=None,
                 duration=None, description=None):  # Added description parameter
        """Adds a new task."""
        temp_id = generate_uuid()
        command = {
            "type": "item_add",
            "temp_id": temp_id,
            "uuid": generate_uuid(),
            "args": {"content": content},
        }
        if project_id:
            command["args"]["project_id"] = project_id
        if due:
            command["args"]["due"] = due
        if priority:
            command["args"]["priority"] = priority
        if parent_id:
            command["args"]["parent_id"] = parent_id
        if child_order:
            command["args"]["child_order"] = child_order
        if section_id:
            command["args"]["section_id"] = section_id
        if day_order:
            command["args"]["day_order"] = day_order
        if collapsed is not None:
            command["args"]["collapsed"] = collapsed
        if labels:
            command["args"]["labels"] = labels
        if assigned_by_uid:
            command["args"]["assigned_by_uid"] = assigned_by_uid
        if responsible_uid:
            command["args"]["responsible_uid"] = responsible_uid
        if auto_reminder is not None:
            command["args"]["auto_reminder"] = auto_reminder
        if auto_parse_labels is not None:
            command["args"]["auto_parse_labels"] = auto_parse_labels
        if duration:
            command["args"]["duration"] = duration
        if description:  # Added description handling
            command["args"]["description"] = description

        self.commands.append(command)
        return temp_id

    def update_task(self, task_id, content=None, due=None):
        """Updates an existing task."""
        command = {
            "type": "item_update",
            "uuid": generate_uuid(),
            "args": {"id": task_id},
        }
        if content:
            command["args"]["content"] = content
        if due:
            command["args"]["due"] = due
        self.commands.append(command)

    def update_project(self, project_id, name=None, color=None, collapsed=None, is_favorite=None, view_style=None):
        """Updates an existing project."""
        command = {
            "type": "project_update",
            "uuid": generate_uuid(),
            "args": {"id": project_id},
        }
        if name:
            command["args"]["name"] = name
        if color:
            command["args"]["color"] = color
        if collapsed is not None:
            command["args"]["collapsed"] = collapsed
        if is_favorite is not None:
            command["args"]["is_favorite"] = is_favorite
        if view_style:
            command["args"]["view_style"] = view_style
        self.commands.append(command)


def generate_uuid():
    """Generates a UUID (Universally Unique Identifier)."""
    import random
    import string
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=32))


# Example Usage
api_token = TODOIST_TOKEN
api = TodoistSync(api_token)

# Initial sync to get projects and items
initial_sync_result = api.sync()
print("Initial Sync Result:", json.dumps(initial_sync_result))

# Add a project
# project_temp_id = api.add_project("My New Project")

# # Add tasks
# task1_temp_id = api.add_task("Buy groceries", project_id=project_temp_id)
# task2_temp_id = api.add_task("Pay bills")

# # Update a task
# api.update_task(task1_temp_id, content="Buy milk and bread",
#                 due={"string": "tomorrow"})

# # Sync to execute commands and get updated data
# sync_result = api.sync()
# print("Sync Result:", sync_result)

# # Store the returned sync_token for the next sync
# stored_sync_token = api.sync_token
# print("Stored Sync Token:", stored_sync_token)

```

## todoist_handler.py

```python
import requests
import json
import uuid


class TodoistSync:
    def __init__(self, api_token, sync_token="*"):
        self.api_token = api_token
        self.sync_token = sync_token
        self.commands = []

    def sync(self, resource_types=["projects", "items"]):
        """Performs a synchronization with the Todoist API."""
        headers = {"Authorization": f"Bearer {self.api_token}"}
        data = {
            "sync_token": self.sync_token,
            "resource_types": json.dumps(resource_types),
            "commands": json.dumps(self.commands),
        }

        response = requests.post(
            "https://api.todoist.com/sync/v9/sync", headers=headers, data=data
        )

        if response.status_code == 200:
            response_data = response.json()
            self.sync_token = response_data["sync_token"]
            self.commands = []  # Clear commands after successful sync

            return response_data
        else:
            raise Exception(
                f"Sync failed with status code: {response.status_code}")

    def add_project(self, name):
        """Adds a project to the command queue."""
        temp_id = str(uuid.uuid4())
        command = {
            "type": "project_add",
            "temp_id": temp_id,
            "uuid": str(uuid.uuid4()),
            "args": {"name": name},
        }
        self.commands.append(command)
        return temp_id

    def add_task(self, content, project_id=None, due=None, priority=None, parent_id=None,
                 child_order=None, section_id=None, day_order=None, collapsed=None, labels=None,
                 assigned_by_uid=None, responsible_uid=None, auto_reminder=None, auto_parse_labels=None,
                 duration=None, description=None):
        """Adds a task to the command queue."""
        temp_id = str(uuid.uuid4())
        command = {
            "type": "item_add",
            "temp_id": temp_id,
            "uuid": str(uuid.uuid4()),
            "args": {"content": content},
        }
        if project_id:
            command["args"]["project_id"] = project_id
        if due:
            command["args"]["due"] = due
        if priority:
            command["args"]["priority"] = priority
        if parent_id:
            command["args"]["parent_id"] = parent_id
        # ... (add other optional parameters as needed)

        self.commands.append(command)
        return temp_id

    def update_task(self, task_id, content=None, due=None, priority=None, parent_id=None,
                    # ... other optional parameters
                    ):
        """Updates a task in the command queue."""
        command = {
            "type": "item_update",
            "uuid": str(uuid.uuid4()),
            "args": {"id": task_id},
        }
        if content:
            command["args"]["content"] = content
        if due:
            command["args"]["due"] = due
        if priority:
            command["args"]["priority"] = priority
        if parent_id:
            command["args"]["parent_id"] = parent_id
        # ... (add other optional parameters as needed)

        self.commands.append(command)

    def update_project(self, project_id, name=None, color=None, collapsed=None, is_favorite=None, view_style=None):
        """Updates a project in the command queue."""
        command = {
            "type": "project_update",
            "uuid": str(uuid.uuid4()),
            "args": {"id": project_id},
        }
        if name:
            command["args"]["name"] = name
        if color:
            command["args"]["color"] = color
        # ... (add other optional parameters as needed)

        self.commands.append(command)

    def get_project(self, project_id):
        """Retrieves a project from Todoist."""
        headers = {"Authorization": f"Bearer {self.api_token}"}
        data = {"project_id": project_id}

        response = requests.post(
            "https://api.todoist.com/sync/v9/projects/get", headers=headers, data=data
        )

        if response.status_code == 200:
            response_data = response.json()
            return response_data["project"]
        else:
            raise Exception(
                f"Failed to retrieve project: {response.status_code}")

    def get_task(self, task_id):
        """Retrieves a task from Todoist."""
        headers = {"Authorization": f"Bearer {self.api_token}"}
        data = {"item_id": task_id}

        response = requests.post(
            "https://api.todoist.com/sync/v9/items/get", headers=headers, data=data
        )

        if response.status_code == 200:
            response_data = response.json()
            return response_data["item"]
        else:
            raise Exception(f"Failed to retrieve task: {response.status_code}")

```

