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
