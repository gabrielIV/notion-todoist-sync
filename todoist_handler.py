import requests
import json
import uuid
from notion_handler import update_notion_task, update_notion_project
from config import logger


class TodoistSync:
    def __init__(self, api_token, sync_token="*"):
        self.api_token = api_token
        self.sync_token = sync_token
        self.commands = []

    def sync(self, resource_types=["projects", "items"]):
        """Performs a synchronization with the Todoist API."""
        logger.info("Full Syncing with Todoist API : " + self.sync_token)
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

            # update sync token
            self.sync_token = response_data["sync_token"]

            json.dump(response_data, open(
                "data/todoist_create_response_data.json", "w"), indent=2)

            # Update Notion with the new ID
            if notion_id:

                temp_id = command["temp_id"]
                new_id = response_data["temp_id_mapping"].get(
                    temp_id, args.get("id"))

                print("command_type : ", command_type)

                if command_type == "project_add":
                    update_notion_project(page_id=notion_id, properties={"TodoistID": {
                        "rich_text": [{"text": {"content": new_id}}]}})
                elif command_type == "item_add" or command_type == "item_move":

                    # get project id from response. filter out projecy_id from items
                    project_id = None
                    parent_id = None
                    for item in response_data["items"]:
                        if item["id"] == new_id:
                            project_id = item["project_id"]
                            parent_id = item["parent_id"]
                            break

                    if not project_id or not parent_id:
                        # check if they exist in args
                        project_id = args.get("project_id")
                        parent_id = args.get("parent_id")

                    print("Project ID : ", project_id)
                    print("Parent ID : ", parent_id)

                    properties = {"TodoistID": {
                        "rich_text": [{"text": {"content": new_id}}]},
                        "TodoistProjectID": {
                            "rich_text": [{"text": {"content": project_id}}]
                    }}

                    if parent_id:
                        properties["TodoistParentID"] = {
                            "rich_text": [{"text": {"content": parent_id}}]}

                    update_notion_task(page_id=notion_id,
                                       properties=properties)

                return new_id

            return response_data
        else:
            raise Exception(
                f"Command execution failed with status code: {response.status_code}")

    def add_project(self, name, notion_id=None):
        """Adds a project directly."""
        logger.info("Adding project to Todoist : " + name)
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
        logger.info("Updating task in Todoist : Name : " +
                    content)
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
        logger.info("Updating project in Todoist : " + name)
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

    def complete_task(self, task_id, date_completed=None):
        """Completes a task."""
        logger.info("Completing task in Todoist : " + task_id)
        args = {"id": task_id}
        if date_completed:
            args["date_completed"] = date_completed
        return self._create_command("item_complete", args)

    def uncomplete_task(self, task_id):
        """Uncompletes a task."""
        logger.info("Uncompleting task in Todoist : " + task_id)
        return self._create_command("item_uncomplete", {"id": task_id})

    def move_task(self, task_id, project_id=None, parent_id=None, notion_id=None):
        """Moves a task to a new project or parent task."""
        logger.info("Moving task in Todoist : " + task_id)
        args = {"id": task_id, }
        if project_id:
            args["project_id"] = project_id
        if parent_id:
            args["parent_id"] = parent_id

        print("Move Task Args : ", json.dumps(args, indent=2))
        return self._create_command("item_move", args, notion_id)
