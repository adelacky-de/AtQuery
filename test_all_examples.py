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

mock_uic = MagicMock()
mock_uic.loadUiType.return_value = (DummyForm, object)
sys.modules['qgis.PyQt'].uic = mock_uic

# CRITICAL: Link the submodule mocks to the parent package mock attributes
sys.modules['qgis.PyQt'].QtWidgets = sys.modules['qgis.PyQt.QtWidgets']
sys.modules['qgis.PyQt'].QtCore = sys.modules['qgis.PyQt.QtCore']

sys.modules['processing'] = MagicMock()

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
    def __init__(self, uri_or_name="AdminArea_DCD_20230609.gdb_converted", name=None, provider=None):
        # Support both single-arg (for our tests) and 3-arg (for create_bbox_layer) constructors
        if name is None:
            # Single argument mode - uri_or_name is the layer name
            self._name = uri_or_name
        else:
            # Three argument mode - name is the layer name
            self._name = name
        
        self._fields = {
            "AdminArea_DCD_20230609.gdb_converted": ["OBJECTID", "NAME_EN", "NAME_TC", "AREA_CODE", "SHAPE_Area", "SHAPE_Length"],
            "Roads": ["OBJECTID", "NAME", "TYPE"],
            "Houses": ["OBJECTID", "ADDRESS"],
            "Schools": ["OBJECTID", "NAME"],
            "Parcels": ["OBJECTID", "PARCEL_ID", "OWNER"],
            "UrbanZones": ["OBJECTID", "ZONE_TYPE"],
            "Rivers": ["OBJECTID", "NAME"],
            "Buildings": ["OBJECTID", "TYPE"],
            "PropertyBoundaries": ["OBJECTID", "ID"],
            "BoundingBox": ["OBJECTID"],
            "Parcel_Info": ["OBJECTID", "PARCEL_ID", "INFO"]
        }
        self._valid = True
    
    def name(self):
        return self._name
    
    def fields(self):
        # Create proper field objects that have a name() method returning a string
        field_names = self._fields.get(self._name, ["OBJECTID"])
        
        class MockField:
            def __init__(self, field_name):
                self._field_name = field_name
            def name(self):
                return self._field_name
        
        return [MockField(fn) for fn in field_names]
    
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
    
    def isValid(self):
        return self._valid
    
    def dataProvider(self):
        mock_provider = MagicMock()
        mock_provider.addFeatures.return_value = True
        return mock_provider
    
    def updateExtents(self):
        pass

class QgsGeometry:
    @staticmethod
    def fromRect(rect):
        return QgsGeometry()

class QgsFeature:
    def __init__(self):
        pass
    def setGeometry(self, geom):
        pass

class QgsRectangle:
    def __init__(self, xmin, ymin, xmax, ymax):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

# Inject them into qgis.core
sys.modules['qgis.core'].QgsExpression = QgsExpression
sys.modules['qgis.core'].QgsFeatureRequest = QgsFeatureRequest
sys.modules['qgis.core'].QgsVectorLayer = QgsVectorLayer
sys.modules['qgis.core'].QgsGeometry = QgsGeometry
sys.modules['qgis.core'].QgsFeature = QgsFeature
sys.modules['qgis.core'].QgsRectangle = QgsRectangle

# Create layer instances for all test scenarios
layers = {
    "AdminArea_DCD_20230609.gdb_converted": QgsVectorLayer("AdminArea_DCD_20230609.gdb_converted"),
    "Roads": QgsVectorLayer("Roads"),
    "Houses": QgsVectorLayer("Houses"),
    "Schools": QgsVectorLayer("Schools"),
    "Parcels": QgsVectorLayer("Parcels"),
    "UrbanZones": QgsVectorLayer("UrbanZones"),
    "Rivers": QgsVectorLayer("Rivers"),
    "Buildings": QgsVectorLayer("Buildings"),
    "PropertyBoundaries": QgsVectorLayer("PropertyBoundaries"),
    "BoundingBox": QgsVectorLayer("BoundingBox"),
    "Parcel_Info": QgsVectorLayer("Parcel_Info")
}

