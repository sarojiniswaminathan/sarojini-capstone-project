import os
import json
import asyncio
import streamlit as st
from typing import Dict, Any
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Set up Gemini Client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------------------------------------
# 1. CUSTOM SKILL: Deterministic Material & Hours Allocator
# ---------------------------------------------------------
def allocate_materials_and_estimate_hours(
    garment_type: str, 
    required_fabric_name: str, 
    requested_meters: float
) -> Dict[str, Any]:
    """Custom Tailoring Skill: Checks fractional inventory against requirements,
    calculates reserved stock, and estimates labor hours based on Section 10 baselines.
    """
    # Baseline estimate lookup (Section 10)
    baseline_hours = {
        "Corset": 10.0,
        "Simple Dress": 6.5,
        "Fitted Dress": 12.0,
        "Trousers": 8.0,
        "Tuxedo": 16.0,
        "Alteration": 1.0
    }
    
    estimated_hours = baseline_hours.get(garment_type, 8.0)
    
    # Read current inventory state
    inventory_path = "./data/inventory.json"
    if os.path.exists(inventory_path):
        with open(inventory_path, "r") as f:
            inventory = json.load(f)
    else:
        inventory = []

    material_found = False
    is_available = False
    shortage = 0.0

    for item in inventory:
        if required_fabric_name.lower() in item["name"].lower():
            material_found = True
            if item["available_qty"] >= requested_meters:
                is_available = True
                # Reserve stock deterministically
                item["reserved_qty"] += requested_meters
                item["available_qty"] -= requested_meters
            else:
                shortage = requested_meters - item["available_qty"]
            break

    # Persist updated inventory state
    if material_found and is_available:
        with open(inventory_path, "w") as f:
            json.dump(inventory, f, indent=2)

    return {
        "garment_type": garment_type,
        "estimated_labor_hours": estimated_hours,
        "material_status": "AVAILABLE_AND_RESERVED" if is_available else "SHORTAGE_SOURCING_REQUIRED",
        "shortage_meters": shortage,
        "stage_breakdown": {
            "design_pattern_hrs": round(estimated_hours * 0.15, 1),
            "cutting_prep_hrs": round(estimated_hours * 0.15, 1),
            "construction_hrs": round(estimated_hours * 0.55, 1),
            "finishing_hrs": round(estimated_hours * 0.15, 1)
        }
    }

# ---------------------------------------------------------
# 2. MULTI-STEP AGENT LOOP WITH MCP CONNECTORS
# ---------------------------------------------------------
async def execute_agent_workflow(user_order_prompt: str, log_callback):
    # MCP Server Configurations
    gcal_mcp_params = StdioServerParameters(
        command="npx",
        args=["-y", "@sudomcp/google-calendar-mcp"],
        env={"GOOGLE_OAUTH_CREDENTIALS": "./credentials.json"}
    )
    
    fs_mcp_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "./data"]
    )

    log_callback("🟢 Initiating Agentic Loop...")
    
    async with stdio_client(gcal_mcp_params) as (gcal_read, gcal_write), \
               stdio_client(fs_mcp_params) as (fs_read, fs_write):
               
        async with ClientSession(gcal_read, gcal_write) as gcal_session, \
                   ClientSession(fs_read, fs_write) as fs_session:
            
            await gcal_session.initialize()
            await fs_session.initialize()

            # Tool Registration
            tool_handlers = {
                "allocate_materials_and_estimate_hours": lambda kwargs: allocate_materials_and_estimate_hours(**kwargs)
            }

            gcal_tools = await gcal_session.list_tools()
            fs_tools = await fs_session.list_tools()

            for t in gcal_tools.tools:
                tool_handlers[t.name] = lambda kwargs, name=t.name: gcal_session.call_tool(name, kwargs)
            for t in fs_tools.tools:
                tool_handlers[t.name] = lambda kwargs, name=t.name: fs_session.call_tool(name, kwargs)

            chat = client.chats.create(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    tools=[allocate_materials_and_estimate_hours],
                    system_instruction=(
                        "You are the Tailoring Business Agent. For new customer orders:\n"
                        "1. Use `allocate_materials_and_estimate_hours` skill to verify and reserve materials.\n"
                        "2. Check Google Calendar MCP to find fitting/sewing slots that avoid college classes.\n"
                        "3. Use Filesystem MCP to record the final job order sheet in `./data/`.\n"
                        "Always follow a strict Perceive -> Reason -> Act -> Observe loop."
                    )
                )
            )

            response = chat.send_message(user_order_prompt)
            
            while True:
                function_calls = response.function_calls
                if not function_calls:
                    log_callback("🏁 Workflow Execution Completed.")
                    return response.text

                for call in function_calls:
                    t_name = call.name
                    t_args = call.args
                    log_callback(f"🔹 [ACT] Executing Tool `{t_name}` with parameters: `{json.dumps(t_args)}`")

                    if t_name in tool_handlers:
                        res = tool_handlers[t_name](t_args)
                        if asyncio.iscoroutine(res):
                            res = await res
                        
                        output_content = res.content if hasattr(res, "content") else res
                        log_callback(f"🔸 [OBSERVE] Tool Result: `{output_content}`")
                        
                        response = chat.send_message(
                            types.Part.from_function_response(name=t_name, response={"result": output_content})
                        )

# ---------------------------------------------------------
# 3. WEB APP INTERFACE (STREAMLIT)
# ---------------------------------------------------------
def main():
    st.set_page_config(page_title="Tailoring Agent Control Center", layout="wide")
    st.title("🧵 Tailoring Business Agent — Operations Dashboard")
    st.caption("AI-Powered Order, Inventory, Production & Scheduling System")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Submit New Customer Order")
        garment = st.selectbox("Garment Type", ["Corset", "Simple Dress", "Fitted Dress", "Trousers", "Tuxedo", "Alteration"])
        fabric = st.selectbox("Required Fabric", ["Black Denim", "Red Satin", "Blue Cotton"])
        meters = st.number_input("Meters Required", min_value=0.5, max_value=10.0, value=2.5, step=0.25)
        notes = st.text_area("Customer Notes & Deadline", "Client needs this for a college gala next Friday. Bust: 36in, Waist: 28in.")
        
        submit_btn = st.button("Process Order with Agent Loop")

    with col2:
        st.subheader("Agent Execution Log (Perceive-Reason-Act-Observe)")
        log_box = st.empty()
        logs = []

        def append_log(msg):
            logs.append(msg)
            log_box.markdown("\n\n".join([f"- {l}" for l in logs]))

        if submit_btn:
            prompt = (
                f"Customer wants a {garment} using {meters}m of {fabric}. "
                f"Details: {notes}. Reserve materials, check schedule, and save job order."
            )
            with st.spinner("Agent running workflow..."):
                final_res = asyncio.run(execute_agent_workflow(prompt, append_log))
                st.success("Agent Workflow Complete!")
                st.markdown("### Final Agent Output")
                st.write(final_res)

if __name__ == "__main__":
    main()
