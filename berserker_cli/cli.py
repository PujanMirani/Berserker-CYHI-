import os
import sys
import subprocess

def main():
    # Find the directory where this python package is installed
    package_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(package_dir)
    
    # Path to the compiled Go binary
    binary_path = os.path.join(repo_root, "berserker")
    
    if not os.path.exists(binary_path):
        print(f"Error: The Berserker TUI binary was not found at {binary_path}")
        print("Compiling it now with 'go build -o berserker main.go'...")
        try:
            subprocess.run(["go", "build", "-o", "berserker", "main.go"], cwd=repo_root, check=True)
            print("Successfully compiled.")
        except Exception as e:
            print(f"Failed to compile Go binary. Do you have Go installed? Error: {e}")
            sys.exit(1)
            
    # Execute the Go binary
    # We pass the current Python executable so the Go binary can use it instead of a hardcoded venv path
    env = os.environ.copy()
    env["BERSERKER_PYTHON_EXEC"] = sys.executable
    env["BERSERKER_REPO_ROOT"] = repo_root
    
    try:
        subprocess.run([binary_path], cwd=os.getcwd(), env=env)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
