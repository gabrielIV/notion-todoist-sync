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