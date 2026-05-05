# test_brain_local.py
"""
AtQuery Local Test Suite
------------------------
Tests the full brain loop including the post-loop fallback constraint.

Usage:
  python -m test.test_brain_local                   # Run all tests
  python -m test.test_brain_local --verbose          # Verbose AI responses
  python -m test.test_brain_local --fallback=Y       # Simulate user choosing "Yes - Execute Best Match"
  python -m test.test_brain_local --fallback=N       # Simulate user choosing "No - Search & Learn"
  python -m test.test_brain_local --test=6           # Run only test #6 (unrecognized query)
"""

import requests
import json
import time
import re
import sys
import os

# Ensure root-level imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.ai_brain import (
    get_base_tools, get_toolbox_skills, get_system_prompt, get_forced_execution_prompt,
    identify_toolboxes, identify_community_toolbox, load_community_toolbox,
    get_available_toolboxes_summary, _load_catalog_from_md
)

MODEL_NAME = "qwen2.5:3b"
OLLAMA_URL = "http://localhost:11434/api/chat"

# ── MOCK DATA ─────────────────────────────────────────────────────────────────
MOCK_LAYERS = {
    "AdminArea_DCD": {
        "fields": ["OBJECTID", "NAME_EN", "SHAPE_Area", "NAME_TC"],
        "crs": "EPSG:4326"
    },
    "AdminArea_DCD_20230609.gdb_converted — DCD": {
        "fields": ["OBJECTID", "NAME_EN", "NAME_TC", "AREA_TYPE", "CSDI_ADMIN_AREA_ID"],
        "crs": "EPSG:4326"
    },
    "points_of_interest": {
        "fields": ["id", "name", "category"],
        "crs": "EPSG:4326"
    }
}

# ── TEST SUITE ────────────────────────────────────────────────────────────────
TEST_SUITE = [
    # Index  Query                                                       Expected outcome
    "what layers are in the project",                                    # 1 — ProjectDiscovery
    "buffer the 'AdminArea_DCD' layer by 500 meters",                    # 2 — VectorProcessing
    "select features from 'AdminArea_DCD' where NAME_EN is 'Southern District'",  # 3 — SelectionTools
    "calculate slope from 'dem_raster'",                                 # 4 — RasterAnalysis
    "add the OSM basemap",                                               # 5 — WebServices
    "calculate zonal statistics for the raster 'elevation' using 'AdminArea_DCD'", # 6 — NOT in any toolbox → FALLBACK
    "how do I make a sandwich",                                          # 7 — Non-GIS → FALLBACK
]

# ── MOCK TOOL HANDLER ─────────────────────────────────────────────────────────
def mock_handle_tool_call(tool_call_json):
    try:
        data = json.loads(tool_call_json)
        func = data.get("function", {})
        name = func.get("name")
        args = func.get("arguments", {})

        if name == 'get_toolbox_catalog':
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

        # Community toolbox tools — execute mock success
        return json.dumps({"status": "mock_success", "tool": name, "args": args})

    except Exception as e:
        return json.dumps({"error": str(e)})


# ── JSON REPAIR ───────────────────────────────────────────────────────────────
def repair_json_response(msg):
    if not msg.get('tool_calls') and msg.get('content'):
        content = msg['content'].strip()
        json_matches = re.findall(r'\{.*\}', content, re.DOTALL)
        for json_str in json_matches:
            try:
                json_str = json_str.replace('"parameters"', '"arguments"')
                data = json.loads(json_str)
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


# ── FALLBACK SIMULATION ───────────────────────────────────────────────────────
def simulate_fallback(query: str, choice: str, verbose: bool = False):
    """
    Headless simulation of the post-loop fallback constraint.
    choice: 'Y' = "Yes - Execute Best Match", 'N' = "No - Search & Learn"
    """
    print(f"\n  {'─'*60}")
    print(f"  ⚠️  POST-LOOP FALLBACK TRIGGERED")
    print(f"  {'─'*60}")

    toolboxes_summary = get_available_toolboxes_summary()
    print(f"  📋 Available toolboxes:\n{toolboxes_summary}")
    print(f"\n  Simulating user choice: [{choice}]")

    if choice.upper() == 'Y':
        # ── DIRECT FORCE EXECUTE ──────────────────────────────────────────
        print("  ⚡ Force-loading ALL toolboxes for direct execution...")
        catalog = _load_catalog_from_md()
        forced_tools = get_base_tools()
        for tb_name in catalog.keys():
            forced_tools.extend(get_toolbox_skills(tb_name))
        forced_tools.extend(load_community_toolbox())

        print(f"  ℹ️  Total tools available: {len(forced_tools)}")

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": get_forced_execution_prompt()},
                {"role": "user", "content": query}
            ],
            "tools": forced_tools,
            "stream": False,
            "options": {"temperature": 0.0}
        }

        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=90)
            resp.raise_for_status()
            ai_msg = resp.json().get("message", {})
            if verbose:
                print(f"  > Raw Force Response: {ai_msg}")

            if ai_msg.get("tool_calls"):
                for tc in ai_msg["tool_calls"]:
                    tool_name = tc.get("function", {}).get("name")
                    output = mock_handle_tool_call(json.dumps(tc))
                    print(f"  ✅ Force-executed: {tool_name} → {output[:80]}")
            else:
                print(f"  ℹ️  AI response (no tool): {ai_msg.get('content', '')[:120]}")
        except Exception as e:
            print(f"  ❌ Force-execute error: {e}")

    else:
        # ── SYNTHESIZE + REGISTER ─────────────────────────────────────────
        print("  🔍 Synthesizing new tool from AI knowledge...")
        try:
            from core.web_search import synthesize_and_register
            tool_data = synthesize_and_register(query)
            if tool_data:
                print(f"  ✅ New tool registered: '{tool_data['name']}'")
                print(f"     Description: {tool_data['description']}")
                print(f"     Keywords:    {', '.join(tool_data.get('keywords', []))}")
                print(f"     Saved to:    core/community_toolbox.json")
                print(f"     📧 Email notification queued to adelacky.de@gmail.com")
                if verbose:
                    print(f"     Implementation:\n{tool_data.get('implementation', '')[:300]}")
            else:
                print("  ⚠️  Synthesis failed (check Ollama connection)")
        except Exception as e:
            print(f"  ❌ Synthesis error: {e}")


