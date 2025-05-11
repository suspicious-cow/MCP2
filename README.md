# Model Context Protocol (MCP) Python Implementation

This project implements a functioning Model Context Protocol (MCP) server and client in Python, following the Anthropic MCP specification. It demonstrates the key patterns of the MCP protocol through a simple, interactive example.

## What is MCP?

The Model Context Protocol (MCP) is an open standard built on JSON-RPC 2.0 for connecting AI models to external data sources and tools. It defines a client-server architecture where an AI application communicates with one or more MCP servers, each exposing capabilities such as:

- **Tools**: Executable functions that perform actions
- **Resources**: Data sources that provide information
- **Prompts**: Predefined templates or workflows

MCP standardizes how these capabilities are discovered and invoked, serving as a "USB-C for AI" that allows models to interact with external systems in a structured way.

## Project Structure

- `server/`: MCP server implementation
  - `server.py`: WebSocket server that handles MCP requests and provides sample tools/resources
- `client/`: MCP client implementation
  - `client.py`: Demo client that connects to the server and exercises all MCP capabilities

## Features Demonstrated

This implementation showcases the core MCP protocol flow:

1. **Capability Negotiation**: Client-server handshake via `initialize`
2. **Capability Discovery**: Listing available tools and resources
3. **Tool Invocation**: Calling the `add_numbers` tool with parameters
4. **Resource Access**: Reading text content from a resource

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the MCP server (in one terminal):
   ```bash
   python server/server.py
   ```

2. Run the MCP client (in another terminal):
   ```bash
   python client/client.py
   ```

The client will connect to the server, perform the MCP handshake, discover capabilities, and demonstrate invoking tools and accessing resources with formatted output.

## How It Works

### MCP Server

The server:
- Accepts WebSocket connections
- Responds to JSON-RPC requests following the MCP specification
- Provides a sample tool (`add_numbers`)
- Provides a sample resource (`example.txt`)
- Supports the MCP handshake and capability discovery

### MCP Client

The client:
- Connects to the server via WebSocket
- Performs the MCP handshake
- Discovers available tools and resources
- Demonstrates calling a tool and reading a resource
- Presents the results in a formatted display

## Protocol Details

MCP implements these key methods:

| Method | Description |
|--------|-------------|
| `initialize` | Handshake to establish capabilities |
| `tools/list` | List available tools |
| `tools/call` | Call a tool with arguments |
| `resources/list` | List available resources |
| `resources/read` | Read resource content |
| `prompts/list` | List available prompts |

## Extending the Project

You can extend this implementation by:
- Adding more tools with different capabilities
- Adding dynamic resources that change on each read
- Implementing prompt templates for guided interactions
- Creating more interactive client applications

## References

- [Anthropic Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [WebSockets Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
