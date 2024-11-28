import os
import subprocess
import sys

print("# Made by Kai Stephens, NOT SUITABLE FOR USE")

def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in process.stdout:
        print(line.decode(), end="")
    for line in process.stderr:
        print(line.decode(), end="")
    process.wait()
    if process.returncode != 0:
        sys.exit(f"Error: Command failed: {command}")

def create_virtual_env():
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        run_command(f"{sys.executable} -m venv venv")
    else:
        print("Virtual environment already exists.")

def activate_virtual_env():
    activate_script = "venv\\Scripts\\activate" if os.name == "nt" else "source venv/bin/activate"
    return activate_script

def install_requirements():
    if not os.path.exists("requirements.txt"):
        sys.exit("Error: 'requirements.txt' not found in the current directory.")
    
    print("Installing dependencies...")
    pip_executable = "venv\\Scripts\\pip" if os.name == "nt" else "venv/bin/pip"
    run_command(f"{pip_executable} install -r requirements.txt")

def check_flask_files():
    if not os.path.exists("app.py"):
        sys.exit("Error: 'app.py' not found in the current directory.")
    if not os.path.exists("templates"):
        sys.exit("Error: 'templates' directory not found in the current directory.")


if __name__ == "__main__":
    print("Setting up your environment and running the application...")
    create_virtual_env()
    install_requirements()
    check_flask_files()
