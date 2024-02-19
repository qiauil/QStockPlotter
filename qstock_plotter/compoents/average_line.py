import numpy as np
from typing import Union
from PyQt6.QtGui import QContextMenuEvent,QColor,QIcon
from PyQt6.QtCore import Qt,pyqtSignal
from PyQt6.QtWidgets import QWidget
from qfluentwidgets import CommandBar,FluentIcon,Action,FluentIconBase,qconfig,RoundMenu
from qfluentwidgets.common.overload import singledispatchmethod
import pyqtgraph as pg
from pyqtgraph import PlotCurveItem
from ..widgets.q_plot_widget import QPlotWidget
from ..widgets.colorful_toggle_button import ColorfulToggleButton
from ..widgets.value_select_box import NewAverageLineBox

class AverageLineItem(PlotCurveItem):
    """
    A class representing an average line item on a plot.

    Attributes:
        num_average_data (int): The number of data points to use for calculating the average.
    """

    def __init__(self, data, num_average_data:int, color:QColor, line_width: float):
        """
        Initializes an AverageLineItem object.

        Args:
            data (array-like): The data points for which the average line is calculated.
            num_average_data (int): The number of data points to use for calculating the average.
            color (str): The color of the average line.
            line_width (float): The width of the average line.
        """
        super().__init__(pen=pg.mkPen(color, width=line_width),
                         clickable=False,
                         x=np.arange(num_average_data-1, len(data)),
                         y=np.asarray([np.mean(data[i:i+num_average_data]) for i in range(len(data)-num_average_data+1)]))
        self.num_average_data = num_average_data

    def get_local_plot_range(self, start: float, end: float):
        """
        Returns the minimum and maximum values of the average line within the specified range.

        Args:
            start (float): The start value of the range.
            end (float): The end value of the range.

        Returns:
            tuple: A tuple containing the minimum and maximum values of the average line within the range.
                   If there are no data points within the range, returns None.
        """
        _, ys = self.getData()
        ys = ys[max(0, int(start-self.num_average_data)):max(0, int(end-self.num_average_data))]
        if len(ys) > 0:
            return np.min(ys), np.max(ys)
        else:
            return None

class AverageLineButton(ColorfulToggleButton):
    """
    A button widget that represents an average line.

    This button provides functionality for removing the average line and displays a context menu when right-clicked.

    Signals:
        - sigRemoveClicked: Emitted when the remove action is triggered.

    Args:
        parent (QWidget): The parent widget.

    Overloaded Methods:
        - __init__(self, parent: QWidget = None)
        - __init__(self, color: QColor, text: str, parent: QWidget = None, icon: Union[QIcon, FluentIconBase, str] = None)
        - __init__(self, icon: QIcon, color: QColor, text: str, parent: QWidget = None)
        - __init__(self, icon: FluentIconBase, color: QColor, text: str, parent: QWidget = None)
    """

    sigRemoveClicked = pyqtSignal()

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.color = None
        qconfig.themeChangedFinished.connect(self.set_color)
        self.context_menu = RoundMenu("Context Menu")
        self.remove_action = Action("Remove")
        self.remove_action.setIcon(FluentIcon.DELETE)
        self.remove_action.triggered.connect(self.sigRemoveClicked.emit)
        self.context_menu.addAction(self.remove_action)

    @__init__.register
    def _(self, color: QColor, text: str, parent: QWidget = None, icon: Union[QIcon, FluentIconBase, str] = None):
        self.__init__(parent)
        self.setText(text)
        self.setIcon(icon)
        self.color = color
        self.set_color()

    @__init__.register
    def _(self, icon: QIcon, color: QColor, text: str, parent: QWidget = None):
        self.__init__(color, text, parent, icon)

    @__init__.register
    def _(self, icon: FluentIconBase, color: QColor, text: str, parent: QWidget = None):
        self.__init__(color, text, parent, icon)

    def contextMenuEvent(self, a0: QContextMenuEvent) -> None:
        self.context_menu.exec(a0.globalPos())

class AverageLineComponent():
    """
    A component that handles the addition and removal of average lines on a plot.
    """
    
    def __init__(self, plot_widget: QPlotWidget, parent=None) -> None:
        """
        Initializes the AverageLineComponent object.

        Parameters:
        - plot_widget (QPlotWidget): The plot widget where the average lines are added.
        - parent: The parent object of the component.
        """
        self.parent = parent
        self.plot_widget = plot_widget
        self.plot_items_bar = CommandBar(parent=self.parent)
        self.plot_items_bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.plot_items_bar.setFixedHeight(25)
        self.add_line_action = Action("Add average line")
        self.add_line_action.setIcon(FluentIcon.ADD)
        self.add_line_action.triggered.connect(self.__on_add_line_action_clicked)
        self.plot_items_bar.addAction(self.add_line_action)

        self.average_lines = {}
        
    def __on_add_line_action_clicked(self):
        """
        Handles the event when the add line action is clicked.
        Shows a dialog box for selecting the number of data points and color for the average line.
        Adds the average line to the plot.
        """
        msg = NewAverageLineBox(num_data=len(self.parent.main_item.get_feature_value()), existed_values=self.average_lines.keys(), parent=self.parent)
        if msg.exec():
            self.add_average_line(int(msg.value_edit.text()), msg.color_selector.current_item)
            
    def get_widget(self):
        """
        Returns the plot_items_bar widget.

        Returns:
        - QWidget: The plot_items_bar widget.
        """
        return self.plot_items_bar
    
    def add_average_line(self, num_average_data, color):
        """
        Adds an average line to the plot.

        Parameters:
        - num_average_data (int): The number of data points to calculate the average.
        - color: The color of the average line.
        """
        if hasattr(self.parent, "main_item") == False:
            raise ValueError("The parent plotter has no main item")
        if self.parent.main_item is None:
            raise ValueError("The main item of the parent plotter is None")
        data = self.parent.main_item.get_feature_value()
        style = self.parent.main_item.style
        average_line = AverageLineItem(data, num_average_data, color, style.line_width)
        self.average_lines[num_average_data] = average_line
        self.plot_widget.add_item(average_line)
        toggle_button = AverageLineButton(color=color, parent=self.plot_items_bar, text="MA{}".format(num_average_data))
        toggle_button.setFixedHeight(25)
        toggle_button.setChecked(True)
        def on_toggle_button_clicked():
            if toggle_button.isChecked():
                self.plot_widget.add_item(average_line)
                self.average_lines[num_average_data] = average_line
            else:
                self.plot_widget.remove_item(average_line)
                self.average_lines.pop(num_average_data)
        def on_remove_button_clicked():
            self.plot_widget.remove_item(average_line)
            self.average_lines.pop(num_average_data)
            self.plot_items_bar.removeWidget(toggle_button)
            toggle_button.deleteLater()
        toggle_button.clicked.connect(on_toggle_button_clicked)
        toggle_button.sigRemoveClicked.connect(on_remove_button_clicked)
        self.plot_items_bar._insertWidgetToLayout(len(self.plot_items_bar._widgets)-1, toggle_button)
    
    def add_default_average_lines(self):
        """
        Adds the default average lines based on the style of the main item.
        """
        style = self.parent.main_item.style
        for num_average_data in style.average_line_color.keys():
            self.add_average_line(num_average_data, style.average_line_color[num_average_data])
    