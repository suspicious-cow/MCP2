# MCP Python Server and Client

This project implements a minimal Model Context Protocol (MCP) server and client in Python, following the Anthropic MCP specification.

## Structure
- `server/`: MCP server implementation
- `client/`: MCP client implementation

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
- Run the server:
  ```bash
  python server/server.py
  ```
- Run the client:
  ```bash
  python client/client.py
  ```

## References
- [Anthropic Model Context Protocol Spec](https://modelcontextprotocol.io/)
