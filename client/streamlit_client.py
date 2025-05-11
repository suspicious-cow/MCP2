import streamlit as st
import asyncio
import websockets
import json

st.set_page_config(page_title="MCP Streamlit Client", layout="wide")

def run_async(coro):
    # Create a new event loop for each async operation
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

class MCPClient:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.req_id = 1

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    async def send(self, method, params=None):
        if params is None:
            params = {}
        req = {
            "jsonrpc": "2.0",
            "id": self.req_id,
            "method": method,
            "params": params
        }
        await self.websocket.send(json.dumps(req))
        resp = await self.websocket.recv()
        self.req_id += 1
        return json.loads(resp)

    async def close(self):
        if self.websocket:
            await self.websocket.close()

st.title("MCP Streamlit Client")

server_url = st.text_input("MCP Server URL", "ws://localhost:8765")
connect_btn = st.button("Connect")

if "client" not in st.session_state:
    st.session_state.client = None
if "connected" not in st.session_state:
    st.session_state.connected = False

if connect_btn or st.session_state.connected:
    if not st.session_state.connected:
        client = MCPClient(server_url)
        try:
            # Explicitly run the connect method and check its result
            connection_result = run_async(client.connect())
            if connection_result:
                st.session_state.client = client
                st.session_state.connected = True
                st.success("Connected to MCP server!")
            else:
                st.error("Failed to connect to MCP server")
                st.session_state.connected = False
        except Exception as e:
            st.error(f"Failed to connect: {e}")
            st.session_state.connected = False

if st.session_state.connected and st.session_state.client:
    client = st.session_state.client

    # Handshake
    if st.button("Initialize (Handshake)"):
        resp = run_async(client.send("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "StreamlitClient", "version": "1.0.0"}
        }))
        st.json(resp)

    # Tools
    if st.button("List Tools"):
        resp = run_async(client.send("tools/list"))
        st.json(resp)
        if "result" in resp and isinstance(resp["result"], list):
            st.session_state.tools = resp["result"]
    if "tools" in st.session_state:
        st.subheader("Call Tool")
        tool_names = [tool["name"] for tool in st.session_state.tools]
        if tool_names:
            tool_choice = st.selectbox("Tool", tool_names)
            if tool_choice == "add_numbers":
                a = st.number_input("a", value=1)
                b = st.number_input("b", value=2)
                if st.button("Call add_numbers"):
                    resp = run_async(client.send("tools/call", {
                        "name": "add_numbers",
                        "arguments": {"a": a, "b": b}
                    }))
                    st.json(resp)

    # Resources
    if st.button("List Resources"):
        resp = run_async(client.send("resources/list"))
        st.json(resp)
        if "result" in resp and isinstance(resp["result"], list):
            st.session_state.resources = resp["result"]
    if "resources" in st.session_state:
        st.subheader("Read Resource")
        uris = [res["uri"] for res in st.session_state.resources]
        if uris:
            uri_choice = st.selectbox("Resource URI", uris)
            if st.button("Read Resource"):
                resp = run_async(client.send("resources/read", {
                    "uris": [uri_choice]
                }))
                st.json(resp)

    # Prompts (optional)
    if st.button("List Prompts"):
        resp = run_async(client.send("prompts/list"))
        st.json(resp)

    if st.button("Disconnect"):
        run_async(client.close())
        st.session_state.connected = False
        st.session_state.client = None
        st.success("Disconnected.")
