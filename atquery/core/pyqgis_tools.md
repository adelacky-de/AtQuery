# PyQGIS Developer Cookbook: Comprehensive Reference

This document provides a technical overview of the most essential **PyQGIS** functions organized by their application area, as detailed in the **[QGIS 3.40 Developer Cookbook](https://docs.qgis.org/3.40/en/docs/pyqgis_developer_cookbook/index.html)**.

---

## 1. Project & Layer Management

## QgsProject.instance().read("path")
*logic: Loads a QGIS project file (`.qgs` or `.qgz`) from the specified file path into the current application instance.

## QgsProject.instance().write("path")
*logic: Saves the current project state to a file. Useful for automated project generation or backup.

## QgsProject.instance().mapLayers()
*logic: Returns a dictionary of all layers in the project. Keys are unique layer IDs; values are `QgsMapLayer` objects.

## QgsProject.instance().mapLayersByName("name")
*logic: Retrieves a list of layers that match a specific display name. Useful for finding layers when IDs are unknown.

## QgsProject.instance().addMapLayer(layer)
*logic: Formally adds a layer object to the project's Table of Contents (TOC), making it visible in the layer tree.

---

## 2. Vector Layer Operations

## layer.fields()
*logic: Retrieves the attribute schema of a vector layer. Used to inspect column names, types (String, Int, etc.), and lengths.

## layer.getFeatures(request)
*logic: Returns an iterator over the features in the layer. Can be filtered using a `QgsFeatureRequest` to optimize performance.

## layer.selectByExpression("expression")
*logic: Selects features that match a standard QGIS expression string (e.g., `"Type" = 'Industrial'`).

## layer.selectedFeatures()
*logic: Returns a list of all features currently highlighted by the user or an automated selection process.

## layer.dataProvider().addFeatures([list])
*logic: Directly inserts new feature objects into the layer's underlying data source.

## layer.dataProvider().deleteFeatures([ids])
*logic: Permanently removes features from the data source using their unique IDs (FIDs).

---

## 3. Raster Layer Operations

## layer.width() / layer.height()
*logic: Returns the dimensions of the raster in pixels (number of columns and rows).

## layer.dataProvider().identify(point, mode)
*logic: Retrieves the pixel value(s) at a specific geographical coordinate. Used for "Value at Point" queries.

---

## 4. Geometry & Projections

## QgsGeometry.fromWkt("wkt_string")
*logic: Creates a geometry object from a "Well-Known Text" string (e.g., `POINT(0 0)` or `POLYGON(...)`).

## geom.area() / geom.length()
*logic: Calculates the planar area or length of a geometry in the units of its Coordinate Reference System.

## geom.intersects(other_geom)
*logic: A spatial predicate that returns `True` if two geometries share any part of their space.

## QgsCoordinateReferenceSystem("EPSG:4326")
*logic: Initializes a CRS object used for coordinate transformations and spatial lookups.

---

## 5. Map Canvas & UI

## iface.mapCanvas().setExtent(rect)
*logic: Changes the visible boundaries of the map window to match the provided `QgsRectangle`.

## iface.messageBar().pushMessage("title", "text", level)
*logic: Displays a non-blocking notification banner at the top of the QGIS interface.

---

## 6. Processing & Expressions

## QgsApplication.processingRegistry().algorithms()
*logic: Searches for available geoprocessing algorithms. Use keywords like "slope", "centroid", or "intersection" to find the correct algorithm ID.

## processing.algorithmHelp(algorithm_id)
*logic: Retrieves the parameter requirements and description for a specific algorithm. Essential for understanding how to construct a `processing.run()` call correctly.

## processing.run(algorithm_id, parameters)
*logic: Executes a geoprocessing algorithm with a dictionary of inputs. The most powerful tool for multi-step GIS workflows.

---

## 7. Application Settings

## QgsSettings().value("key", "default")
*logic: Retrieves a user setting from the QGIS global registry or project-specific settings.

## QgsSettings().setValue("key", value)
*logic: Persistently stores a configuration value, ensuring it remains available after the application restarts.

---
© 2026 AdelaC
