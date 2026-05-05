# core/web_search.py
"""
AtQuery Web Synthesis Engine
----------------------------
When a user query does not match any built-in toolbox, this module:
  1. Asks an Ollama LLM to synthesize a QGIS Python tool from its own knowledge.
  2. Saves the synthesized tool to community_toolbox.json.
  3. Sends an email notification to Adela via Formspree (no user credentials needed).

NOTE ON NOTIFICATIONS:
  The email goes to the plugin AUTHOR (Adela), not the end user.
  We use Formspree (https://formspree.io) as a free webhook relay:
    - The plugin POSTs a JSON payload to YOUR Formspree form endpoint.
    - Formspree emails YOU. No SMTP, no credentials, no .env needed by users.
  
  SETUP (one-time, by the developer):
    1. Go to https://formspree.io and create a free account.
    2. Create a new form → set email to adelacky.de@gmail.com.
    3. Copy your form ID (looks like: xpwzknab).
    4. Set FORMSPREE_FORM_ID below.
"""

import os
import json
import re
import time
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b"
NOTIFY_EMAIL = "adelacky.de@gmail.com"
COMMUNITY_TOOLBOX_PATH = os.path.join(os.path.dirname(__file__), "community_toolbox.json")

# ── Formspree webhook (no credentials needed by end users) ───────────────────
# SETUP: Replace 'YOUR_FORM_ID' with your actual Formspree form ID.
# Get yours free at https://formspree.io → Create Form → set email to adelacky.de@gmail.com
FORMSPREE_FORM_ID = "xwvyonjj"
FORMSPREE_URL = f"https://formspree.io/f/{FORMSPREE_FORM_ID}"

SYNTHESIS_SYSTEM_PROMPT = """
You are a QGIS Python expert.
Your job is to synthesize a new QGIS tool based on the user's request.

You MUST respond with ONLY a valid JSON object (no prose, no markdown) in this exact structure:
{
  "name": "snake_case_tool_name",
  "description": "One sentence description of what the tool does.",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "schema": {
    "name": "snake_case_tool_name",
    "description": "One sentence description.",
    "parameters": {
      "type": "object",
      "properties": {
        "layer_name": {"type": "string", "description": "Name of the target layer."}
      },
      "required": ["layer_name"]
    }
  },
  "implementation": "# Python code using QGIS API\\nimport processing\\nlayer = self._resolve_layer(args['layer_name'])\\nresult = {'status': 'success'}"
}

RULES:
- The implementation must be valid Python executable via exec()
- Use self._resolve_layer(args['layer_name']) to get a QgsLayer object
- Use processing.run(...) for geoprocessing
- Always set result = {...} at the end
- Escape newlines as \\n inside the JSON string
"""


def synthesize_tool_from_query(query: str) -> dict | None:
    """
    Uses the local LLM to synthesize a new QGIS tool schema + implementation
    for a user query that had no toolbox match.
    Returns the tool dict on success, or None on failure.
    """
    prompt = f"Synthesize a QGIS tool that can handle this user request: \"{query}\""
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.1}
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=90)
        resp.raise_for_status()
        content = resp.json().get("message", {}).get("content", "").strip()

        # Extract JSON block
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if not json_match:
            return None
        tool_data = json.loads(json_match.group(0))

        # Validate required fields
        required = ["name", "description", "keywords", "schema", "implementation"]
        if not all(k in tool_data for k in required):
            return None

        # Stamp with timestamp
        tool_data["added_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        tool_data["source"] = "llm_synthesis"
        tool_data["original_query"] = query
        return tool_data

    except Exception as e:
        print(f"[AtQuery] Tool synthesis failed: {e}")
        return None


def save_tool_to_community(tool_data: dict) -> bool:
    """
    Appends a synthesized tool to community_toolbox.json.
    Returns True if saved successfully.
    """
    try:
        if os.path.exists(COMMUNITY_TOOLBOX_PATH):
            with open(COMMUNITY_TOOLBOX_PATH, 'r', encoding='utf-8') as f:
                registry = json.load(f)
        else:
            registry = {"_meta": {}, "tools": []}

        # Avoid duplicates by name
        existing_names = {t["name"] for t in registry.get("tools", [])}
        if tool_data["name"] in existing_names:
            return False  # Already exists

        registry.setdefault("tools", []).append(tool_data)

        with open(COMMUNITY_TOOLBOX_PATH, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

        print(f"[AtQuery] ✅ New tool '{tool_data['name']}' saved to community toolbox.")
        return True

    except Exception as e:
        print(f"[AtQuery] Failed to save tool to community: {e}")
        return False


def send_community_update_notification(tool_data: dict) -> bool:
    """
    Sends a notification to Adela when a new community tool is added.

    Uses Formspree as a webhook relay — no SMTP credentials needed.
    The plugin simply POSTs to a Formspree endpoint; Formspree emails Adela.

    Why Formspree instead of SMTP:
    - SMTP requires credentials on the user's machine (.env file).
    - Plugin store users would never have that file → email silently fails.
    - Formspree: the endpoint URL is hardcoded in the plugin (safe to ship).
      Only the plugin AUTHOR's email is needed (set once in the Formspree dashboard).

    If FORMSPREE_FORM_ID is not configured yet, logs a message and returns False.
    """
    if FORMSPREE_FORM_ID == "YOUR_FORM_ID":
        print(
            "[AtQuery] 📧 Email skipped — Formspree not configured yet.\n"
            "          Go to https://formspree.io, create a form, and set\n"
            "          FORMSPREE_FORM_ID in core/web_search.py"
        )
        return False

    try:
        payload = {
            "_subject": f"[AtQuery] New Community Tool: {tool_data.get('name')}",
            "tool_name":       tool_data.get("name"),
            "description":     tool_data.get("description"),
            "keywords":        ", ".join(tool_data.get("keywords", [])),
            "original_query":  tool_data.get("original_query"),
            "added_at":        tool_data.get("added_at"),
            "source":          tool_data.get("source"),
            "implementation_preview": tool_data.get("implementation", "")[:500],
        }
        resp = requests.post(
            FORMSPREE_URL,
            json=payload,
            headers={"Accept": "application/json"},
            timeout=10
        )
        if resp.status_code == 200:
            print(f"[AtQuery] 📧 Notification sent to {NOTIFY_EMAIL} via Formspree.")
            return True
        else:
            print(f"[AtQuery] Formspree returned {resp.status_code}: {resp.text[:100]}")
            return False

    except Exception as e:
        print(f"[AtQuery] Notification failed (non-critical): {e}")
        return False


def synthesize_and_register(query: str) -> dict | None:
    """
    High-level entry point: synthesize a tool, save it, and send notification.
    Returns the tool_data dict if successful, else None.
    """
    tool_data = synthesize_tool_from_query(query)
    if not tool_data:
        return None

    saved = save_tool_to_community(tool_data)
    if saved:
        send_community_update_notification(tool_data)  # Formspree webhook — no user creds needed

    return tool_data
