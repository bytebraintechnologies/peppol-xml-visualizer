import paramiko
from scp import SCPClient
import sys
import os
import time
from dotenv import load_dotenv

# Load env variables from .env file in project root
# We need to determine project root before we can reliably find .env if running from script dir
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
load_dotenv(os.path.join(project_root, ".env"))

# Credentials
HOST = os.getenv("AZURE_HOST")
USER = os.getenv("AZURE_USER")
PASS = os.getenv("AZURE_PASS")
PORT = 22

if not all([HOST, USER, PASS]):
    print("Error: AZURE_HOST, AZURE_USER, and AZURE_PASS must be set in .env file.")
    sys.exit(1)

# Files to transfer
# Files/Directories to transfer (relative to project root)
FILES_TO_TRANSFER = [
    "app",
    "assets",
    "requirements.txt",
    "Dockerfile",
    "Caddyfile",
    "test_data"
]

def create_ssh_client(server, port, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(server, port, user, password)
        return client
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None

def run_command(client, command, print_output=True):
    print(f"Running: {command}")
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    
    if print_output:
        if out: print(f"STDOUT: {out}")
        if err: print(f"STDERR: {err}")
    
    return exit_status, out, err

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    print(f"Connecting to {HOST}...")
    ssh = create_ssh_client(HOST, PORT, USER, PASS)
    if not ssh:
        sys.exit(1)

    print("Success! preparing to deploy.")

    # 1. Check/Install Docker
    print("\n--- Checking for Docker ---")
    status, out, err = run_command(ssh, "docker --version", print_output=False)
    if status != 0:
        print("Docker not found. Attempting to install Docker (assuming Ubuntu/Debian)...")
        # Simple convenience script install for Ubuntu
        run_command(ssh, "curl -fsSL https://get.docker.com -o get-docker.sh")
        run_command(ssh, f"echo '{PASS}' | sudo -S sh get-docker.sh")
        # Add permission to current user
        run_command(ssh, f"echo '{PASS}' | sudo -S usermod -aG docker {USER}")
        print("Docker installed. NOTE: You might need to re-login for group permissions to apply. Trying to proceed...")
    else:
        print(f"Docker is already installed: {out}")

    # 2. Transfer Files
    print("\n--- Transferring Files ---")
    # Make a directory
    remote_dir = "peppol-visualizer"
    run_command(ssh, f"mkdir -p {remote_dir}")

    try:
        with SCPClient(ssh.get_transport()) as scp:
            for item in FILES_TO_TRANSFER:
                local_path = os.path.join(project_root, item)
                if os.path.exists(local_path):
                    print(f"Uploading {item}...")
                    scp.put(local_path, recursive=True, remote_path=f"{remote_dir}")
                else:
                    print(f"Warning: Local item {local_path} not found!")
    except Exception as e:
        print(f"SCP Error: {e}")
        sys.exit(1)

    # 3. Build Docker Image
    print("\n--- Building Docker Image (this may take a while) ---")
    # Use sudo -S to accept password from stdin
    build_cmd = f"cd {remote_dir} && echo '{PASS}' | sudo -S docker build -t peppol-visualizer ."
    
    stdin, stdout, stderr = ssh.exec_command(build_cmd)
    
    # Stream output
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            line = stdout.channel.recv(1024).decode()
            sys.stdout.write(line)
        if stderr.channel.recv_ready():
             line = stderr.channel.recv(1024).decode()
             sys.stderr.write(line)

    if stdout.channel.recv_exit_status() != 0:
        print("Build failed.")
        sys.exit(1)

    # 4. Orchestrate Containers
    print("\n--- Orchestrating Containers ---")
    
    # Create Network if not exists
    run_command(ssh, f"echo '{PASS}' | sudo -S docker network create peppol-net || true")

    # Stop/Remove existing containers
    run_command(ssh, f"echo '{PASS}' | sudo -S docker rm -f caddy peppol-app || true")

    # Run API App (Internal only, attached to network)
    print("Starting API App...")
    run_command(ssh, f"echo '{PASS}' | sudo -S docker run -d --name peppol-app --network peppol-net --restart always peppol-visualizer")

    # Run Caddy (Public facing, maps ports 80 and 443)
    print("Starting Caddy Reverse Proxy...")
    # We mount the Caddyfile and the 'caddy_data' volume to persist certificates
    caddy_cmd = (
        f"echo '{PASS}' | sudo -S docker run -d --name caddy "
        "--network peppol-net "
        "--restart always "
        "-p 80:80 -p 443:443 "
        f"-v $(pwd)/{remote_dir}/Caddyfile:/etc/caddy/Caddyfile "
        "-v caddy_data:/data "
        "caddy:2-alpine"
    )
    status, out, err = run_command(ssh, caddy_cmd)

    if status == 0:
        print("\n-----------------------------------")
        print("DEPLOYMENT SUCCESSFUL (HTTPS Enabled)")
        print(f"HTTP:  http://{HOST}/render")
        print(f"HTTPS: https://{HOST}/render (Note: Self-signed warning expected for IP)")
        print("-----------------------------------")
        print("IMPORTANT: Ensure Port 443 is OPEN in your Azure Network Security Group!")
    else:
        print("Failed to run containers.")

    ssh.close()

if __name__ == "__main__":
    main()
