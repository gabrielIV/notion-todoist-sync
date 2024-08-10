# Notion-Todoist Sync

This project synchronizes tasks and projects between Notion and Todoist.

## Setup

### Prerequisites

- [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed on your system.

### Creating and Activating the Conda Environment

1. Clone this repository:

   ```
   git clone https://github.com/your-username/notion-todoist-sync.git
   cd notion-todoist-sync
   ```

2. Create the Conda environment from the `environment.yml` file:

   ```
   conda env create -f environment.yml
   ```

3. Activate the environment:

   - On Windows:

     ```
     conda activate notion-todoist-sync
     ```

   - On macOS and Linux:
     ```
     source activate notion-todoist-sync
     ```

   Note: If the above command doesn't work, try:

   ```
   conda activate notion-todoist-sync
   ```

   You should see `(notion-todoist-sync)` at the beginning of your command prompt, indicating that the environment is active.

4. Verify the environment is activated:
   ```
   conda info --envs
   ```
   The active environment should have an asterisk (\*) next to it.

Important: Always make sure to activate the Conda environment before running the script or installing additional packages. You'll need to activate the environment each time you open a new terminal window or start a new session.

### Setting Environment Variables

[... rest of the environment variables section ...]

## Running the Sync

1. Ensure your Conda environment is activated:

   ```
   conda activate notion-todoist-sync
   ```

2. Run the synchronization script:
   ```
   python main.py
   ```

## Development

If you need to add new dependencies:

1. Activate the Conda environment:

   ```
   conda activate notion-todoist-sync
   ```

2. Add the dependency to `environment.yml`

3. Update the environment:
   ```
   conda env update -f environment.yml --prune
   ```

## Deactivating the Environment

When you're done working on the project, you can deactivate the Conda environment:

```
conda deactivate
```

## Troubleshooting

If you encounter any issues, ensure:

- Your Conda environment is activated before running the script or installing packages.
- Your API tokens are correct and have the necessary permissions.
- Your Notion databases are set up correctly.
- You're using the correct database IDs.
- Environment variables are set correctly and accessible to the script.

If you're having trouble activating the environment, try:

- Closing and reopening your terminal.
- Updating Conda: `conda update -n base -c defaults conda`
- Reinstalling the environment:
  ```
  conda remove --name notion-todoist-sync --all
  conda env create -f environment.yml
  ```

For any other issues, please open an issue on the GitHub repository.