def mock_mapLayersByName(name):
    return [layers[name]] if name in layers else []

def mock_addMapLayer(layer):
    # Add the layer to our layers dict
    layers[layer.name()] = layer
    return layer

# Set up the mock QgsProject BEFORE importing AtQuery_dockwidget
# This is crucial because when AtQuery_dockwidget imports, it will call QgsProject.instance()
mock_project = MagicMock()
mock_project.mapLayersByName.side_effect = mock_mapLayersByName
mock_project.mapLayers.return_value = layers
mock_project.addMapLayer.side_effect = mock_addMapLayer

# Patch QgsProject.instance to return our mock_project
sys.modules['qgis.core'].QgsProject = MagicMock()
sys.modules['qgis.core'].QgsProject.instance.return_value = mock_project

# Import the module to test
sys.path.append("/Users/adelachu/Desktop/WWU/AtQuery")
from atquery.AtQuery_dockwidget import AtQueryDockWidget
from atquery.ai_brain import get_system_prompt, get_tools

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
        mock_extent.xMinimum.return_value = 113.8
        mock_extent.yMinimum.return_value = 22.1
        mock_extent.xMaximum.return_value = 114.3
        mock_extent.yMaximum.return_value = 22.5
        self.iface.mapCanvas().extent.return_value = mock_extent
        
        # Mock the CRS for create_bbox_layer
        mock_crs = MagicMock()
        mock_crs.authid.return_value = "EPSG:4326"
        self.iface.mapCanvas().mapSettings().destinationCrs.return_value = mock_crs

