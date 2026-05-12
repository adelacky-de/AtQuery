# AtQuery_input.py

from qgis.PyQt import QtWidgets, QtCore, QtGui

class DropLineEdit(QtWidgets.QLineEdit):
    """
    A QLineEdit that accepts Drag & Drop from the QGIS Layer Tree.
    When a layer is dropped, it inserts the layer's name into the text.
    """
    def __init__(self, parent=None):
        super(DropLineEdit, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText("Ask a question (or drag a layer here)...")

    def dragEnterEvent(self, event):
        # Check if the event has text (which QGIS Layer Tree provides)
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            # Get the layer name (or text)
            dropped_text = event.mimeData().text()
            
            # Clean up potential 'file://' or path-like strings if needed, 
            # but usually QGIS drops the layer name into text editors.
            
            # Insert at current cursor position
            self.insert(dropped_text)
            self.setFocus()
            event.accept()
        else:
            event.ignore()
