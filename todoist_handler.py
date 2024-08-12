import requests
import json
import uuid
from notion_handler import update_notion_task, update_notion_project


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

    def _create_command(self, command_type, args, notion_id=None):
        """Creates and executes a command directly without using the command queue."""
        headers = {"Authorization": f"Bearer {self.api_token}"}
        command = {
            "type": command_type,
            "temp_id": str(uuid.uuid4()),
            "uuid": str(uuid.uuid4()),
            "args": args
        }
        data = {
            "sync_token": "*",  # Use "*" for immediate execution
            "resource_types": json.dumps(["projects", "items"]),
            "commands": json.dumps([command]),
        }

        response = requests.post(
            "https://api.todoist.com/sync/v9/sync", headers=headers, data=data
        )

        if response.status_code == 200:
            response_data = response.json()
            temp_id = command["temp_id"]
            new_id = response_data["temp_id_mapping"][temp_id]

            # Update Notion with the new ID
            if notion_id:
                if command_type == "project_add":
                    update_notion_project(page_id=notion_id, properties={"TodoistID": {
                        "rich_text": [{"text": {"content": new_id}}]}})
                elif command_type == "item_add":
                    update_notion_task(page_id=notion_id, properties={"TodoistID": {
                        "rich_text": [{"text": {"content": new_id}}]}})

            return response_data
        else:
            raise Exception(
                f"Command execution failed with status code: {response.status_code}")

    def add_project(self, name, notion_id=None):
        """Adds a project directly."""
        return self._create_command("project_add", {"name": name}, notion_id)

    def add_task(self, content, project_id=None, due=None, priority=None, parent_id=None,
                 child_order=None, section_id=None, day_order=None, collapsed=None, labels=None,
                 assigned_by_uid=None, responsible_uid=None, auto_reminder=None, auto_parse_labels=None,
                 duration=None, description=None, notion_id=None):
        """Adds a task directly."""
        args = {"content": content}
        if project_id:
            args["project_id"] = project_id
        if due:
            args["due"] = due
        if priority:
            args["priority"] = priority
        if parent_id:
            args["parent_id"] = parent_id
        # ... (add other optional parameters as needed)

        return self._create_command("item_add", args, notion_id)


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
            # raise Exception(
            #     f"Failed to retrieve project: {response.status_code}")
            print(f"Failed to retrieve project: {response.status_code}")
            return None

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
            # raise Exception(f"Failed to retrieve task: {response.status_code}")
            print(f"Failed to retrieve task: {response.status_code}")
            return None
