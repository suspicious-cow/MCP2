import asyncio
import websockets
import json
from typing import Dict, Any
import sqlite3

# --- MCP Server Implementation ---
# This server accepts WebSocket connections and speaks JSON-RPC 2.0.
# It supports the MCP handshake (initialize), tool listing/calling, and resource listing/reading.

# Server info and capabilities (as per MCP spec)
SERVER_INFO = {
    "name": "ExamplePythonMCPServer",
    "version": "1.0.0"
}

CAPABILITIES = {
    "logging": {},
    "prompts": {"listChanged": False},
    "resources": {"subscribe": False, "listChanged": False},
    "tools": {"listChanged": False}
}

# Example tool definition (add two numbers)
TOOLS = [
    {
        "name": "add_numbers",
        "description": "Add two numbers and return the sum.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    },
    {
        "name": "employee_information",
        "description": "Get information about employees. (Stub: not yet implemented)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "department": {"type": "string", "description": "Department name (optional)"}
            },
            "required": []
        }
    }
]

# Example resource definition (static text file)
RESOURCES = [
    {
        "uri": "file:///example.txt",
        "name": "Example Text File",
        "description": "A static example text file.",
        "mimeType": "text/plain"
    }
]

# Resource content
RESOURCE_CONTENTS = {
    "file:///example.txt": "Hello, this is the content of example.txt!"
}

# Initialize SQLite database and sample data if not exists
def init_sqlite_db():
    import os
    db_path = os.path.join(os.path.dirname(__file__), 'company.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        hire_date TEXT NOT NULL
    )''')
    # Insert sample data if table is empty
    c.execute('SELECT COUNT(*) FROM employees')
    if c.fetchone()[0] == 0:
        c.executemany('''INSERT INTO employees (name, department, email, hire_date) VALUES (?, ?, ?, ?)''', [
            ('Alice Smith', 'Engineering', 'alice.smith@example.com', '2020-01-15'),
            ('Bob Johnson', 'Marketing', 'bob.johnson@example.com', '2019-07-23'),
            ('Carol Lee', 'Sales', 'carol.lee@example.com', '2021-03-10'),
            ('David Kim', 'Engineering', 'david.kim@example.com', '2018-11-05'),
            ('Eva Brown', 'HR', 'eva.brown@example.com', '2022-06-01')
        ])
    conn.commit()
    conn.close()

init_sqlite_db()

# WebSocket connection handler (note websockets.serve() expects this signature)
async def handle_jsonrpc(websocket):
    print("Client connected!")
    async for message in websocket:
        try:
            request = json.loads(message)
            print(f"Received message: {request}")
            response = await handle_request(request)
            if response is not None:
                print(f"Sending response: {response}")
                await websocket.send(json.dumps(response))
        except Exception as e:
            print(f"Error: {e}")
            # Send JSON-RPC error response
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -32603, "message": str(e)}
            }
            await websocket.send(json.dumps(error_response))

async def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    method = request.get("method")
    req_id = request.get("id")
    params = request.get("params", {})

    # --- MCP handshake ---
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": CAPABILITIES,
                "serverInfo": SERVER_INFO
            }
        }
    # --- Tools discovery ---
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": TOOLS
        }
    # --- Tools invocation ---
    elif method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        if name == "add_numbers":
            a = arguments.get("a")
            b = arguments.get("b")
            if a is not None and b is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"sum": a + b}
                }
            else:
                raise ValueError("Missing arguments for add_numbers")
        elif name == "employee_information":
            # Stub implementation
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"message": "This is a stub for employee_information. Not yet implemented."}
            }
        else:
            raise ValueError(f"Unknown tool: {name}")
    # --- Resources discovery ---
    elif method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": RESOURCES
        }
    # --- Resources read ---
    elif method == "resources/read":
        uris = params.get("uris", [])
        contents = []
        for uri in uris:
            if uri in RESOURCE_CONTENTS:
                contents.append({
                    "uri": uri,
                    "mimeType": "text/plain",
                    "text": RESOURCE_CONTENTS[uri]
                })
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"contents": contents}
        }
    # --- Prompts discovery (empty for now) ---
    elif method == "prompts/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": []
        }
    # --- Prompts get (not implemented) ---
    elif method == "prompts/get":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": "No prompts implemented."}
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"}
        }

async def main():
    print("Starting MCP server on ws://localhost:8765 ...")
    # Modern websockets library uses single-argument handlers (no path)
    async with websockets.serve(handle_jsonrpc, "localhost", 8765):
        print("Server started successfully!")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
