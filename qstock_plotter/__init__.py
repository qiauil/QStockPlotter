from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy
from qfluentwidgets import TransparentToggleToolButton, FluentIcon, isDarkTheme
from .widgets.q_plot_widget import QPlotWidget
from .widgets.navigation_widget import PivotInterface, SegmentedInterface
from .compoents.zoom_move import (
    StockWidgetZoomBar,
    StockWidgetHorizontalScroller,
    StockWidgetVerticalScroller,
)
from .compoents.draw_line import DrawLineComponent
from .compoents.frame_recorder import FrameRecorderComponent
from .compoents.average_line import AverageLineComponent
from .libs.plot_item import *
from .libs.style import QStockIcon, set_background_with_theme
from .libs.data_handler import PricesDataFrame, VolumeDataFrame

from typing import Optional


class QStockPlotter(QWidget):

    def __init__(self, show_zoom_bar=True, parent=None) -> None:
        super().__init__(parent)

        self.main_item = None

        self.setMinimumSize(450, 200)
        self.main_plotter = QPlotWidget(self)

        self.y_scroller = StockWidgetVerticalScroller(self.main_plotter, parent=self)
        self.x_scroller = StockWidgetHorizontalScroller(self.main_plotter, parent=self)
        if show_zoom_bar:
            self.zoom_bar = StockWidgetZoomBar(self.main_plotter, parent=self)

        self.draw_line_component = DrawLineComponent(self.main_plotter, parent=self)
        self.draw_line_command_bar, self.draw_line_table = (
            self.draw_line_component.get_widget()
        )
        self.draw_line_table.show()

        self.frame_recorder_component = FrameRecorderComponent(
            self.main_plotter, parent=self
        )
        self.saved_frame_table = self.frame_recorder_component.get_widget()
        self.saved_frame_table.show()

        self.average_line_component = AverageLineComponent(
            self.main_plotter, parent=self
        )
        self.average_line_command_bar = self.average_line_component.get_widget()

        #self.navigation_widget = PivotInterface(parent=self)
        self.navigation_widget = SegmentedInterface(parent=self)
        self.navigation_widget.addSubInterface(
            self.draw_line_table, "saved_line_table", "Lines"
        )
        self.navigation_widget.addSubInterface(
            self.saved_frame_table, "saved_frame_table", "Frames"
        )
        self.navigation_widget.hide()
        self.show_up_button = TransparentToggleToolButton(QStockIcon.CHEVRON_LEFT)
        self.show_up_button.setFixedWidth(10)
        self.show_up_button.clicked.connect(self.__on_show_up_button_clicked)

        self.main_plotter.insert_context_menu(
            self.frame_recorder_component.jump_to_menu
        )
        self.main_plotter.insert_context_menu(
            self.frame_recorder_component.record_current_frame_action
        )
        self.main_plotter.insert_context_menu(self.draw_line_component.menu_action)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)
        self.inner_layout = QVBoxLayout()
        self.inner_layout.setContentsMargins(0, 0, 0, 0)
        self.inner_layout.setSpacing(0)
        self.plotter_grid_layout = QGridLayout()
        self.plotter_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.plotter_grid_layout.setSpacing(0)

        self.main_layout.addLayout(self.inner_layout)
        self.main_layout.addWidget(self.show_up_button)
        self.main_layout.addWidget(self.navigation_widget)
        self.inner_layout.addWidget(self.draw_line_command_bar)
        self.inner_layout.addLayout(self.plotter_grid_layout)
        self.inner_layout.addWidget(self.average_line_command_bar)
        self.plotter_grid_layout.addWidget(self.main_plotter, 0, 0, 1, 1)
        self.plotter_grid_layout.addWidget(self.y_scroller, 0, 1, 1, 1)
        self.plotter_grid_layout.addWidget(self.x_scroller, 1, 0, 1, 2)

        for m in ['update_plot', 
                  "move_y_loc", 
                  "set_zoom_model", 
                  "set_y_loc_model", 
                  "set_full_range_enabled",
                  "set_x_range",
                  "move_to_end",
                  "move_to_start",]:
            setattr(self, m, getattr(self.main_plotter, m))

        set_background_with_theme(self)

        qconfig.themeChanged.connect(lambda theme: set_background_with_theme(self, theme))

    def add_main_item(self, plot_item, x_ticks=None, y_ticks=None):
        if self.main_item is not None:
            raise Exception(
                "Main item already exists. There can only be one main item."
            )
        self.main_item = plot_item
        self.main_plotter.add_item(plot_item, x_ticks, y_ticks)
        self.average_line_component.add_default_average_lines()

    def remove_main_item(self):
        if self.main_item is None:
            raise Exception("No main item exists.")
        self.main_plotter.remove_item(self.main_item)
        self.main_item = None

    def __on_show_up_button_clicked(self):
        if self.navigation_widget.isHidden():
            self.navigation_widget.show()
            self.show_up_button.setIcon(FluentIcon.CHEVRON_RIGHT)
        else:
            self.navigation_widget.hide()
            self.show_up_button.setIcon(QStockIcon.CHEVRON_LEFT)

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.navigation_widget.setFixedWidth(min(int(self.width() * 0.3), 350))
        return super().resizeEvent(a0)

    def update_plot(self, x_loc:Optional[float]=None, x_range:Optional[float]=None):
        self.main_plotter.update_plot(x_loc, x_range)

