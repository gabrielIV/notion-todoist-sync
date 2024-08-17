# Notion-Todoist Synchronization

This project provides a Python script to synchronize tasks and projects between Notion and Todoist. It uses the Notion API and the Todoist Sync API to keep your data consistent across both platforms.

## Features

- **Two-way Synchronization:** Synchronizes changes from Notion to Todoist and vice versa.
- **Project Synchronization:** Creates, updates, and deletes projects in both Notion and Todoist.
- **Task Synchronization:** Creates, updates, and deletes tasks in both Notion and Todoist, including task details such as title, due date, status, and priority.
- **Error Handling:** Includes error handling to gracefully handle unexpected situations and provide helpful error logs.
- **Scheduled Execution:** Can be scheduled to run automatically using GitHub Actions.
- **Manual Triggers:** Allows manual triggering of the synchronization process.
- **Secrets Management:** Uses GitHub Secrets to securely store API tokens and other sensitive information.

## Prerequisites

- **Python 3.x:** Make sure you have Python 3 installed on your system.
- **Notion API Token:** Obtain an API token from your Notion integration settings.
- **Todoist API Token:** Obtain an API token from your Todoist account settings.
- **Notion Database IDs:** Identify the IDs of your Notion databases for tasks, projects, and variables.
- **GitHub Account:** Required if you want to use GitHub Actions for scheduled execution.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/gabrielIV/notion-todoist-sync.git
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Create a `.env` file:**

   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file:**

   - Replace the placeholders with your actual API tokens and database IDs:

   ```
   NOTION_TOKEN=your_notion_api_token
   TODOIST_API_TOKEN=your_todoist_api_token
   NOTION_TASKS_DB_ID=your_notion_tasks_database_id
   NOTION_PROJECTS_DB_ID=your_notion_projects_database_id
   NOTION_VARIABLES_DB_ID=your_notion_variables_database_id
   ```

## Usage

### Manual Execution

1. **Activate the virtual environment (if you created one):**

   ```bash
   source .venv/bin/activate
   ```

2. **Run the script:**
   ```bash
   python main.py
   ```

### Scheduled Execution with GitHub Actions

1. **Set up secrets in your GitHub repository:**

   - Go to your repository on GitHub.
   - Navigate to "Settings" -> "Secrets and variables" -> "Actions".
   - Click "New repository secret".
   - For each environment variable in the `.env` file, create a corresponding secret with the same name and its value.

2. **Commit and push the changes to your repository.**

The workflow defined in `.github/workflows/main.yml` will run automatically every hour.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Notion API:** [https://developers.notion.com/](https://developers.notion.com/)
- **Todoist Sync API:** [https://developer.todoist.com/sync/v9/](https://developer.todoist.com/sync/v9/)
- **GitHub Actions:** [https://github.com/features/actions](https://github.com/features/actions)
