import http.server
import socketserver
import urllib.parse
import os
import sys
import threading
import socket

# --- Configuration Constants ---
PORT = 80
YAML_FILE = 'config.yaml'
HOST1_USERNAME = 'isard'
HOST1_PASSWORD = 'pirineus'

# --- Concurrency Control ---
# Lock to ensure thread-safe access to the YAML file
file_lock = threading.Lock()

class RequestHandler(http.server.BaseHTTPRequestHandler):
    """
    Custom HTTP Request Handler to handle:
    - /insert: Add or update user data (name, email) with client IP.
    - /list: Display a sorted HTML list of users.
    - Other: Display usage instructions.
    """

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        # --- Endpoint: /insert ---
        if path == '/insert':
            self.handle_insert(parsed_path.query)
        
        # --- Endpoint: /list ---
        elif path == '/list':
            self.handle_list()
            
        # --- Default: Help Message ---
        else:
            self.handle_help()

    def handle_insert(self, query_string):
        """
        Process the /insert request.
        Parses query parameters and updates the YAML file.
        """
        query_params = urllib.parse.parse_qs(query_string, encoding='utf-8')
        
        name = query_params.get('name', [None])[0]
        email = query_params.get('email', [None])[0]
        
        if name and email:
            client_ip = self.client_address[0]
            
            # Use lock to prevent race conditions during file I/O
            user_count = 0
            with file_lock:
                user_count = self.update_yaml(client_ip, name, email)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Data saved successfully.\n")
            
            if user_count:
                print(f"UPDATE: {YAML_FILE} includes {user_count} users")
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            error_msg = "Missing 'name' or 'email' parameters.\nTip: Be careful to add \" when using curl (e.g., curl \"http://...&...\")\n"
            self.wfile.write(error_msg.encode('utf-8'))

    def handle_list(self):
        """
        Process the /list request.
        Reads the YAML file and returns an HTML list of users sorted by name.
        """
        cases = []
        with file_lock:
            cases = self.read_yaml_cases()

        # Sort cases alphabetically by name
        cases.sort(key=lambda x: x.get('name', '').lower())

        # Generate HTML
        html_content = "<html><body><h1>User List</h1><ul>"
        for case in cases:
            name = case.get('name', 'Unknown')
            email = case.get('email', 'Unknown')
            html_content += f"<li><b>{name}</b>: {email}</li>"
        html_content += "</ul></body></html>"

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def handle_help(self):
        """
        Display usage instructions for invalid paths.
        """
        help_text = """
Usage Instructions:

1. Insert Data:
   Endpoint: /insert
   Parameters: name, email
   Example (curl):
   $> curl "http://<SERVER_IP>/insert?name=John&email=john@example.com"

2. List Users:
   Endpoint: /list
   Description: Returns an HTML list of users sorted by name.
   Example (browser):
   http://<SERVER_IP>/list

Note: IP address is automatically detected and used as a unique identifier.
        """
        self.send_response(200) # Return 200 OK so users can read the help
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write((help_text.strip() + "\n").encode('utf-8'))

    def read_yaml_cases(self):
        """
        Reads the YAML file and returns a list of case dictionaries.
        """
        cases = []
        if os.path.exists(YAML_FILE):
            try:
                with open(YAML_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                current_case = {}
                for line in lines:
                    line = line.strip()
                    if line.startswith('#'):
                        if current_case:
                            cases.append(current_case)
                            current_case = {}
                        current_case['name'] = line[1:].strip()
                    elif line.startswith('- tt_members:'):
                        current_case['email'] = line.split(':', 1)[1].strip()
                    elif line.startswith(':host1_ip:'):
                        current_case['ip'] = line[len(':host1_ip:'):].strip()
                
                if current_case:
                    cases.append(current_case)
            except Exception as e:
                print(f"Error reading YAML: {e}")
        return cases

    def update_yaml(self, ip, name, email):
        """
        Updates the YAML file with the new user data.
        Ensures unique IP addresses (overwrites existing entry if IP matches).
        Returns the total number of users.
        """
        cases = self.read_yaml_cases()

        # Update existing case or append new one
        updated = False
        for case in cases:
            if case.get('ip') == ip:
                case['name'] = name
                case['email'] = email
                updated = True
                break
        
        if not updated:
            cases.append({'name': name, 'email': email, 'ip': ip})
            
        # Write back to file
        try:
            with open(YAML_FILE, 'w', encoding='utf-8') as f:
                f.write("global:\n")
                f.write(f"  :host1_username: {HOST1_USERNAME}\n")
                f.write(f"  :host1_password: {HOST1_PASSWORD}\n")
                f.write("cases:\n")
                for case in cases:
                    f.write(f"# {case.get('name', '')}\n")
                    f.write(f"- tt_members: {case.get('email', '')}\n")
                    f.write(f"  :host1_ip: {case.get('ip', '')}\n")
            
            return len(cases)
        except Exception as e:
            print(f"Error writing YAML: {e}")
            return 0

def run(server_class=http.server.HTTPServer, handler_class=RequestHandler):
    """
    Main function to start the HTTP server.
    """
    try:
        # Count existing users on startup
        user_count = 0
        if os.path.exists(YAML_FILE):
            try:
                with open(YAML_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.strip().startswith('# '):
                            user_count += 1
            except Exception as e:
                print(f"Warning: Could not read {YAML_FILE}: {e}")
        
        print(f"Starting server on port {PORT}...")
        print(f"{YAML_FILE} includes {user_count} users")
        
        # Display server listening information
        print(f"Server listening on ALL interfaces (0.0.0.0:{PORT})")
        print(f"Access the server using:")
        print(f"  http://<YOUR_IP>:{PORT}/")
        print(f"  (Run 'ip a' on Linux or 'ipconfig' on Windows to find your IP addresses)")
        
        server_address = ('', PORT)
        httpd = server_class(server_address, handler_class)
        httpd.serve_forever()
    except PermissionError:
        print(f"Error: Permission denied binding to port {PORT}. Try running as Administrator/root.")
    except OSError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
