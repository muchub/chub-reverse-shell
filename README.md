# Chub Reverse Shell

## Description
Chub Reverse Shell is a Python application designed to set up a reverse shell server and manage client connections. It uses `ngrok` to create a secure tunnel for connecting clients 
and allows for command execution on the connected clients. The server captures and logs commands and data from clients, providing an interface for managing these interactions.

## Features
- Sets up a reverse shell server using Flask and `ngrok` for secure tunneling.
- Dynamically generates a payload script for clients to connect back to the server.
- Execute commands to clients and receives their responses.
- Tracks connected clients and logs received data and sent commands.
- Provides a web interface for managing and monitoring connected clients.

## Usage
1. Clone the repository:

    ```
    git clone https://github.com/muchub/chub-reverse-shel.git
    ```

2. Navigate to the project directory:

    ```
    cd chub-reverse-shel
    ```

3. Install the required dependencies:

    ```
    pip install -r requirements.txt
    ```

4. Run the script:

    ```
    python chub.py -p [PORT] 
    ```

5. Go to "http://localhost:5000/" for enter the panel
   
## Author
- **Muchub** - [GitHub](https://github.com/muchub)
