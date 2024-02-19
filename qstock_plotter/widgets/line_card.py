
from typing import Union
from PyQt6.QtGui import QAction, QMouseEvent, QPainter, QPixmap, QPen, QResizeEvent,QColor
from PyQt6.QtCore import Qt,pyqtSignal
from PyQt6.QtWidgets import QLabel,QListWidget
from qfluentwidgets import RoundMenu,CheckableMenu,TableWidget,Action,qconfig,isDarkTheme,MenuIndicatorType,FluentIcon
from qfluentwidgets.common.icon import toQIcon

class LineCard(QLabel):
    """
    A custom QLabel widget that displays a horizontal line.

    Args:
        line_color (Qt.GlobalColor): The color of the line. Defaults to Qt.GlobalColor.black.
        line_width (int): The width of the line. Defaults to 2.
        dash_type (list): The dash pattern of the line. Defaults to [3, 10, 1, 10, 1, 10].
        width (int): The width of the widget. Defaults to 200.
        height (int): The height of the widget. Defaults to 10.
        parent (QWidget): The parent widget. Defaults to None.
    """

    def __init__(self, line_color=Qt.GlobalColor.black, line_width=2, dash_type=[3, 10, 1, 10, 1, 10], width=200, height=10, parent=None) -> None:
        self.dash_type = dash_type
        self.line_width = line_width
        self.line_color = line_color
        super().__init__(parent=parent)
        self.resize(width, height)

    def __draw_line(self):
        """
        Internal method to draw the line on the widget.
        """
        canvas = QPixmap(self.width(), self.height())
        canvas.fill(QColor(0, 0, 0, 0))
        painter = QPainter(canvas)
        pen = QPen(self.line_color, self.line_width)
        pen.setDashPattern(self.dash_type)
        painter.setPen(pen)
        painter.drawLine(0, int(self.height() / 2), self.width(), int(self.height() / 2))
        painter.end()
        self.setPixmap(canvas)

    def set_dash_type(self, dash_type):
        """
        Set the dash pattern of the line.

        Args:
            dash_type (list): The dash pattern of the line.
        """
        self.dash_type = dash_type
        self.__draw_line()

    def set_line_width(self, line_width):
        """
        Set the width of the line.

        Args:
            line_width (int): The width of the line.
        """
        self.lineWidth = line_width
        self.__draw_line()

    def set_line_color(self, line_color):
        """
        Set the color of the line.

        Args:
            line_color (Qt.GlobalColor): The color of the line.
        """
        self.line_color = line_color
        self.__draw_line()

    def resizeEvent(self, a0: QResizeEvent) -> None:
        """
        Reimplemented from QLabel.resizeEvent().
        Redraws the line when the widget is resized.

        Args:
            a0 (QResizeEvent): The resize event.
        """
        self.__draw_line()
        return super().resizeEvent(a0)
'''   
class DashTypeAction(Action):
    
    def __init__(self, dash_type, dash_type_name=None, parent=None):
        self.dash_type=dash_type
        self.dash_type_name=dash_type_name
        super().__init__(text="       ", parent=parent)

class DashTypeRoundMenu(RoundMenu):
    
    def __init__(self, title="", line_width=2,line_color=Qt.GlobalColor.black,parent=None):
        self.line_width=line_width
        self.line_color=line_color
        super().__init__(title, parent)
    
    def add_dash_type_action(self, action: DashTypeAction):
        item = self._createActionItem(action)
        self.view.addItem(item)
        line_card=LineCard(line_color=self.line_color,line_width=self.line_width,dash_type=action.dash_type)
        self.view.setItemWidget(item, line_card)
        line_card.sigClicked.connect(lambda:self._onItemClicked(item))
        self.adjustSize()     
    
    def add_dash_type_actions(self, actions: list[DashTypeAction]):
        for action in actions:
            self.add_dash_type_action(action)

class DashTypeCheckableMenu(CheckableMenu):
    
    def __init__(self, title="", parent=None,indicatorType=MenuIndicatorType.RADIO,line_width=2,line_color=Qt.GlobalColor.black):
        self.line_width=line_width
        self.line_color=line_color
        super().__init__(title, parent,indicatorType=MenuIndicatorType.RADIO)
    
    def add_dash_type_action(self, action: DashTypeAction):
        item = self._createActionItem(action)
        item.setIcon(toQIcon(FluentIcon.ADD))
        self.view.addItem(item)
        line_card=LineCard(line_color=self.line_color,line_width=self.line_width,dash_type=action.dash_type)
        self.view.setItemWidget(item, line_card)
        def _onItemClicked():
            action.trigger()
            self._closeParentMenu()
            self.adjustSize()
        line_card.sigClicked.connect(_onItemClicked)
        self.adjustSize()
    
    def add_dash_type_actions(self, actions: list[DashTypeAction]):
        for action in actions:
            self.add_dash_type_action(action)
'''   