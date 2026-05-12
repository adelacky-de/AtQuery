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
        # Accept anything for now so we can see what QGIS is sending
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        mime = event.mimeData()
        dropped_text = ""
        
        if mime.hasText():
            dropped_text = mime.text()
        elif mime.hasUrls():
            # If it's a file path (like a .shp dragged from folder)
            dropped_text = mime.urls()[0].toLocalFile()
        
        if dropped_text:
            # If it's a full path, just take the base name
            if os.path.exists(dropped_text):
                dropped_text = os.path.basename(dropped_text).split('.')[0]
            
            self.insert(dropped_text)
            self.setFocus()
            event.acceptProposedAction()
        else:
            # Fallback for QGIS internal items if plain text is missing
            from qgis.utils import iface
            layer = iface.activeLayer()
            if layer:
                self.insert(layer.name())
                self.setFocus()
                event.acceptProposedAction()
            else:
                event.ignore()
