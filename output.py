import os

def collect_contents(root_folder, output_file):
    with open(output_file, "w", encoding="utf-8") as outfile:
        for foldername, subfolders, filenames in os.walk(root_folder):
            for filename in filenames:
                # Skip the output file itself if inside root folder
                if filename == output_file:
                    continue

                file_path = os.path.join(foldername, filename)
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
