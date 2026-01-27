--- 

## 8. CRS and Projections

This section details how to handle Coordinate Reference Systems (CRS) and CRS transformations in PyQGIS using the `QgsCoordinateReferenceSystem` and `QgsCoordinateTransform` classes.

### Key Classes and Functions:

## QgsCoordinateReferenceSystem
*logic: Encapsulates a Coordinate Reference System. Can be created using various identifiers like EPSG codes (e.g., "EPSG:4326"), Well-Known Text (WKT) strings, or other QGIS internal IDs.
*example:
```python
from qgis.core import QgsCoordinateReferenceSystem

# Create a CRS from an EPSG code
crs_epsg = QgsCoordinateReferenceSystem("EPSG:4326")
print(f"CRS from EPSG: {crs_epsg.isValid()}, {crs_epsg.description()}")

# Create a CRS from WKT (example WKT for WGS 84)
wkt_string = 'GEOGCRS["WGS 84",DATUM["World Geodetic System 1984",ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],CS[ellipsoidal,2],AXIS["geodetic latitude (Lat)",north,ORDER[1],ANGLEUNIT["degree",0.0174532925199433]],AXIS["geodetic longitude (Lon)",east,ORDER[2],ANGLEUNIT["degree",0.0174532925199433]],USAGE[SCOPE["Horizontal component of 3D system."],AREA["World."],BBOX[-90,-180,90,180]],ID["EPSG",4326]]'
crs_wkt = QgsCoordinateReferenceSystem(wkt_string)
print(f"CRS from WKT: {crs_wkt.isValid()}, {crs_wkt.description()}")

# Access CRS properties
print(f"EPSG ID: {crs_epsg.srsid()}")
print(f"Projection Acronym: {crs_epsg.projectionAcronym()}")
```

## QgsCoordinateTransform
*logic: Handles the transformation of coordinates between two different Coordinate Reference Systems.
*example:
```python
from qgis.core import QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform

# Define source and destination CRS
source_crs = QgsCoordinateReferenceSystem("EPSG:4326") # WGS 84 Geographic
dest_crs = QgsCoordinateReferenceSystem("EPSG:3857")   # WGS 84 / Pseudo-Mercator (for web maps)

# Create a coordinate transform object
transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())

# Point to transform (e.g., New York City)
point_wgs84 = QgsPointXY(-74.0060, 40.7128)

# Perform the transformation
point_mercator = transform.transform(point_wgs84)
print(f"Original WGS84: {point_wgs84.x()}, {point_wgs84.y()}")
print(f"Transformed Mercator: {point_mercator.x()}, {point_mercator.y()}")
```

### Important Note for Standalone Applications:
For standalone PyQGIS applications, ensure `QgsApplication.setPrefixPath()` is correctly configured to allow QGIS to locate its internal CRS database.

### Provided Code Snippet (Common Imports):
```python
from qgis.core import (
  QgsApplication,
  QgsDataSourceUri,
  QgsCategorizedSymbolRenderer,
  QgsClassificationRange,
  QgsPointXY,
  QgsProject,
  QgsExpression,
  QgsField,
  QgsFields,
  QgsFeature,
  QgsFeatureRequest,
  QgsFeatureRenderer,
  QgsGeometry,
  QgsGraduatedSymbolRenderer,
  QgsMarkerSymbol,
  QgsMessageLog,
  QgsRectangle,
  QgsRendererCategory,
  QgsRendererRange,
  QgsSymbol,
  QgsVectorDataProvider,
  QgsVectorLayer,
  QgsVectorFileWriter,
  QgsWkbTypes,
  QgsSpatialIndex,
  QgsVectorLayerUtils
)

from qgis.core.additions.edit import edit

from qgis.PyQt.QtGui import (
    QColor,
)
```

---

## Project and Layer Tools

This section covers tools for interacting with the QGIS project and layers.

## QgsProject_mapLayers
*logic: Returns a list of all layer names in the current QGIS project. ALWAYS call this first to check available layers before attempting any geospatial operations.
*example:
```python
from qgis.core import QgsProject

# Get a dictionary of all map layers in the project
layers = QgsProject.instance().mapLayers()

# Get a list of layer names
layer_names = [layer.name() for layer in layers.values()]
print(layer_names)
```

## QgsVectorLayer_fields
*logic: Retreives the field names for a specific layer. You MUST call this if the user asks for attributes, fields, or columns.
*example:
```python
from qgis.core import QgsProject

layer_name = "my_vector_layer"  # Replace with your layer name
layer = QgsProject.instance().mapLayersByName(layer_name)[0]

# Get a list of field names
field_names = [field.name() for field in layer.fields()]
print(field_names)
```

## QgsVectorLayer_selectByExpression
*logic: Selects features from a vector layer based on an SQL-like query expression and zooms to the selection.
*example:
```python
from qgis.core import QgsProject, QgsExpression

layer_name = "my_vector_layer" # Replace with your layer name
layer = QgsProject.instance().mapLayersByName(layer_name)[0]

# Expression to select features
expression = "\"field_name\" = 'some_value'" # Replace with your expression

# Select features
layer.selectByExpression(expression)
```

