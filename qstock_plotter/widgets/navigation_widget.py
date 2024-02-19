# coding:utf-8
# Modify from pyqt6-fluent-widgets
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
from qfluentwidgets import (Pivot, qrouter, SegmentedWidget)
from ..libs.style import StyleSheet
 
class PivotInterface(QWidget):
    """ Pivot interface """

    Nav = Pivot

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        StyleSheet.NAVIGATION_VIEW_INTERFACE.apply(self)
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
    
    def set_current_item(self, widget):
        self.stackedWidget.setCurrentWidget(widget)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.setDefaultRouteKey(self.stackedWidget, widget.objectName())

    def addSubInterface(self, widget, objectName, text):
        widget.setObjectName(objectName)
        #widget.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )
        if len(self.pivot.items) == 1:
            self.set_current_item(widget)

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())


class SegmentedInterface(PivotInterface):

    Nav = SegmentedWidget

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout.removeWidget(self.pivot)
        self.vBoxLayout.insertWidget(0, self.pivot)
