import sys
import json
import unittest
from unittest.mock import MagicMock, patch

# Mock QGIS modules BEFORE importing the actual module
sys.modules['qgis'] = MagicMock()
sys.modules['qgis.core'] = MagicMock()
sys.modules['qgis.PyQt'] = MagicMock()
sys.modules['qgis.PyQt.QtCore'] = MagicMock()
sys.modules['qgis.PyQt.QtWidgets'] = MagicMock()

# Define a dummy base class for QDockWidget so inheritance works properly
class MockQDockWidget:
    def __init__(self, parent=None):
        pass
    def closeEvent(self, event):
        pass

sys.modules['qgis.PyQt.QtWidgets'].QDockWidget = MockQDockWidget

# Mock uic.loadUiType to return a dummy class
class DummyForm:
    def setupUi(self, widget):
        pass

# We need to make sure qgis.PyQt.uic is available and loadUiType returns (DummyForm, object)
mock_uic = MagicMock()
mock_uic.loadUiType.return_value = (DummyForm, object)
sys.modules['qgis.PyQt'].uic = mock_uic

# CRITICAL: Link the submodule mocks to the parent package mock attributes
sys.modules['qgis.PyQt'].QtWidgets = sys.modules['qgis.PyQt.QtWidgets']
sys.modules['qgis.PyQt'].QtCore = sys.modules['qgis.PyQt.QtCore']

sys.modules['processing'] = MagicMock()

# Now we can import the classes we want to test
# We need to manually mock the specific classes used in AtQuery_dockwidget
from qgis.core import QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsRectangle

# Define dummy classes for QgsExpression and QgsFeatureRequest
class QgsExpression:
    def __init__(self, expr):
        self.expr = expr
    def hasParserError(self):
        return False
    def parserErrorString(self):
        return ""

class QgsFeatureRequest:
    def __init__(self, expr=None):
        pass
    def setFilterExpression(self, expr):
        pass

class QgsVectorLayer:
    def __init__(self):
        pass
    def name(self):
        return "AdminArea_DCD_20230609.gdb_converted"
    def fields(self):
        return [MagicMock(name=lambda: "NAME_EN"), MagicMock(name=lambda: "SHAPE_Area")]
    def getFeatures(self, request=None):
        return [MagicMock(id=lambda: 1)]
    def selectByIds(self, ids):
        pass
    def selectByExpression(self, expr):
        pass
    def boundingBoxOfSelected(self):
        return MagicMock()
    def selectedFeatureCount(self):
        return 1

# Inject them into qgis.core
sys.modules['qgis.core'].QgsExpression = QgsExpression
sys.modules['qgis.core'].QgsFeatureRequest = QgsFeatureRequest
sys.modules['qgis.core'].QgsVectorLayer = QgsVectorLayer

# Mock QgsProject instance
mock_project = MagicMock()
QgsProject.instance.return_value = mock_project

# Mock map layers
# Create an instance of our dummy QgsVectorLayer
mock_layer = QgsVectorLayer()
# We don't need to set return values for methods defined in the class, 
# but mapLayersByName needs to return this instance
mock_project.mapLayersByName.return_value = [mock_layer]
mock_project.mapLayers.return_value = {"layer_id": mock_layer}

# Import the module to test
# We assume the file is at /Users/adelachu/Desktop/WWU/AtQuery/atquery/AtQuery_dockwidget.py
sys.path.append("/Users/adelachu/Desktop/WWU/AtQuery")
from atquery.AtQuery_dockwidget import AtQueryDockWidget
from atquery.ai_brain import get_system_prompt, get_tools

print(f"DEBUG: AtQueryDockWidget type: {AtQueryDockWidget}")
print(f"DEBUG: AtQueryDockWidget bases: {AtQueryDockWidget.__bases__}")
print(f"DEBUG: dir(AtQueryDockWidget): {dir(AtQueryDockWidget)}")

# Create a test subclass that bypasses __init__
class TestableAtQueryDockWidget(AtQueryDockWidget):
    def __init__(self):
        # Bypass parent __init__ completely to avoid GUI setup
        self.model_name = "llama3:latest"
        self.chat_display = MagicMock()
        self.user_input = MagicMock()
        self.send_button = MagicMock()
        self.iface = MagicMock()
        
        # Mock the map canvas extent
        mock_extent = MagicMock()
        mock_extent.xMinimum.return_value = 0
        mock_extent.yMinimum.return_value = 0
        mock_extent.xMaximum.return_value = 100
        mock_extent.yMaximum.return_value = 100
        self.iface.mapCanvas().extent.return_value = mock_extent

