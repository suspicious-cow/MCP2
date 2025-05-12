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
        
async def discover_mcp_resources():
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

        # 2. Send resources/list request
        resources_list_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/list",
            "params": {}
        }
        await websocket.send(json.dumps(resources_list_req))
        resources_response = await websocket.recv()
        resources = json.loads(resources_response)["result"]
        return resources

def mcp_tool_to_openai_function(tool):
    """Convert an MCP tool definition to OpenAI function-calling format."""
    # Ensure the parameters schema has the required 'type' field at the top level
    params_schema = tool["inputSchema"].copy()  # Make a copy to avoid modifying the original
    
    # Add debug print to inspect the schema structure
    print(f"Converting tool {tool['name']} with schema: {json.dumps(params_schema)}")
    
    # Ensure schema has all required fields for OpenAI
    if "type" not in params_schema:
        params_schema["type"] = "object"
        
    # OpenAI expects 'properties' even if empty
    if "properties" not in params_schema:
        params_schema["properties"] = {}
    
    # Remove any src field that might cause issues with OpenAI
    if "src" in params_schema:
        del params_schema["src"]
        
    return {
        "name": tool["name"],
        "description": tool["description"],
        "parameters": params_schema
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

# Initialize session state if needed
if 'openai_functions' not in st.session_state:
    st.session_state['openai_functions'] = []
if 'mcp_tools' not in st.session_state:
    st.session_state['mcp_tools'] = []
if 'mcp_resources' not in st.session_state:
    st.session_state['mcp_resources'] = []
    
# Display status of MCP server connection
if st.session_state['mcp_tools']:
    st.sidebar.success(f"Connected to MCP server with {len(st.session_state['mcp_tools'])} tools")
    for tool in st.session_state['mcp_tools']:
        st.sidebar.write(f"- {tool['name']}")
else:
    st.sidebar.warning("Not connected to MCP server. Click 'Discover MCP Server' to connect.")

# Button to discover tools and resources
if st.button("Discover MCP Server"):
    with st.spinner("Discovering tools and resources from MCP server..."):
        try:
            tools = asyncio.run(discover_mcp_tools())
            # Debug: print the raw tools response
            st.write("[DEBUG] Raw tools response from MCP server:")
            st.json(tools)
            # Only store if valid list
            if not isinstance(tools, list):
                st.error(f"Error: MCP server did not return a list of tools. Got: {tools}")
            else:
                # Convert MCP tools to OpenAI functions
                openai_functions = []
                for tool in tools:
                    try:
                        openai_function = mcp_tool_to_openai_function(tool)
                        # Verify the function is valid
                        if all(k in openai_function for k in ["name", "description", "parameters"]):
                            openai_functions.append(openai_function)
                        else:
                            st.warning(f"Skipping invalid function: {tool['name']}")
                    except Exception as e:
                        st.warning(f"Error converting tool {tool.get('name', 'unknown')}: {e}")
                
                st.session_state['mcp_tools'] = tools
                st.session_state['openai_functions'] = openai_functions
            # Discover resources
            resources = asyncio.run(discover_mcp_resources())
            st.session_state['mcp_resources'] = resources
            st.success("Discovered tools and resources:")
            st.subheader("Tools")
            st.json(tools)
            st.subheader("Resources")
            st.json(resources)
        except Exception as e:
            st.error(f"Error discovering tools/resources: {e}")
            st.session_state['openai_functions'] = []

# Button to show employees table
if st.button("Show Employees Table"):
    import sqlite3
    import os
    db_path = os.path.join("server", "company.db")
    if not os.path.exists(db_path):
        st.error(f"Database not found at {db_path}. Please ensure the server has initialized the database.")
    else:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        try:
            c.execute("SELECT id, name, department, email, hire_date FROM employees")
            rows = c.fetchall()
            import pandas as pd
            df = pd.DataFrame(rows, columns=["ID", "Name", "Department", "Email", "Hire Date"])
            st.subheader("Employees Table")
            st.dataframe(df)
        except sqlite3.OperationalError as e:
            st.error(f"Database error: {e}")
        finally:
            conn.close()

if submitted:
    if not prompt.strip():
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Waiting for OpenAI response..."):
            try:
                openai_functions = st.session_state.get('openai_functions', None)
                st.write("[DEBUG] Functions sent to LLM:")
                st.json(openai_functions)
                
                # Validate the functions before sending them to OpenAI
                valid_functions = []
                if openai_functions:
                    for func in openai_functions:
                        try:
                            # Make sure each function has required fields
                            if all(k in func for k in ["name", "description", "parameters"]):
                                # Create a copy to avoid modifying the original
                                validated_func = func.copy()
                                validated_params = validated_func["parameters"].copy()
                                
                                # Validate that parameters is a valid JSON schema
                                if isinstance(validated_params, dict):
                                    # Add type if missing
                                    if "type" not in validated_params:
                                        validated_params["type"] = "object"
                                        
                                    # Ensure properties exists
                                    if "properties" not in validated_params:
                                        validated_params["properties"] = {}
                                        
                                    # Remove any src field
                                    if "src" in validated_params:
                                        del validated_params["src"]
                                        
                                    # Update the parameters in the function
                                    validated_func["parameters"] = validated_params
                                    valid_functions.append(validated_func)
                                    st.write(f"[DEBUG] Validated function: {validated_func['name']}")
                                else:
                                    st.warning(f"Function {func['name']} has invalid parameters schema type: {type(func['parameters'])}")
                            else:
                                missing = [k for k in ["name", "description", "parameters"] if k not in func]
                                st.warning(f"Function missing required fields: {missing}")
                        except Exception as e:
                            st.warning(f"Error validating function {func.get('name', 'unknown')}: {e}")
                
                # Try to serialize to JSON and print
                try:
                    st.write("[DEBUG] JSON serialization of validated functions:")
                    st.code(json.dumps(valid_functions, indent=2))
                except Exception as ser_e:
                    st.error(f"[DEBUG] JSON serialization error: {ser_e}")
                
                kwargs = {
                    'model': "gpt-4o",
                    'messages': [{"role": "user", "content": prompt}],
                    'stream': False  # We need to inspect the full response for function_call
                }
                if valid_functions:
                    kwargs['functions'] = valid_functions
                response = openai.chat.completions.create(**kwargs)
                # Check for function_call in the response
                message = response.choices[0].message
                if hasattr(message, 'function_call') and message.function_call:
                    st.write("[DEBUG] LLM requested function call:")
                    st.json({
                        'name': message.function_call.name,
                        'arguments': message.function_call.arguments
                    })
                    # Call the MCP server with the requested function
                    import ast
                    func_name = message.function_call.name
                    try:
                        func_args = json.loads(message.function_call.arguments)
                    except Exception:
                        # Sometimes arguments may be a stringified dict, try ast.literal_eval
                        func_args = ast.literal_eval(message.function_call.arguments)
                    async def call_mcp_tool(name, arguments):
                        uri = "ws://localhost:8765"
                        try:
                            st.write(f"[DEBUG] Connecting to MCP server at {uri} to call tool: {name}")
                            async with websockets.connect(uri) as websocket:
                                # 1. Send initialize handshake
                                initialize_req = {
                                    "jsonrpc": "2.0",
                                    "id": 1,
                                    "method": "initialize",
                                    "params": {
                                        "protocolVersion": "2024-11-05",
                                        "capabilities": {}
                                    }
                                }
                                await websocket.send(json.dumps(initialize_req))
                                handshake_response = await websocket.recv()
                                # Log handshake response for debugging
                                handshake_data = json.loads(handshake_response)
                                st.write("[DEBUG] MCP handshake successful:")
                                st.json(handshake_data)
                                
                                # 2. Call the tool
                                tools_call_req = {
                                    "jsonrpc": "2.0",
                                    "id": 2,
                                    "method": "tools/call",
                                    "params": {
                                        "name": name,
                                        "arguments": arguments
                                    }
                                }
                                st.write(f"[DEBUG] Sending tool call request for {name}:")
                                st.json(tools_call_req)
                                
                                await websocket.send(json.dumps(tools_call_req))
                                tools_call_response = await websocket.recv()
                                
                                try:
                                    response_data = json.loads(tools_call_response)
                                    st.write(f"[DEBUG] Received tool call response:")
                                    st.json(response_data)
                                    
                                    # Check for errors in the response
                                    if "error" in response_data:
                                        st.error(f"MCP server returned an error: {response_data['error']['message']}")
                                        return {"result": {"error": response_data["error"]}}
                                    
                                    return response_data
                                except json.JSONDecodeError as je:
                                    st.error(f"Failed to decode MCP response: {tools_call_response}")
                                    return {"result": {"error": f"JSON decode error: {str(je)}"}}
                        except websockets.exceptions.ConnectionError as ce:
                            st.error(f"Failed to connect to MCP server: {ce}")
                            return {"result": {"error": f"Connection error: {str(ce)}"}}
                        except Exception as e:
                            st.error(f"Error in call_mcp_tool: {e}")
                            return {"result": {"error": str(e)}}
                    mcp_result = asyncio.run(call_mcp_tool(func_name, func_args))
                    st.write("[DEBUG] MCP tool call result:")
                    st.json(mcp_result)
                    # Send the function result back to the LLM as a new message
                    function_response = mcp_result.get('result')
                    
                    # Make sure function_response is JSON serializable
                    if function_response is None:
                        st.error("MCP server returned no result - check server logs")
                        function_response = {"error": "No result returned from MCP server"}
                    
                    # Format the response to be sent as a function response message
                    function_response_str = None
                    try:
                        function_response_str = json.dumps(function_response)
                        st.write("[DEBUG] Formatted function result for LLM:")
                        st.code(function_response_str, language="json")
                    except TypeError as te:
                        st.error(f"Failed to serialize function response: {te}")
                        function_response_str = json.dumps({"error": f"Failed to serialize result: {str(te)}"})
                    
                    followup_kwargs = {
                        'model': "gpt-4o",
                        'messages': [
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": None, "function_call": {
                                "name": func_name,
                                "arguments": json.dumps(func_args)
                            }},
                            {"role": "function", "name": func_name, "content": function_response_str}
                        ],
                        'stream': True
                    }
                    
                    st.write("[DEBUG] Sending function result back to OpenAI for processing")
                    followup_response = openai.chat.completions.create(**followup_kwargs)
                    answer = ""
                    response_placeholder = st.empty()
                    for chunk in followup_response:
                        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                            answer += chunk.choices[0].delta.content
                            response_placeholder.markdown(answer)
                else:
                    # No function call, just show the LLM's answer
                    answer = message.content
                    st.markdown(answer)
            except Exception as e:
                st.error(f"Error: {e}")
