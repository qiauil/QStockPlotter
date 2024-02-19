from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsOpacityEffect,QHBoxLayout
from PyQt6.QtCore import QPropertyAnimation,Qt
from qfluentwidgets import SimpleCardWidget,ToolButton,Slider,FluentIcon
import math
from ..libs.helpers import limit_in_range

class ZoomBar(SimpleCardWidget):
    
    def __init__(self,parent=None,use_opacity_effect=True) -> None:
        super().__init__(parent=parent)
        self.zoom_slider = Slider(orientation=Qt.Orientation.Horizontal,parent=self)
        self.zoom_slider.setMinimum(0)
        self.zoom_slider.setMaximum(100)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.__on_zoom_slider_moved)
        self.zoom_in_button = ToolButton(FluentIcon.ZOOM_IN,parent=self)
        self.zoom_in_button.clicked.connect(self.__on_zoom_in_button_clicked)
        self.zoom_out_button = ToolButton(FluentIcon.ZOOM_OUT,parent=self)
        self.zoom_out_button.clicked.connect(self.__on_zoom_out_button_clicked)
        self.zoom_tool_layout=QHBoxLayout(self)
        self.zoom_tool_layout.setContentsMargins(5,5, 5, 5)
        self.zoom_tool_layout.setSpacing(5)
        self.zoom_tool_layout.addWidget(self.zoom_out_button)
        self.zoom_tool_layout.addWidget(self.zoom_slider)
        self.zoom_tool_layout.addWidget(self.zoom_in_button)
        if use_opacity_effect:
            self.opacity_effect = QGraphicsOpacityEffect(self)
            self.opacity_ani = QPropertyAnimation(self.opacity_effect, b'opacity', self)
            self.opacity_effect.setOpacity(0.1)
            self.setGraphicsEffect(self.opacity_effect)
        self.value_min=0
        self.value_max=100
        self.current_value=100
        self.move_from_update=False
        self.zoom_coef=10 # a constant to control the zoom speed. Do NOT change it.
        self.e_constant=math.exp(self.zoom_coef) # a constant to control the zoom speed
        self.__init_config_variable()
        self.update_widget()
        
    def __init_config_variable(self):
        self.zoom_out_factor=1.1
        self.zoom_in_factor=0.9
        

    def enterEvent(self, e):
        if hasattr(self,"opacity_ani"):
            self.opacity_ani.setEndValue(0.8)
            self.opacity_ani.setDuration(150)
            self.opacity_ani.start()
        return super().enterEvent(e)
    
    def leaveEvent(self, e):
        if hasattr(self,"opacity_ani"):
            self.opacity_ani.setEndValue(0.1)
            self.opacity_ani.setDuration(150)
            self.opacity_ani.start()
        return super().leaveEvent(e)

    def __on_zoom_slider_moved(self):
        """
        Callback function for when the zoom slider is moved.
        Adjusts the x range and updates the plot, zoom slider, and scrollbars accordingly.
        """
        if not self.move_from_update:
            z_value=(100-self.zoom_slider.value())/self.zoom_coef
            value=(math.exp(z_value)-1)*(self.value_max-self.value_min)/(self.e_constant-1)+self.value_min
            self.update_widget(value)
            self.apply_value_func(value)

    def __on_zoom_out_button_clicked(self):
        """
        Handles the click event of the zoom out button.
        Zooms out the x-axis range by a factor of zoom_out_factor, updates the plot,
        and updates the zoom slider, x scroller, y scroller, and zoom buttons.
        """
        value = self.current_value*self.zoom_out_factor
        if value >= self.value_max:
            value=self.value_max
        self.update_widget(value)
        self.apply_value_func(value)

    def __on_zoom_in_button_clicked(self):
        """
        Handles the click event of the zoom in button.
        Zooms in the x-axis range by a factor of zoom_in_factor, updates the plot,
        and updates the zoom slider, x scroller, y scroller, and zoom buttons.
        """
        value = self.current_value*self.zoom_in_factor
        if value <= self.value_min:
            value=self.value_min
        self.update_widget(value)
        self.apply_value_func(value)

    def update_min_max_value(self,min_v=None,max_v=None):
        if min_v is not None:
            self.value_min=min_v
        if max_v is not None:
            self.value_max=max_v
        self.update_widget()

    def update_widget(self,value = None):
        run=False
        if value is None:
            run=True
        else:
            value=limit_in_range(value,self.value_min,self.value_max)
            if value!=self.current_value:
                self.current_value=value
                run=True
        if run:
            self.move_from_update=True
            self.zoom_slider.setValue(100 - int(
                math.log(
                    ((self.current_value - self.value_min) * (self.e_constant - 1) / (self.value_max - self.value_min) + 1)
                ) * self.zoom_coef
            ))   
            self.move_from_update=False
            if self.current_value == self.value_min:
                self.zoom_in_button.setEnabled(False)
                self.zoom_out_button.setEnabled(True)
            elif self.current_value == self.value_max:
                self.zoom_out_button.setEnabled(False)
                self.zoom_in_button.setEnabled(True)
            else:
                if not self.zoom_out_button.isEnabled():
                    self.zoom_out_button.setEnabled(True)
                if not self.zoom_in_button.isEnabled():
                    self.zoom_in_button.setEnabled(True)

    def apply_value_func(self,value):
        raise NotImplementedError()