import os

EXCLUDE = {"__pycache__", ".git", "venv", "migrations"}

def print_structure(path, indent=0):
    for item in sorted(os.listdir(path)):
        if item in EXCLUDE:
            continue
        print("│   " * indent + "├── " + item)
        full_path = os.path.join(path, item)
        if os.path.isdir(full_path):
            print_structure(full_path, indent + 1)

print_structure(".")
