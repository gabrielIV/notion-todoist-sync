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