class PriceVolumePlotter(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(8)
        self.setLayout(self.main_layout)

        self.price_plotter = QStockPlotter(show_zoom_bar=True)
        self.volume_plotter = QStockPlotter(show_zoom_bar=True)

        self.price_plotter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.volume_plotter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_layout.addWidget(self.price_plotter,stretch=3)
        self.main_layout.addWidget(self.volume_plotter,stretch=1)

        self.price_plotter.main_plotter.sigViewChanged.connect(
            lambda: self.__on_view_changed(self.price_plotter.main_plotter)
        )
        self.volume_plotter.main_plotter.sigViewChanged.connect(
            lambda: self.__on_view_changed(self.volume_plotter.main_plotter)
        )

        set_background_with_theme(self)

        qconfig.themeChanged.connect(lambda theme: set_background_with_theme(self, theme))

    def __on_view_changed(self, active_plot_widget):
        if active_plot_widget == self.price_plotter.main_plotter:
            self.volume_plotter.update_plot(
                x_loc=active_plot_widget.viewRect().left(),
                x_range=active_plot_widget.viewRect().width(),
            )
        else:
            self.price_plotter.update_plot(
                x_loc=active_plot_widget.viewRect().left(),
                x_range=active_plot_widget.viewRect().width(),
            )

    def plot_price_volume(
        self, price_data: PricesDataFrame, 
        volume_data: VolumeDataFrame
    ):
        price_item = get_plot_item(price_data)
        self.price_plotter.add_main_item(price_item, x_ticks=price_item.get_x_ticks())
        volume_item=get_plot_item(volume_data)
        self.volume_plotter.add_main_item(volume_item, x_ticks=volume_item.get_x_ticks())

    def plot_trade_data(self, trade_data: TradeData):
        self.plot_price_volume(trade_data.prices, trade_data.volume)

    def update_plot(self, x_loc:Optional[float]=None, x_range:Optional[float]=None):
        self.price_plotter.update_plot(x_loc, x_range)

    def set_x_range(self, x_loc:Optional[float]=None, x_range:Optional[float]=None):
        self.price_plotter.set_x_range(x_loc, x_range)
        self.volume_plotter.set_x_range(x_loc, x_range)

    def move_to_end(self):
        self.price_plotter.move_to_end()
    
    def move_to_start(self):
        self.price_plotter.move_to_start()