class TestAllExamples(unittest.TestCase):
    def setUp(self):
        self.agent = TestableAtQueryDockWidget()

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_1_core_workflow(self, mock_post):
        """Example 1: Core Workflow - Handling a Vague Request"""
        print("\n--- Example 1: Core Workflow ---")
        
        messages = [{"role": "user", "content": "Select the Southern District in the 'AdminArea' layer."}]
        
        # Step 1: AI calls get_layer_list
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "get_layer_list", "arguments": {}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg_1 = self.agent._get_ai_response(messages)
        tool_output_1 = self.agent.handle_tool_call(json.dumps(ai_msg_1['tool_calls'][0]))
        self.assertIn("AdminArea_DCD_20230609.gdb_converted", tool_output_1)
        print(f"✅ Step 1: get_layer_list returned layers")
        
        messages.append(ai_msg_1)
        messages.append({"role": "tool", "content": tool_output_1})
        
        # Step 2: AI calls get_layer_details
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "get_layer_details", "arguments": {"layer_name": "AdminArea_DCD_20230609.gdb_converted"}}}]
            }
        }
        
        ai_msg_2 = self.agent._get_ai_response(messages)
        tool_output_2 = self.agent.handle_tool_call(json.dumps(ai_msg_2['tool_calls'][0]))
        self.assertIn("NAME_EN", tool_output_2)
        print(f"✅ Step 2: get_layer_details returned fields")
        
        messages.append(ai_msg_2)
        messages.append({"role": "tool", "content": tool_output_2})
        
        # Step 3: AI calls select_features
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "select_features", "arguments": {"layer_name": "AdminArea_DCD_20230609.gdb_converted", "sql": "\"NAME_EN\" = 'Southern District'"}}}]
            }
        }
        
        ai_msg_3 = self.agent._get_ai_response(messages)
        tool_output_3 = self.agent.handle_tool_call(json.dumps(ai_msg_3['tool_calls'][0]))
        self.assertIn("Selected and zoomed to", tool_output_3)
        print(f"✅ Step 3: select_features executed successfully")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_2_misspelled_layer(self, mock_post):
        """Example 2: Handling Misspelled Layer Name"""
        print("\n--- Example 2: Misspelled Layer Name ---")
        
        messages = [{"role": "user", "content": "Select stuff from 'AdminAre'."}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "get_layer_list", "arguments": {}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("AdminArea_DCD_20230609.gdb_converted", tool_output)
        print(f"✅ get_layer_list can help identify correct layer name")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_2b_misspelled_field(self, mock_post):
        """Example 2b: Handling Misspelled Field Name"""
        print("\n--- Example 2b: Misspelled Field Name ---")
        
        messages = [{"role": "user", "content": "Select features in 'AdminArea_DCD_20230609.gdb_converted' where 'NME_EN' is 'Southern District'."}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "get_layer_details", "arguments": {"layer_name": "AdminArea_DCD_20230609.gdb_converted"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("NAME_EN", tool_output)
        self.assertNotIn("NME_EN", tool_output)
        print(f"✅ get_layer_details can help identify correct field name")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_3_numeric_comparison(self, mock_post):
        """Example 3: Simple Numeric Comparison"""
        print("\n--- Example 3: Numeric Comparison ---")
        
        messages = [{"role": "user", "content": "Find all areas with a shape area greater than 5000000 in 'AdminArea_DCD_20230609.gdb_converted'."}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "select_features", "arguments": {"layer_name": "AdminArea_DCD_20230609.gdb_converted", "sql": "\"SHAPE_Area\" > 5000000"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("Selected and zoomed to", tool_output)
        print(f"✅ Numeric comparison query executed successfully")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_4_like_operator(self, mock_post):
        """Example 4: Partial String Match with LIKE"""
        print("\n--- Example 4: LIKE Operator ---")
        
        messages = [{"role": "user", "content": "Select areas that contain 'District' in their name from the 'AdminArea_DCD_20230609.gdb_converted' layer."}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "select_features", "arguments": {"layer_name": "AdminArea_DCD_20230609.gdb_converted", "sql": "\"NAME_EN\" LIKE '%District%'"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("Selected and zoomed to", tool_output)
        print(f"✅ LIKE operator query executed successfully")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_5_or_operator(self, mock_post):
        """Example 5: Multiple Conditions with OR"""
        print("\n--- Example 5: OR Operator ---")
        
        messages = [{"role": "user", "content": "Find Southern District or Eastern District in 'AdminArea_DCD_20230609.gdb_converted'."}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "select_features", "arguments": {"layer_name": "AdminArea_DCD_20230609.gdb_converted", "sql": "\"NAME_EN\" = 'Southern District' OR \"NAME_EN\" = 'Eastern District'"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("Selected and zoomed to", tool_output)
        print(f"✅ OR operator query executed successfully")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_6_in_operator(self, mock_post):
        """Example 6: Using the IN operator"""
        print("\n--- Example 6: IN Operator ---")
        
        messages = [{"role": "user", "content": "Select features in 'AdminArea_DCD_20230609.gdb_converted' where name is 'Southern District' or 'Eastern District'."}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "select_features", "arguments": {"layer_name": "AdminArea_DCD_20230609.gdb_converted", "sql": "\"NAME_EN\" IN ('Southern District', 'Eastern District')"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("Selected and zoomed to", tool_output)
        print(f"✅ IN operator query executed successfully")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_7_counting_features(self, mock_post):
        """Example 7: Counting Features"""
        print("\n--- Example 7: Counting Features ---")
        
        messages = [{"role": "user", "content": "How many features are in the 'AdminArea_DCD_20230609.gdb_converted' layer?"}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "select_features", "arguments": {"layer_name": "AdminArea_DCD_20230609.gdb_converted", "sql": "1=1"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("count", tool_output)
        print(f"✅ Counting query executed successfully")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_8_querying_fields(self, mock_post):
        """Example 8: Querying Layer Fields"""
        print("\n--- Example 8: Querying Layer Fields ---")
        
        messages = [{"role": "user", "content": "What fields does the AdminArea_DCD_20230609.gdb_converted layer have?"}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "get_layer_details", "arguments": {"layer_name": "AdminArea_DCD_20230609.gdb_converted"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("NAME_EN", tool_output)
        self.assertIn("SHAPE_Area", tool_output)
        print(f"✅ Field query executed successfully")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_9_spatial_within_distance(self, mock_post):
        """Example 9: Spatial Selection - Within Distance"""
        print("\n--- Example 9: Spatial - Within Distance ---")
        
        messages = [{"role": "user", "content": "Select houses within 500m of schools."}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "select_features", "arguments": {"layer_name": "Houses", "sql": "overlay_nearest('Schools', max_distance:=500)"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("Selected and zoomed to", tool_output)
        print(f"✅ Spatial within distance query executed successfully")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_10_spatial_within(self, mock_post):
        """Example 10: Spatial Selection - Contains/Within"""
        print("\n--- Example 10: Spatial - Within/Contains ---")
        
        messages = [{"role": "user", "content": "Select parcels that are inside the urban zones."}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "select_features", "arguments": {"layer_name": "Parcels", "sql": "overlay_within('UrbanZones')"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("Selected and zoomed to", tool_output)
        print(f"✅ Spatial within query executed successfully")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_11_spatial_intersects(self, mock_post):
        """Example 11: Spatial Selection - Intersects"""
        print("\n--- Example 11: Spatial - Intersects ---")
        
        messages = [{"role": "user", "content": "Select roads that intersect with rivers."}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "select_features", "arguments": {"layer_name": "Roads", "sql": "overlay_intersects('Rivers')"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("Selected and zoomed to", tool_output)
        print(f"✅ Spatial intersects query executed successfully")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_12_spatial_touches(self, mock_post):
        """Example 12: Spatial Selection - Touches"""
        print("\n--- Example 12: Spatial - Touches ---")
        
        messages = [{"role": "user", "content": "Find buildings that touch property boundaries."}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "select_features", "arguments": {"layer_name": "Buildings", "sql": "overlay_touches('PropertyBoundaries')"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("Selected and zoomed to", tool_output)
        print(f"✅ Spatial touches query executed successfully")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_13_create_bbox(self, mock_post):
        """Example 13: Creating a Bounding Box"""
        print("\n--- Example 13: Create Bounding Box ---")
        
        messages = [{"role": "user", "content": "Help me create a bounding box."}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "create_bbox_layer", "arguments": {"layer_name": "BoundingBox", "extent": "@map_extent"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("created successfully", tool_output)
        print(f"✅ Bounding box creation executed successfully")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    def test_example_14_select_within_bbox(self, mock_post):
        """Example 14: Spatial Selection - Within Bounding Box"""
        print("\n--- Example 14: Select Within Bounding Box ---")
        
        messages = [{"role": "user", "content": "Select parcels within the bounding box."}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "select_features", "arguments": {"layer_name": "Parcels", "sql": "overlay_within('BoundingBox')"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("Selected and zoomed to", tool_output)
        print(f"✅ Select within bbox query executed successfully")

    @patch('atquery.AtQuery_dockwidget.requests.post')
    @patch('atquery.AtQuery_dockwidget.processing.run')
    def test_example_15_join_attributes(self, mock_processing, mock_post):
        """Example 15: Joining Attributes"""
        print("\n--- Example 15: Join Attributes ---")
        
        # Mock the processing.run to return a successful result
        mock_processing.return_value = {"OUTPUT": MagicMock()}
        
        messages = [{"role": "user", "content": "Join the 'Parcel_Info' layer to the 'Parcels' layer using the 'PARCEL_ID' field."}]
        
        mock_post.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "join_attributes", "arguments": {"input_layer_name": "Parcels", "join_layer_name": "Parcel_Info", "input_join_field": "PARCEL_ID", "join_layer_field": "PARCEL_ID", "join_prefix": "info_"}}}]
            }
        }
        mock_post.return_value.status_code = 200
        
        ai_msg = self.agent._get_ai_response(messages)
        tool_output = self.agent.handle_tool_call(json.dumps(ai_msg['tool_calls'][0]))
        self.assertIn("success", tool_output)
        print(f"✅ Join attributes executed successfully")

