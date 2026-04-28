# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
# NOTE: Removed 'from .resources import *' since we are loading the icon directly
from .ui.AtQuery_dockwidget import AtQueryDockWidget

class AtQuery:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr(u'&AtQuery')
        self.toolbar = self.iface.addToolBar(u'AtQuery')
        self.toolbar.setObjectName(u'AtQuery')
        self.dockwidget = None
        self.first_start = True

    def tr(self, message):
        return QCoreApplication.translate('AtQuery', message)

    def initGui(self):
        # FIX: Loading icon with correct .jpg extension directly from the plugin folder.
        icon_path = os.path.join(self.plugin_dir, 'Icon_AtQuery.jpg') 
        
        self.action = QAction(QIcon(icon_path), self.tr(u'AI Chat for QGIS'), self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.menu, self.action)
        self.actions.append(self.action)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&AtQuery'), action)
            self.iface.removeToolBarIcon(action)
        
        if self.toolbar:
            self.iface.mainWindow().removeToolBar(self.toolbar)
        
        if self.dockwidget:
            try:
                self.dockwidget.closingPlugin.disconnect(self.unload)
            except TypeError:
                pass
            self.iface.removeDockWidget(self.dockwidget)
            self.dockwidget = None

    def run(self):
        if self.first_start:
            self.dockwidget = AtQueryDockWidget()
            
            # CRITICAL FIX: Pass the interface to the dock widget
            self.dockwidget.set_iface(self.iface) 
            
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.closingPlugin.connect(self.unload)
            self.first_start = False
            
        self.dockwidget.show()