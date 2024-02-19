from PyQt6.QtWidgets import QWidget
from pyqtgraph import SignalProxy
from ..widgets.q_plot_widget import QPlotWidget
from ..widgets.zoom_bar import ZoomBar
from ..widgets.fluent_scroller import HorizontalFluentScroller, VerticalFluentScroller
from ..libs.constant import ZOOM_MODEL,YLOC_MODEL

class StockWidgetZoomBar(ZoomBar):
    """
    A custom zoom bar widget for the stock plot widget.

    Args:
        plot_widget (QPlotWidget): The parent plot widget.
        parent (QWidget): The parent widget.

    Attributes:
        plot_widget (QPlotWidget): The parent plot widget.
        current_value (float): The current value of the plot widget's view rectangle width.
    """

    def __init__(self, plot_widget: QPlotWidget, parent=None) -> None:
        super().__init__(parent=parent, use_opacity_effect=True)
        self.plot_widget = plot_widget
        self.current_value = plot_widget.viewRect().width()

        def update_position():
            self.setGeometry(self.plot_widget.geometry().width() - 300 - 20, self.plot_widget.geometry().y() + 10, 300, 40)

        update_position()
        self.plot_widget.sigSizeChanged.connect(update_position)

        def update_boundings():
            self.current_value = self.plot_widget.viewRect().width()
            self.update_min_max_value(min_v=self.plot_widget.x_range_min, max_v=self.plot_widget.x_range_max)

        update_boundings()
        self.plot_widget.sigBoundingUpdated.connect(update_boundings)

        def update_widget():
            self.update_widget(value=self.plot_widget.viewRect().width())

        update_widget()
        self.plotter_view_changed_slot = SignalProxy(self.plot_widget.sigRangeChanged, rateLimit=50, slot=update_widget)

    def apply_value_func(self, value):
        """
        Apply the given value to the plot widget's x range.

        Args:
            value (float): The value to be applied.

        Returns:
            None

        """
        # x_loc = (self.plot_widget.viewRect().right()+self.plot_widget.viewRect().left())/2-value/2
        self.plot_widget.update_plot(x_range=value)

class StockWidgetHorizontalScroller(HorizontalFluentScroller):
    """
    A custom horizontal scroller widget for controlling the movement of a plot widget.
    
    Args:
        plot_widget (QPlotWidget): The plot widget to be controlled.
        parent: The parent widget.
    """
    
    def __init__(self, plot_widget: QPlotWidget, parent: None) -> None:
        super().__init__(parent)
        self.plot_widget=plot_widget
        self.move_unit_ratio=0.02
        self.move_unit_min=1
        self.move_from_update=False
        self.update_location()
        self.plot_widget.sigBoundingUpdated.connect(self.update_location)
        self.plotter_view_changed_slot = SignalProxy(self.plot_widget.sigRangeChanged, rateLimit=50, slot=self.update_location)
        self.valueChanged.connect(self.on_value_changed)
        
    def update_location(self):
        """
        Update the location and range of the scroller based on the plot widget's view.
        """
        self.move_unit=max(self.plot_widget.viewRect().width()*self.move_unit_ratio,self.move_unit_min)
        self.setRange(0,int((self.plot_widget.x_end - self.plot_widget.x_start - self.plot_widget.viewRect().width()) / self.move_unit))
        self.move_from_update=True
        self.setValue(int((self.plot_widget.viewRect().left() - self.plot_widget.x_start) / self.move_unit))
        self.move_from_update=False

    def on_value_changed(self): 
        """
        Handle the value changed signal of the scroller and update the plot widget's plot accordingly.
        """
        if not self.move_from_update:
            self.plot_widget.update_plot(x_loc=self.value()*self.move_unit+self.plot_widget.x_start)

class StockWidgetVerticalScroller(VerticalFluentScroller):
    """
    A custom vertical scroller widget for controlling the y-axis movement of a plot widget.
    
    Args:
        plot_widget (QPlotWidget): The plot widget to control.
        parent (None): The parent widget.
    """
    
    def __init__(self, plot_widget: QPlotWidget, parent: None) -> None:
        super().__init__(parent)
        self.plot_widget=plot_widget
        self.move_unit_ratio=0.02
        self.move_unit_min=1
        self.move_from_update=False
        self.update_location()
        self.on_zoom_loc_model_changed()
        self.plot_widget.sigZoomModelChanged.connect(self.on_zoom_loc_model_changed)
        self.plot_widget.sigYLocModelChanged.connect(self.on_zoom_loc_model_changed)
        self.plot_widget.sigBoundingUpdated.connect(self.update_location)
        self.plotter_view_changed_slot = SignalProxy(self.plot_widget.sigRangeChanged, rateLimit=50, slot=self.update_location)
        self.valueChanged.connect(self.on_value_changed)
        
    def update_location(self):
        """
        Update the location and range of the scroller based on the plot widget's current state.
        """
        self.move_unit=max(self.plot_widget.viewRect().height()*self.move_unit_ratio,self.move_unit_min)
        maximum_y=int((self.plot_widget.y_end - self.plot_widget.y_start - self.plot_widget.viewRect().height()) / self.move_unit)
        self.setRange(0,maximum_y)
        self.move_from_update=True
        self.setValue(maximum_y-int((self.plot_widget.viewRect().top() - self.plot_widget.y_start) / self.move_unit))
        self.move_from_update=False

    def on_value_changed(self): 
        """
        Handle the value changed signal of the scroller and update the plot widget's y-axis location accordingly.
        """
        if not self.move_from_update:
            self.plot_widget.move_y_loc((self.maximum() - self.value()) * self.move_unit + self.plot_widget.y_start)
    
    def on_zoom_loc_model_changed(self):
        """
        Handle the zoom and y-axis location model changed signals of the plot widget and enable/disable the scroller accordingly.
        """
        if self.plot_widget.zoom_model != ZOOM_MODEL.AUTO_RANGE and self.plot_widget.y_loc_model == YLOC_MODEL.FREE:
            self.setEnabled(True)
        else:
            self.setEnabled(False)
    