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
        # Explicitly accept CopyAction to prevent QGIS from 'moving' the layer out of the tree
        if event.mimeData().hasText() or event.mimeData().hasUrls():
            event.accept(QtCore.Qt.CopyAction)
        else:
            event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText() or event.mimeData().hasUrls():
            event.accept(QtCore.Qt.CopyAction)
        else:
            event.accept()

    def dropEvent(self, event):
        mime = event.mimeData()
        dropped_text = ""
        
        if mime.hasText():
            dropped_text = mime.text()
        elif mime.hasUrls():
            dropped_text = mime.urls()[0].toLocalFile()
        
        if dropped_text:
            if os.path.exists(dropped_text):
                dropped_text = os.path.basename(dropped_text).split('.')[0]
            
            # Manually insert the text
            self.insert(dropped_text)
            self.setFocus()
            
            # CRITICAL: We IGNORE the event. 
            # This makes the source (QGIS) think the drop was REJECTED.
            # Thus, QGIS will NOT delete the layer from the legend.
            event.ignore()
        else:
            from qgis.utils import iface
            layer = iface.activeLayer()
            if layer:
                self.insert(layer.name())
                self.setFocus()
                event.ignore()
            else:
                event.ignore()