## QgsProject_extent
*logic: Returns the extent (bounding box) of the entire QGIS project. Use this when the user asks for the overall map extent.
*example:
```python
from qgis.core import QgsProject

# Get the extent of all layers in the project
extent = QgsProject.instance().extent()
print(extent.toString())
```

## processing_run_selectbylocation
*logic: Selects features from a layer that have a spatial relationship (intersect, contain, overlap) with features from another layer or a geometry.
*example:
```python
import processing

# Parameters for select by location
params = {
    'INPUT': 'my_input_layer', # or layer object
    'PREDICATE': [0],  # 0 for intersect
    'INTERSECT': 'my_intersect_layer', # or layer object
    'METHOD': 0 # 0 for creating new selection
}

# Run the algorithm
processing.run("native:selectbylocation", params)
```

## processing_run_joinattributestable
*logic: Joins attributes from a secondary layer to a primary layer based on a matching field value.
*example:
```python
import processing

# Parameters for join attributes by table
params = {
    'INPUT': 'my_input_layer',
    'FIELD': 'join_field_input',
    'INPUT_2': 'my_join_layer',
    'FIELD_2': 'join_field_join',
    'PREFIX': 'joined_',
    'OUTPUT': 'memory:'
}

# Run the algorithm
result = processing.run("native:joinattributestable", params)
joined_layer = result['OUTPUT']
```

## processing_run_native_buffer
*logic: Creates a buffer zone around all features in a layer. This creates a polygon layer with buffered geometries.
*example:
```python
import processing

# Parameters for buffer
params = {
    'INPUT': 'my_layer',
    'DISTANCE': 100, # in layer units
    'SEGMENTS': 5,
    'END_CAP_STYLE': 0, # Round
    'JOIN_STYLE': 0, # Round
    'MITER_LIMIT': 2,
    'DISSOLVE': False,
    'OUTPUT': 'memory:'
}

# Run the algorithm
result = processing.run("native:buffer", params)
buffered_layer = result['OUTPUT']
```

## QgsVectorLayer_createMemoryLayer
*logic: Creates a temporary memory layer (e.g., a bounding box polygon) from a specified extent.
*example:
```python
from qgis.core import QgsVectorLayer, QgsProject, QgsRectangle, QgsGeometry

# Define an extent
extent_rect = QgsRectangle(-180, -90, 180, 90)
geom = QgsGeometry.fromWkt(extent_rect.toWkt())

# Create a memory layer
vl = QgsVectorLayer("Polygon", "temporary_layer", "memory")
pr = vl.dataProvider()
feat = QgsFeature()
feat.setGeometry(geom)
pr.addFeatures([feat])
vl.updateExtents()
QgsProject.instance().addMapLayer(vl)
```

## QgsApplication_processingRegistry_algorithms
*logic: Searches for geoprocessing algorithms by keywords.
*example:
```python
from qgis.core import QgsApplication

# Search for algorithms with "buffer" in their name
for alg in QgsApplication.processingRegistry().algorithms():
    if "buffer" in alg.displayName().lower():
        print(f"{alg.displayName()}: {alg.id()}")
```

## processing_algorithmHelp
*logic: Returns the help description and parameter requirements for a specific QGIS algorithm ID.
*example:
```python
import processing

# Get help for the buffer algorithm
help_output = processing.algorithmHelp("native:buffer")
print(help_output)
```

## processing_run
*logic: Executes a specified QGIS geoprocessing algorithm with a dictionary of parameters.
*example:
```python
import processing

# Parameters for buffer algorithm
params = {
    'INPUT': 'my_layer',
    'DISTANCE': 100,
    'OUTPUT': 'memory:'
}

# Run the algorithm
result = processing.run("native:buffer", params)
output_layer = result['OUTPUT']
```

## QgsVectorLayer_setSingleSymbolRenderer
*logic: Changes the color of a vector layer to a single specified color. Use this to change layer appearance.
*example:
```python
from qgis.core import QgsProject, QgsSingleSymbolRenderer
from qgis.PyQt.QtGui import QColor

layer_name = "my_vector_layer" # Replace with your layer name
layer = QgsProject.instance().mapLayersByName(layer_name)[0]
symbol = layer.renderer().symbol()

# Change color
symbol.setColor(QColor("red"))

# Refresh layer
layer.triggerRepaint()
```

## QgsVectorLayer_crs
*logic: Returns the Coordinate Reference System (CRS) of a layer.
*example:
```python
from qgis.core import QgsProject

layer_name = "my_vector_layer" # Replace with your layer name
layer = QgsProject.instance().mapLayersByName(layer_name)[0]

# Get CRS
crs = layer.crs()
print(f"CRS: {crs.authid()}")
```

## processing_run_reprojectlayer
*logic: Reprojects a layer to a new Coordinate Reference System (CRS).
*example:
```python
import processing

# Parameters for reprojecting a layer
params = {
    'INPUT': 'my_layer',
    'TARGET_CRS': 'EPSG:3857',
    'OUTPUT': 'memory:'
}

# Run the algorithm
result = processing.run("native:reprojectlayer", params)
reprojected_layer = result['OUTPUT']
```