class TestAtQueryFlow(unittest.TestCase):
    def setUp(self):
        self.agent = TestableAtQueryDockWidget()

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_select_southern_district_flow(self, mock_post):
        print("\n--- Starting Simulation: 'Select the Southern District' ---")
        
        # Scenario:
        # 1. User asks to select Southern District.
        # 2. AI calls get_layer_list (simulated).
        # 3. AI calls get_layer_details (simulated).
        # 4. AI calls select_features.
        # 5. AI gives final answer.

        # We will test the _get_ai_response payload construction and handle_tool_call logic.

        # --- Step 1: User Input ---
        user_text = "Select the Southern District in the 'AdminArea' layer."
        messages = [{"role": "user", "content": user_text}]
        
        # --- Step 2: AI Response (Mocked to return tool call) ---
        # Mocking Ollama response: AI wants to call get_layer_list
        mock_response_1 = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "function": {
                        "name": "get_layer_list",
                        "arguments": {} # Ollama returns dict
                    }
                }]
            }
        }
        mock_post.return_value.json.return_value = mock_response_1
        mock_post.return_value.status_code = 200

        print("-> Calling _get_ai_response (Step 1)...")
        ai_msg_1 = self.agent._get_ai_response(messages)
        
        # VERIFY PAYLOAD: Check if system prompt is in messages
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        self.assertEqual(payload['messages'][0]['role'], 'system')
        self.assertIn("MANDATORY CHECKLIST", payload['messages'][0]['content'])
        print("✅ Payload verification passed: System prompt is correctly placed.")

        # --- Step 3: Handle Tool Call (get_layer_list) ---
        print("-> Handling tool call: get_layer_list...")
        tool_call_1 = ai_msg_1['tool_calls'][0]
        tool_output_1 = self.agent.handle_tool_call(json.dumps(tool_call_1))
        print(f"   Tool Output: {tool_output_1}")
        self.assertIn("AdminArea_DCD_20230609.gdb_converted", tool_output_1)
        print("✅ Tool execution passed: get_layer_list returned layers.")

        # Update messages
        messages.append(ai_msg_1)
        messages.append({"role": "tool", "content": tool_output_1})

        # --- Step 4: AI Response (Mocked to return select_features) ---
        # Mocking Ollama response: AI now knows the layer and wants to select
        mock_response_2 = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "function": {
                        "name": "select_features",
                        "arguments": {
                            "layer_name": "AdminArea_DCD_20230609.gdb_converted",
                            "sql": "\"NAME_EN\" = 'Southern District'"
                        }
                    }
                }]
            }
        }
        mock_post.return_value.json.return_value = mock_response_2

        print("-> Calling _get_ai_response (Step 2)...")
        ai_msg_2 = self.agent._get_ai_response(messages)

        # --- Step 5: Handle Tool Call (select_features) ---
        print("-> Handling tool call: select_features...")
        tool_call_2 = ai_msg_2['tool_calls'][0]
        
        # Mock layer selection behavior
        # mock_layer.selectedFeatureCount.return_value = 1  <-- Removed this line
        
        tool_output_2 = self.agent.handle_tool_call(json.dumps(tool_call_2))
        print(f"   Tool Output: {tool_output_2}")
        self.assertIn("Selected and zoomed to", tool_output_2)
        print("✅ Tool execution passed: select_features executed.")

        # Update messages
        messages.append(ai_msg_2)
        messages.append({"role": "tool", "content": tool_output_2})

        # --- Step 6: AI Final Answer ---
        mock_response_3 = {
            "message": {
                "role": "assistant",
                "content": "Selected 1 feature in AdminArea_DCD_20230609.gdb_converted."
            }
        }
        mock_post.return_value.json.return_value = mock_response_3
        
        print("-> Calling _get_ai_response (Step 3)...")
        ai_msg_3 = self.agent._get_ai_response(messages)
        print(f"-> Final AI Response: {ai_msg_3['content']}")
        self.assertIn("Selected 1 feature", ai_msg_3['content'])
        print("✅ Simulation completed successfully.")

if __name__ == '__main__':
    unittest.main()