# ── MAIN TEST LOOP ────────────────────────────────────────────────────────────
def run_tests(verbose=False, fallback_choice=None, only_test=None):
    print(f"\n{'='*20} AtQuery Automated Test Suite {'='*20}")
    print(f"Model: {MODEL_NAME} | Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    if fallback_choice:
        print(f"Fallback Mode: Simulating user choice = '{fallback_choice}'")
    print()

    test_list = [(i, q) for i, q in enumerate(TEST_SUITE, 1)]
    if only_test:
        test_list = [(i, q) for i, q in test_list if i == only_test]

    for idx, query in test_list:
        print(f"[{idx}] QUERY: \"{query}\"")
        start_time = time.time()

        # Pre-load based on keywords
        active_tools = get_base_tools()
        detected = identify_toolboxes(query)
        for tb in detected:
            skills = get_toolbox_skills(tb)
            if skills: active_tools.extend(skills)

        # Load community toolbox matches
        community_matches = identify_community_toolbox(query)
        if community_matches:
            active_tools.extend(community_matches)
            print(f"  🗂️  Community toolbox match: {len(community_matches)} tool(s) pre-loaded")

        turn_history = [{"role": "user", "content": query}]

        metrics = {
            "run_time": 0,
            "keywords": detected,
            "toolbox": "None",
            "tool": "None",
            "params": "None",
            "output": "None"
        }

        tool_was_executed = False

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

                # Check for proactive question without tool
                content = msg.get("content", "")
                if "?" in content and not msg.get("tool_calls"):
                    print(f"  > AI asked: \"{content}\"")
                    print("  > Simulating user response: \"YES\"")
                    turn_history.append({"role": "user", "content": "YES"})
                    continue

                if not msg.get("tool_calls"):
                    metrics["output"] = content.strip()
                    if metrics["output"]:
                        tool_was_executed = True  # AI gave a valid text response
                    break

                for tc in msg["tool_calls"]:
                    tool_name = tc.get("function", {}).get("name")
                    args = tc.get("function", {}).get("arguments", {})

                    metrics["tool"] = tool_name
                    metrics["params"] = json.dumps(args)

                    if tool_name == "load_toolbox_skills":
                        metrics["toolbox"] = args.get("toolbox_name")

                    output = mock_handle_tool_call(json.dumps(tc))
                    tool_was_executed = True

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
        print(f"  {'─'*60}")
        print(f"  | Run Time: {metrics['run_time']}s")
        print(f"  | Keywords: {', '.join(metrics['keywords']) if metrics['keywords'] else 'None'}")
        print(f"  | Toolbox:  {metrics['toolbox']}")
        print(f"  | Tool:     {metrics['tool']}")
        print(f"  | Query:    {metrics['params']}")
        output_str = str(metrics['output'])
        print(f"  | Output:   {output_str[:100]}{'...' if len(output_str) > 100 else ''}")
        print(f"  {'─'*60}")

        # ── POST-LOOP FALLBACK (headless simulation) ──────────────────────
        if not tool_was_executed:
            choice = fallback_choice or 'N'  # Default to synthesize in test mode
            simulate_fallback(query, choice, verbose)

        print()


if __name__ == "__main__":
    is_verbose = "--verbose" in sys.argv
    fallback_choice = None
    only_test = None

    for arg in sys.argv[1:]:
        if arg.startswith("--fallback="):
            fallback_choice = arg.split("=")[1].upper()
        if arg.startswith("--test="):
            only_test = int(arg.split("=")[1])

    run_tests(verbose=is_verbose, fallback_choice=fallback_choice, only_test=only_test)
