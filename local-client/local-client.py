import asyncio
import websockets
import json
import pprint

# --- MCP Client Implementation ---
# This client connects to the MCP server, performs handshake, lists capabilities, and invokes a tool and resource.

# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_section(title, content):
    """Print a formatted section with title and JSON content"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'-'*80}{Colors.END}")
    
    if isinstance(content, str):
        # Parse JSON string to dict
        try:
            parsed = json.loads(content)
            pretty_json = json.dumps(parsed, indent=2)
            print(f"{Colors.CYAN}{pretty_json}{Colors.END}")
        except:
            print(f"{Colors.YELLOW}{content}{Colors.END}")
    else:
        # Already a dict or other object
        pretty = pprint.pformat(content, indent=2)
        print(f"{Colors.CYAN}{pretty}{Colors.END}")

async def mcp_client():
    uri = "ws://localhost:8765"
    print(f"{Colors.GREEN}{Colors.BOLD}Connecting to MCP server at {uri}...{Colors.END}")
    
    async with websockets.connect(uri) as websocket:
        # 1. Send initialize handshake
        initialize_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {}  # client capabilities (empty for now)
            }
        }
        print_section("SENDING: Initialize Request", initialize_req)
        await websocket.send(json.dumps(initialize_req))
        
        response = await websocket.recv()
        print_section("RECEIVED: Server Capabilities", response)
        
        # Extract server capabilities for demonstration
        capabilities = json.loads(response)
        if "result" in capabilities:
            server_name = capabilities["result"]["serverInfo"]["name"]
            print(f"{Colors.GREEN}✓ Connected to {Colors.BOLD}{server_name}{Colors.END}")
            
            # Show what the server can do
            print(f"\n{Colors.YELLOW}Server supports:{Colors.END}")
            for cap, enabled in capabilities["result"]["capabilities"].items():
                if enabled:  # If not empty
                    print(f"{Colors.GREEN}  ✓ {cap}{Colors.END}")

        # 2. List tools
        tools_list_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        print_section("SENDING: Tools List Request", tools_list_req)
        await websocket.send(json.dumps(tools_list_req))
        
        response = await websocket.recv()
        print_section("RECEIVED: Available Tools", response)
        
        # Extract tool info for demonstration
        tools_data = json.loads(response)
        if "result" in tools_data and len(tools_data["result"]) > 0:
            print(f"\n{Colors.YELLOW}Available tools:{Colors.END}")
            for tool in tools_data["result"]:
                print(f"{Colors.GREEN}  ➤ {Colors.BOLD}{tool['name']}{Colors.END}: {tool['description']}")

        # 3. Call add_numbers tool
        tools_call_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "add_numbers",
                "arguments": {"a": 5, "b": 7}
            }
        }
        print_section("SENDING: Tool Call Request", tools_call_req)
        await websocket.send(json.dumps(tools_call_req))
        
        response = await websocket.recv()
        print_section("RECEIVED: Tool Call Result", response)
        
        # Extract result for demonstration
        result_data = json.loads(response)
        if "result" in result_data:
            print(f"\n{Colors.YELLOW}Result of add_numbers(5, 7):{Colors.END}")
            print(f"{Colors.GREEN}  = {Colors.BOLD}{result_data['result'].get('sum')}{Colors.END}")

        # 4. List resources
        resources_list_req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/list"
        }
        print_section("SENDING: Resources List Request", resources_list_req)
        await websocket.send(json.dumps(resources_list_req))
        
        response = await websocket.recv()
        print_section("RECEIVED: Available Resources", response)
        
        # Extract resources for demonstration
        resources_data = json.loads(response)
        if "result" in resources_data and len(resources_data["result"]) > 0:
            print(f"\n{Colors.YELLOW}Available resources:{Colors.END}")
            for resource in resources_data["result"]:
                print(f"{Colors.GREEN}  ➤ {Colors.BOLD}{resource['name']}{Colors.END} ({resource['uri']})")

        # 5. Read example resource
        resources_read_req = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "resources/read",
            "params": {"uris": ["file:///example.txt"]}
        }
        print_section("SENDING: Resource Read Request", resources_read_req)
        await websocket.send(json.dumps(resources_read_req))
        
        response = await websocket.recv()
        print_section("RECEIVED: Resource Content", response)
        
        # Extract content for demonstration
        content_data = json.loads(response)
        if "result" in content_data and "contents" in content_data["result"]:
            for content in content_data["result"]["contents"]:
                print(f"\n{Colors.YELLOW}Content of {content['uri']}:{Colors.END}")
                print(f"{Colors.GREEN}  {Colors.BOLD}{content['text']}{Colors.END}")
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.GREEN}{Colors.BOLD}MCP Demo Complete!{Colors.END}")

if __name__ == "__main__":
    asyncio.run(mcp_client())
