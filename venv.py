import os
import sys
import subprocess
import platform
import venv
import shutil

def create_virtualenv(venv_path):
    if not os.path.exists(venv_path):
        print(f"Creating virtual environment in '{venv_path}'...")
        # The EnvBuilder with_pip=True installs pip into the new venv.
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(venv_path)
        print("Virtual environment created.")
    else:
        print(f"Virtual environment already exists at '{venv_path}'.")

def get_pip_path(venv_path):
    # Determine the path to the pip executable inside the venv.
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
        venv_python = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
        venv_python = os.path.join(venv_path, "bin", "python")
    
    if os.path.exists(pip_path):
        print("pip is installed in the virtual environment.")
    else:
        print("pip was not found in the virtual environment. Attempting to install pip via ensurepip...")
        if not os.path.exists(venv_python):
            raise FileNotFoundError(f"Python executable not found in venv: {venv_python}")
        # Use the venv's Python to install pip
        subprocess.check_call([venv_python, "-m", "ensurepip", "--upgrade"])
        # Verify pip was installed
        if not os.path.exists(pip_path):
            raise RuntimeError("Failed to install pip in the virtual environment after ensurepip.")
    return pip_path

def install_requirements(pip_path):
    req_file = "requirements.txt"
    if os.path.exists(req_file):
        print(f"Installing packages from '{req_file}'...")
        try:
            subprocess.check_call([pip_path, "install", "-r", req_file])
            print("Requirements installed successfully.")
        except subprocess.CalledProcessError as e:
            print("Error installing requirements:", e)
    else:
        print("No requirements.txt found, skipping package installation.")

def launch_venv_shell(venv_path):
    print("Launching an interactive shell within the virtual environment...")
    if platform.system() == "Windows":
        # On Windows, launch cmd with the activate script.
        activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
        if os.path.exists(activate_script):
            subprocess.call(["cmd.exe", "/k", activate_script])
        else:
            print(f"Activation script not found at {activate_script}.")
    else:
        # On Unix-like systems, spawn a bash shell with the venv activated.
        activate_script = os.path.join(venv_path, "bin", "activate")
        if os.path.exists(activate_script):
            # The following command sources the activate script and then starts an interactive bash shell.
            subprocess.call(["/bin/bash", "-c", f"source {activate_script} && exec bash"])
        else:
            print(f"Activation script not found at {activate_script}.")

def main():
    venv_dir = "venv"  # Name or path for the virtual environment folder.
    create_virtualenv(venv_dir)
    pip_path = get_pip_path(venv_dir)
    install_requirements(pip_path)
    launch_venv_shell(venv_dir)

if __name__ == "__main__":
    main()
