# test_brain_local.py
import requests
import json
import time
import re
import sys
from core.ai_brain import get_base_tools, get_toolbox_skills, get_system_prompt

MODEL_NAME = "qwen2.5:3b"
OLLAMA_URL = "http://localhost:11434/api/chat"

# --- MOCK DATA CONSTANTS ---
MOCK_LAYERS = {
    "AdminArea_DCD": {
        "fields": ["OBJECTID", "NAME_EN", "SHAPE_Area", "NAME_TC"],
        "crs": "EPSG:4326"
    },
    "AdminArea_DCD_20230609.gdb_converted \u2014 DCD": {
        "fields": ["OBJECTID", "NAME_EN", "NAME_TC", "AREA_TYPE", "CSDI_ADMIN_AREA_ID"],
        "crs": "EPSG:4326"
    },
    "points_of_interest": {
        "fields": ["id", "name", "category"],
        "crs": "EPSG:4326"
    }
}

# --- Automated Test Suite ---
TEST_SUITE = [
    "what layers are in the project",
    "buffer the 'AdminArea_DCD' layer by 500 meters",
    "select features from 'AdminArea_DCD' where NAME_EN is 'Southern District'",
    "calculate slope from 'dem_raster'",
    "add the OSM basemap",
    "create a TIN interpolation for 'points_of_interest' using the 'id' field",
    "invalid_query_test: how do I make a sandwich"
]

# --- Mock QGIS Tools ---
def mock_handle_tool_call(tool_call_json):
    try:
        data = json.loads(tool_call_json)
        func = data.get("function", {})
        name = func.get("name")
        args = func.get("arguments", {})

        if name == 'get_toolbox_catalog':
            # This would normally come from ai_brain, but we mock the output
            from core.ai_brain import _load_catalog_from_md
            catalog = _load_catalog_from_md()
            return json.dumps({"available_toolboxes": catalog})

        elif name == 'load_toolbox_skills':
            toolbox_name = args.get('toolbox_name')
            return json.dumps(get_toolbox_skills(toolbox_name))

        elif name == "QgsProject_mapLayers":
            return json.dumps({"layers": list(MOCK_LAYERS.keys())})

        elif name == 'QgsVectorLayer_fields':
            layer_name = args.get('layer_name')
            if layer_name in MOCK_LAYERS:
                return json.dumps({"layer_name": layer_name, "fields": MOCK_LAYERS[layer_name].get("fields", [])})
            return json.dumps({"error": f"Layer '{layer_name}' not found."})

        elif name == "processing_run_native_buffer":
            return json.dumps({"status": "success", "layer": f"{args.get('layer_name')}_buffer"})

        elif name == "processing_run_gdal_slope":
            return json.dumps({"status": "success", "raster": "slope_output"})

        elif name == "QgsProject_addXyzLayer":
            return json.dumps({"status": "success", "message": f"Added layer {args.get('layer_name')}"})

        elif name == "processing_run_qgis_tininterpolation":
            return json.dumps({"status": "success", "layer": "tin_output"})

        elif name == 'QgsVectorLayer_selectByExpression':
            return json.dumps({"layer": args.get('layer_name'), "sql": args.get('sql'), "count": 1, "action": "Selected"})

        return json.dumps({"error": f"Tool {name} not implemented in mock."})
    except Exception as e:
        return json.dumps({"error": str(e)})

# --- Robustness Layer (Same as in plugin) ---
def repair_json_response(msg):
    if not msg.get('tool_calls') and msg.get('content'):
        content = msg['content'].strip()
        # Find JSON blocks
        json_matches = re.findall(r'\{.*\}', content, re.DOTALL)
        for json_str in json_matches:
            try:
                # Basic repairs
                json_str = json_str.replace('"parameters"', '"arguments"')
                data = json.loads(json_str)
                
                # Check for direct function call vs tool_calls array
                if 'name' in data and 'arguments' in data:
                    msg['tool_calls'] = [{"id": "call_1", "type": "function", "function": data}]
                    msg['content'] = content.replace(json_str, "").strip()
                    break
                elif 'tool_calls' in data:
                    msg['tool_calls'] = data['tool_calls']
                    msg['content'] = content.replace(json_str, "").strip()
                    break
            except:
                continue
    return msg

# --- Main Test Loop ---
def run_tests(verbose=False):
    print(f"\n{'='*20} AtQuery Automated Test Suite {'='*20}")
    print(f"Model: {MODEL_NAME} | Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    for idx, query in enumerate(TEST_SUITE):
        print(f"[{idx+1}] QUERY: \"{query}\"")
        start_time = time.time()
        
        active_tools = get_base_tools()
        turn_history = [{"role": "user", "content": query}]
        
        metrics = {
            "run_time": 0,
            "keywords": [],
            "toolbox": "None",
            "tool": "None",
            "params": "None",
            "output": "None"
        }

        for step in range(5):
            payload = {
                "model": MODEL_NAME,
                "messages": [{"role": "system", "content": get_system_prompt()}] + turn_history,
                "tools": active_tools,
                "stream": False,
                "options": {"temperature": 0.0}
            }

            if verbose:
                print(f"  > Step {step+1} Requesting...")

            try:
                resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
                resp.raise_for_status()
                raw_msg = resp.json().get("message", {})
                
                if verbose:
                    print(f"  > Raw Response: {raw_msg}")

                msg = repair_json_response(raw_msg)
                turn_history.append(msg)

                # Check for Proactive Fallback (Question without Tool Call)
                content = msg.get("content", "")
                if "?" in content and not msg.get("tool_calls"):
                    print(f"  > AI asked: \"{content}\"")
                    print("  > Simulating user response: \"YES\"")
                    turn_history.append({"role": "user", "content": "YES"})
                    continue # Try again with the confirmation in history

                if not msg.get("tool_calls"):
                    metrics["output"] = msg.get("content", "").strip()
                    break

                for tc in msg["tool_calls"]:
                    tool_name = tc.get("function", {}).get("name")
                    args = tc.get("function", {}).get("arguments", {})
                    
                    metrics["tool"] = tool_name
                    metrics["params"] = json.dumps(args)

                    if tool_name == "load_toolbox_skills":
                        metrics["toolbox"] = args.get("toolbox_name")
                    
                    # Mock keyword identification (simplistic for test log)
                    if step == 0:
                        metrics["keywords"] = [k for k in ["buffer", "layers", "slope", "osm", "tin", "select"] if k in query.lower()]

                    output = mock_handle_tool_call(json.dumps(tc))
                    
                    if tool_name == "load_toolbox_skills":
                        new_skills = json.loads(output)
                        if isinstance(new_skills, list):
                            active_tools.extend(new_skills)

                    turn_history.append({"role": "tool", "content": output, "tool_call_id": tc.get("id")})
            
            except Exception as e:
                print(f"  ❌ Error at step {step+1}: {e}")
                break

        metrics["run_time"] = round(time.time() - start_time, 2)

        # Print Metrics Table
        print(f"  {'-'*60}")
        print(f"  | Run Time: {metrics['run_time']}s")
        print(f"  | Keywords: {', '.join(metrics['keywords']) if metrics['keywords'] else 'None'}")
        print(f"  | Toolbox:  {metrics['toolbox']}")
        print(f"  | Tool:     {metrics['tool']}")
        print(f"  | Query:    {metrics['params']}")
        print(f"  | Output:   {metrics['output'][:100]}...")
        print(f"  {'-'*60}\n")

if __name__ == "__main__":
    is_verbose = "--verbose" in sys.argv
    run_tests(verbose=is_verbose)
