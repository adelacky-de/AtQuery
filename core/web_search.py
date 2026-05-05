# core/web_search.py
"""
AtQuery Web Synthesis Engine
----------------------------
When a user query does not match any built-in toolbox, this module:
  1. Asks an Ollama LLM to synthesize a QGIS Python tool from its own knowledge.
  2. Saves the synthesized tool to community_toolbox.json.
  3. Sends an email notification to the admin (adelacky.de@gmail.com).

The LLM-synthesis approach (no external search key needed) is used by default.
"""

import os
import json
import re
import time
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b"
NOTIFY_EMAIL = "adelacky.de@gmail.com"
COMMUNITY_TOOLBOX_PATH = os.path.join(os.path.dirname(__file__), "community_toolbox.json")

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


def send_community_update_email(tool_data: dict,
                                smtp_host: str = "smtp.gmail.com",
                                smtp_port: int = 587,
                                smtp_user: str = "",
                                smtp_pass: str = "") -> bool:
    """
    Sends an email notification to the admin when a new community tool is added.
    
    SETUP: Set smtp_user and smtp_pass via environment variables:
      ATQUERY_SMTP_USER=your@gmail.com
      ATQUERY_SMTP_PASS=your_app_password

    Gmail requires an App Password (not your regular password).
    Guide: https://support.google.com/accounts/answer/185833
    """
    smtp_user = smtp_user or os.environ.get("ATQUERY_SMTP_USER", "")
    smtp_pass = smtp_pass or os.environ.get("ATQUERY_SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        print("[AtQuery] Email skipped — ATQUERY_SMTP_USER / ATQUERY_SMTP_PASS not set.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[AtQuery] New Community Tool Added: {tool_data.get('name')}"
        msg["From"] = smtp_user
        msg["To"] = NOTIFY_EMAIL

        body_html = f"""
        <html><body>
        <h2>🛠️ AtQuery — New Community Tool</h2>
        <table border="1" cellpadding="8" cellspacing="0">
          <tr><td><b>Tool Name</b></td><td>{tool_data.get('name')}</td></tr>
          <tr><td><b>Description</b></td><td>{tool_data.get('description')}</td></tr>
          <tr><td><b>Keywords</b></td><td>{', '.join(tool_data.get('keywords', []))}</td></tr>
          <tr><td><b>Original Query</b></td><td><i>{tool_data.get('original_query')}</i></td></tr>
          <tr><td><b>Added At</b></td><td>{tool_data.get('added_at')}</td></tr>
          <tr><td><b>Source</b></td><td>{tool_data.get('source')}</td></tr>
        </table>
        <h3>Implementation Preview:</h3>
        <pre style="background:#f4f4f4;padding:10px">{tool_data.get('implementation', '')[:500]}</pre>
        <p>Review and curate at: <code>core/community_toolbox.json</code></p>
        </body></html>
        """
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, NOTIFY_EMAIL, msg.as_string())

        print(f"[AtQuery] 📧 Email notification sent to {NOTIFY_EMAIL}")
        return True

    except Exception as e:
        print(f"[AtQuery] Email notification failed: {e}")
        return False


def synthesize_and_register(query: str) -> dict | None:
    """
    High-level entry point: synthesize a tool, save it, and send email.
    Returns the tool_data dict if successful, else None.
    """
    tool_data = synthesize_tool_from_query(query)
    if not tool_data:
        return None

    saved = save_tool_to_community(tool_data)
    if saved:
        send_community_update_email(tool_data)

    return tool_data
