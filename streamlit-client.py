import streamlit as st
import openai
import os
import websockets
import json
import asyncio

# Define function to discover MCP tools
async def discover_mcp_tools():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # 1. Send initialize handshake
        initialize_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        await websocket.send(json.dumps(initialize_req))
        await websocket.recv()  # Ignore handshake response for now

        # 2. Send tools/list request
        tools_list_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        await websocket.send(json.dumps(tools_list_req))
        tools_response = await websocket.recv()
        tools = json.loads(tools_response)["result"]
        return tools

def mcp_tool_to_openai_function(tool):
    """Convert an MCP tool definition to OpenAI function-calling format."""
    return {
        "name": tool["name"],
        "description": tool["description"],
        "parameters": tool["inputSchema"]
    }

st.title("OpenAI Prompt Round-Trip App")

# Get the OpenAI API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OPENAI_API_KEY environment variable not set.")
    st.stop()

openai.api_key = api_key

# Add a form to handle Ctrl+Enter and button submit
with st.form(key="prompt_form"):
    prompt = st.text_area("Enter your prompt:", key="prompt_input")
    submitted = st.form_submit_button("Send to OpenAI")

# Button to discover tools
if st.button("Discover MCP Tools"):
    with st.spinner("Discovering tools from MCP server..."):
        try:
            tools = asyncio.run(discover_mcp_tools())
            st.session_state['mcp_tools'] = tools
            st.session_state['openai_functions'] = [mcp_tool_to_openai_function(tool) for tool in tools]
            st.success("Discovered tools:")
            st.json(tools)
        except Exception as e:
            st.error(f"Error discovering tools: {e}")

if submitted:
    if not prompt.strip():
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Waiting for OpenAI response..."):
            try:
                # Use the new OpenAI v1 API for streaming chat completions
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    stream=True
                )
                answer = ""
                response_placeholder = st.empty()
                for chunk in response:
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                        answer += chunk.choices[0].delta.content
                        response_placeholder.markdown(answer)
            except Exception as e:
                st.error(f"Error: {e}")
