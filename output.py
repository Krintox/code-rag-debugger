import os

ALLOWED_FOLDERS = {"migrations", "models", "routers", "services", "utils"}
EXCLUDED_FOLDERS = {"__pycache__", "venv", "repositories"}

def collect_contents(root_folder, output_file):
    with open(output_file, "w", encoding="utf-8") as outfile:
        for foldername, subfolders, filenames in os.walk(root_folder):
            # Remove excluded folders so os.walk won't enter them
            subfolders[:] = [sf for sf in subfolders if sf not in EXCLUDED_FOLDERS]

            # relative path from root
            rel_path = os.path.relpath(foldername, root_folder)

            for filename in filenames:
                # Skip the output file itself if inside root folder
                if filename == output_file:
                    continue

                file_path = os.path.join(foldername, filename)

                # Check if file is in root or in allowed folders
                if (
                    rel_path == "."  # file is in root folder
                    or rel_path.split(os.sep)[0] in ALLOWED_FOLDERS
                ):
                    try:
                        with open(file_path, "r", encoding="utf-8") as infile:
                            outfile.write(f"\n--- File: {file_path} ---\n\n")
                            outfile.write(infile.read())
                            outfile.write("\n\n")
                    except Exception as e:
                        outfile.write(f"\n--- Could not read {file_path}: {e} ---\n\n")

if __name__ == "__main__":
    root_folder = os.getcwd()  # current directory
    output_file = "all_contents.txt"
    collect_contents(root_folder, output_file)
    print(f"✅ All contents written to {output_file}")
