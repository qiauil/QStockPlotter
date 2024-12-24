from pyqtgraph import PlotWidget,SignalProxy,AxisItem
from PyQt6.QtCore import Qt,pyqtSignal,QRectF
from math import ceil,log10
from qfluentwidgets import qconfig,Theme,isDarkTheme,MenuAnimationType,FluentIcon,Action,RoundMenu,MenuIndicatorType,CheckableMenu,PillPushButton
from pyqtgraph import PlotCurveItem
from typing import Union
from ..libs.style import LIGHT_BACKGROUND_COLOR,DARK_BACKGROUND_COLOR
from ..libs.constant import ZOOM_MODEL, YLOC_MODEL, SCALE_LOC_MODEL
from ..libs.helpers import limit_in_range,GeneralDataClass
from .value_select_box import select_value
from typing import Optional

class CustomizedAxis(AxisItem):
   
    def __init__(self, orientation, plot_strs=None ,pen=None, textPen=None, tickPen=None, linkView=None, parent=None, maxTickLength=-5, showValues=True, text='', units='', unitPrefix='', **args):
        """
        CustomizedAxis class represents a customized axis for a plot.

        Args:
            orientation (str): The orientation of the axis. Can be 'left', 'right', 'top', or 'bottom'.
            plot_strs (dict): A dictionary mapping index values to plot strings.
            pen (QPen): The pen used to draw the axis line.
            textPen (QPen): The pen used to draw the axis labels.
            tickPen (QPen): The pen used to draw the axis ticks.
            linkView (ViewBox): The view box to link the axis to.
            parent (QObject): The parent object of the axis.
            maxTickLength (int): The maximum length of the tick lines.
            showValues (bool): Whether to show the tick values.
            text (str): The text to display next to the axis.
            units (str): The units of the axis values.
            unitPrefix (str): The prefix to use for the units.
            **args: Additional keyword arguments.
        """
        super().__init__(orientation, pen, textPen, tickPen, linkView, parent, maxTickLength, showValues, text, units, unitPrefix, **args)
        self.plot_strs=plot_strs
        self.min_index=0
        self.max_index=0

    def set_tick_strings(self,plot_strs):
        """
        Set the plot strings for the axis.

        Args:
            plot_strs (dict): A dictionary mapping index values to plot strings.
        """
        self.plot_strs=plot_strs
        indexs=list(plot_strs.keys())
        self.min_index=indexs[0]
        self.max_index=indexs[-1]

    def tick_str(self,value):
        """
        Return the tick string for the given value.

        Args:
            value (float): The value of the tick.

        Returns:
            str: The tick string.
        """
        if self.plot_strs is None:
            return "{:.1f}".format(value)
        else:
            if (value>=self.min_index and value<=self.max_index):
                return self.plot_strs[round(value)]
            else:
                return " "

    def tickStrings(self, values, zoom, spacing):
        """
        Return the strings that should be placed next to ticks.

        This method is called when redrawing the axis and is a good method to override in subclasses.
        The method is called with a list of tick values, a scaling factor, and the spacing between ticks.

        Args:
            values (list): The list of tick values.
            zoom (float): The scaling factor for the axis label.
            spacing (float): The spacing between ticks.

        Returns:
            list: The list of tick strings.
        """
        if self.logMode:
            return self.logTickStrings(values, zoom, spacing)

        places = max(0, ceil(-log10(spacing*zoom)))
        if self.plot_strs is None:
            strings = []
            for v in values:
                vs = v * zoom
                if abs(vs) < .001 or abs(vs) >= 10000:
                    vstr = "%g" % vs
                else:
                    vstr = ("%%0.%df" % places) % vs
                strings.append(vstr)
        else:
            strings = [self.plot_strs[int(v)] if (v>=self.min_index and v<=self.max_index) else " " for v in values ]
        return strings

# NOTE: the y of viewRect is reversed, i.e. the top is the max value and the bottom is the min value
class QPlotWidget(PlotWidget):
    sigBoundingUpdated = pyqtSignal()
    sigSizeChanged = pyqtSignal()
    sigZoomModelChanged = pyqtSignal()
    sigYLocModelChanged = pyqtSignal()
    sigMouseLeaved = pyqtSignal()
    sigEnterPressed = pyqtSignal()
    sigEscapePressed = pyqtSignal()
    sigViewChanged = pyqtSignal()
    sigViewChangedByDrag = pyqtSignal()
    sigViewChangedNotByDrag = pyqtSignal()
    
    def __init__(self, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(parent, background, plotItem, **kargs)
        self.__init_configuration()
        self.__init_variables()
        self.__init__config_variables()
        self.__init_connections()
        self.__init_context_menu()
        
        self.__on_theme_changed()
        self.set_zoom_model(ZOOM_MODEL.AUTO_RANGE)
        self.set_y_loc_model(YLOC_MODEL.DATA_CENTERED)
    
    def __init_configuration(self):
        self.setMouseEnabled(x=True, y=False)
        self.setMenuEnabled(False)
        self.setAxisItems({'bottom':CustomizedAxis(orientation='bottom')})
        self.setAxisItems({'left':CustomizedAxis(orientation='left')})
        self.getAxis('bottom').setHeight(32)
        self.getAxis('bottom').setStyle(tickTextOffset=10)
        self.getAxis('left').setWidth(70)
        self.getAxis('left').setStyle(tickTextOffset=10)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.showGrid(x=True, y=True)
    
    def __init_variables(self):
        self.plotted_items=[]
        self.x_start=None
        self.x_end=None
        self.y_end=None
        self.y_start=None
        self.__reset_bounding()
        self.fixed_yx_ratio=(self.x_end-self.x_start)/(self.y_start-self.y_end)
        self.fixed_y_loc=self.y_start
        self.fixed_y_range=self.y_end-self.y_start
        self.x_start_button_held=False
        self.zoom_model=ZOOM_MODEL.AUTO_RANGE
        self.y_loc_model=YLOC_MODEL.DATA_CENTERED
        self.move_from_code=False
    
    def __init__config_variables(self):
        self.y_autorange_bounding_factor=0.05
        self.zoom_loc_model=SCALE_LOC_MODEL.RIGHT

    def __init_connections(self):
        self.view_changed_slot = SignalProxy(self.sigRangeChanged, rateLimit=50, slot=self.__on_range_changed)
        self.mouse_move_slot = SignalProxy(self.scene().sigMouseMoved, rateLimit=50, slot=self.__show_loc)
        self.show_cursor_slot = SignalProxy(self.scene().sigMouseMoved, rateLimit=50, slot=self.__update_cursor)
        qconfig.themeChanged.connect(self.__on_theme_changed)
        self.sigBoundingUpdated.connect(lambda :self.update_plot(x_loc=self.viewRect().left(),x_range=self.viewRect().width()))

    def __init_context_menu(self):
        self.context_menu_actions = GeneralDataClass(
            zoom_models=GeneralDataClass(
                auto_range=Action('Adaptive'),
                fixed_aspect_ratio=Action('Fixed aspect ratio'),
                fixed_yrange=Action('Fixed y range'),
            ),
            y_loc_models=GeneralDataClass(
                data_centered=Action('Data centered'),
                fixed=Action('Fixed y location'),
                free=Action('Free to move'),
            )
        )
        for _,action in self.context_menu_actions.zoom_models:
            action.setCheckable(True)
        self.context_menu_actions.zoom_models.auto_range.setChecked(True)
        for _,action in self.context_menu_actions.y_loc_models:
            action.setCheckable(True)
        self.context_menu_actions.zoom_models.auto_range.triggered.connect(lambda:self.set_zoom_model(ZOOM_MODEL.AUTO_RANGE))
        self.context_menu_actions.zoom_models.fixed_aspect_ratio.triggered.connect(lambda:self.set_zoom_model(ZOOM_MODEL.FIXED_RATIO))
        self.context_menu_actions.zoom_models.fixed_yrange.triggered.connect(lambda:self.set_zoom_model(ZOOM_MODEL.FIXED_YRANGE))
        self.context_menu_actions.y_loc_models.free.triggered.connect(lambda:self.set_y_loc_model(YLOC_MODEL.FREE))
        self.context_menu_actions.y_loc_models.data_centered.triggered.connect(lambda:self.set_y_loc_model(YLOC_MODEL.DATA_CENTERED))
        self.context_menu_actions.y_loc_models.fixed.triggered.connect(lambda:self.set_y_loc_model(YLOC_MODEL.FIXED))
        self.zoom_model_menu = CheckableMenu("Zoom model", self, indicatorType=MenuIndicatorType.RADIO)
        self.zoom_model_menu.setIcon(FluentIcon.ZOOM)
        self.zoom_model_menu.addActions([action for _,action in self.context_menu_actions.zoom_models])
        self.zoom_model_menu.addSeparator()
        self.zoom_model_menu.addActions([action for _,action in self.context_menu_actions.y_loc_models])
        self.context_menu = RoundMenu(parent=self)
        self.context_menu.addMenu(self.zoom_model_menu)    

    def __reset_bounding(self):
        view_rect = self.viewRect()
        self.x_start=view_rect.left()
        self.x_end=view_rect.right()
        self.y_end=view_rect.bottom()
        self.y_start=view_rect.top()
        self.__on_plot_bounding_updated()
        self.sigBoundingUpdated.emit()
    
    def __on_plot_bounding_updated(self):
        # the reason for not conncecting this function to sigBoundingUpdated is that
        # we need to update the bounding rect before emitting the signal
        # so that outside world can get the updated range_max/min
        self.x_range_max=self.x_end-self.x_start
        self.x_range_min=self.x_range_max/1000
        self.y_range_max=self.y_end-self.y_start
        self.y_range_min=self.y_range_max/1000
        self.setLimits(xMin=self.x_start, xMax=self.x_end, yMin=self.y_start, yMax=self.y_end,
                       minXRange=self.x_range_min, maxXRange=self.x_range_max,
                       minYRange=self.y_range_min, maxYRange=self.y_range_max)

    def __on_range_changed(self):
        self.sigViewChanged.emit()
        if not self.move_from_code:
            self.update_plot()
            self.sigViewChangedByDrag.emit()
        else:
            self.move_from_code=False
            self.sigViewChangedNotByDrag.emit()

    def __on_theme_changed(self,theme=None):
        """
        Callback method triggered when the theme is changed.

        Args:
            theme (Theme): The new theme.

        Returns:
            None
        """
        if theme == Theme.DARK:
            self.setBackground(DARK_BACKGROUND_COLOR)
        elif theme == Theme.LIGHT:
            self.setBackground(LIGHT_BACKGROUND_COLOR)
        else:
            if isDarkTheme():
                self.setBackground(DARK_BACKGROUND_COLOR)
            else:
                self.setBackground(LIGHT_BACKGROUND_COLOR)

    def __plot_bounding(self):
        x_starts=[]; x_ends=[]; y_ends=[]; y_starts=[]
        for item in self.plotted_items:
            x_starts.append(item.boundingRect().left())
            x_ends.append(item.boundingRect().right())
            y_ends.append(item.boundingRect().bottom())
            y_starts.append(item.boundingRect().top())
        return min(x_starts), max(x_ends), min(y_starts), max(y_ends)

    def __show_loc(self,event):
        if not hasattr(self, 'loc_xlabel'):
            #pen = pg.mkPen(self.main_item.style.cross_line_color, width=1)
            #self.vline = pg.InfiniteLine(angle=90, movable=False, pen=pen)
            #self.hline = pg.InfiniteLine(angle=0, movable=False, pen=pen)
            #self.addItem(self.vline, ignoreBounds=True)
            #self.addItem(self.hline, ignoreBounds=True)
            self.loc_xlabel=PillPushButton(parent=self)
            self.loc_ylabel=PillPushButton(parent=self)
            self.loc_ylabel.setFixedHeight(int(self.getAxis('bottom').height()))
            self.loc_xlabel.setFixedHeight(int(self.getAxis('bottom').height()))  
            self.loc_ylabel.setFixedWidth(int(self.getAxis('left').width()))
        pos = event[0]
        mouse_point=self.plotItem.vb.mapSceneToView(pos)
        if self.viewRect().contains(mouse_point):    
            self.loc_ylabel.setText(str(round(mouse_point.y(), 1)))
            self.loc_ylabel.move(0,int(pos.y()-self.loc_ylabel.geometry().height()/2))
            if self.loc_ylabel.isHidden():
                self.loc_ylabel.show()
            self.loc_xlabel.setText(self.getAxis('bottom').tick_str(mouse_point.x()))
            self.loc_xlabel.move(int(pos.x() - self.loc_xlabel.geometry().width()/2),
                                int(self.geometry().height()-self.loc_xlabel.geometry().height()))
            self.loc_xlabel.setFixedWidth(len(self.loc_xlabel.text())*10)
            if self.loc_xlabel.isHidden():
                self.loc_xlabel.show()
        else:
            self.loc_xlabel.hide()
            self.loc_ylabel.hide() 

    def __update_cursor(self,event):
        if self.x_start_button_held:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            mouse_point=self.plotItem.vb.mapSceneToView(event[0])
            find=False
            for item in self.scene().items():
                if isinstance(item, PlotCurveItem):
                    if item.clickable and item.mouseShape().contains(mouse_point):
                        self.setCursor(Qt.CursorShape.PointingHandCursor)
                        find=True
                        break
            if not find:
                self.setCursor(Qt.CursorShape.CrossCursor)

    def __update_zoom_loc_menu(self):
        """
        Update the y range and location menu based on the current zoom model.

        This method enables or disables the y location menu and sets the appropriate
        checked state for the y location models based on the current zoom model.

        Raises:
            Exception: If the zoom model is invalid.
        """
        def enable_y_loc_menu(enable: bool):
            if enable:
                for _, actions in self.context_menu_actions.y_loc_models:
                    actions.setChecked(False)
                    actions.setVisible(True)
                if self.y_loc_model == YLOC_MODEL.FREE:
                    self.context_menu_actions.y_loc_models.free.setChecked(True)
                    self.setMouseEnabled(x=True, y=True)
                elif self.y_loc_model == YLOC_MODEL.DATA_CENTERED:
                    self.context_menu_actions.y_loc_models.data_centered.setChecked(True)
                    self.setMouseEnabled(x=True, y=False)
                elif self.y_loc_model == YLOC_MODEL.FIXED:
                    self.context_menu_actions.y_loc_models.fixed.setChecked(True)
                    self.setMouseEnabled(x=True, y=False)
                else:
                    raise Exception("Invalid y_loc model")
            else:
                for _, actions in self.context_menu_actions.y_loc_models:
                    actions.setChecked(False)
                    actions.setVisible(False)

        if self.zoom_model == ZOOM_MODEL.AUTO_RANGE:
            for _, actions in self.context_menu_actions.zoom_models:
                actions.setChecked(False)
            self.context_menu_actions.zoom_models.auto_range.setChecked(True)
            self.setMouseEnabled(x=True, y=False)
            enable_y_loc_menu(False)
        elif self.zoom_model == ZOOM_MODEL.FIXED_RATIO:
            for _, actions in self.context_menu_actions.zoom_models:
                actions.setChecked(False)
            self.context_menu_actions.zoom_models.fixed_aspect_ratio.setChecked(True)
            enable_y_loc_menu(True)
        elif self.zoom_model == ZOOM_MODEL.FIXED_YRANGE:
            for _, actions in self.context_menu_actions.zoom_models:
                actions.setChecked(False)
            self.context_menu_actions.zoom_models.fixed_yrange.setChecked(True)
            enable_y_loc_menu(True)
        else:
            raise Exception("Invalid zoom model")
                    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.CrossCursor) 
            self.x_start_button_held=False
        return super().mouseReleaseEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.x_start_button_held=True
        return super().mousePressEvent(event)

    def contextMenuEvent(self, e):
        # show context menu
        self.context_menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)
        
    def leaveEvent(self, event):
        if hasattr(self, 'loc_xlabel'):
            self.loc_xlabel.hide()
            self.loc_ylabel.hide()
        self.sigMouseLeaved.emit()
        return super().leaveEvent(event)

    def resizeEvent(self, event):
        self.sigSizeChanged.emit()
        return super().resizeEvent(event)

    def add_item(self, plot_item, x_ticks=None, y_ticks=None):
        """
        Add a plot item to the plot widget.

        Parameters:
        plot_item (PlotItem): The plot item to be added.
        x_ticks (list, optional): The tick labels for the x-axis. Defaults to None.
        y_ticks (list, optional): The tick labels for the y-axis. Defaults to None.

        Returns:
        None
        """
        self.plotted_items.append(plot_item)
        self.addItem(plot_item)
        if len(self.plotted_items) == 1:
            self.x_start, self.x_end, self.y_start, self.y_end = self.__plot_bounding()
        else:
            x_start, x_end, y_start, y_end = self.__plot_bounding()
            self.x_start = min(self.x_start, x_start)
            self.x_end = max(self.x_end, x_end)
            self.y_start = min(self.y_start, y_start)
            self.y_end = max(self.y_end, y_end)
        if x_ticks is not None:
            self.getAxis('bottom').set_tick_strings(x_ticks)
        if y_ticks is not None:
            self.getAxis('left').set_tick_strings(y_ticks)
            
        self.__on_plot_bounding_updated()
        self.update_plot()
        self.sigBoundingUpdated.emit()
        return None

    def remove_item(self, plot_item):
        """
        Removes the specified plot item from the plot widget.

        Args:
            plot_item: The plot item to be removed.

        Returns:
            The return value of the removeItem() method.

        """
        self.plotted_items.remove(plot_item)
        return_value = self.removeItem(plot_item)
        if len(self.plotted_items)>0:
            self.x_start, self.x_end, self.y_start,self.y_end=self.__plot_bounding()
            self.__on_plot_bounding_updated()
            self.sigBoundingUpdated.emit()
        else:
            self.__reset_bounding()
        self.update_plot()
        return return_value
   
    def get_local_range(self, start, end):
        """
        Get the local plot range within the specified start and end values.

        Args:
            start (float): The start value of the range.
            end (float): The end value of the range.

        Returns:
            tuple: A tuple containing the minimum and maximum values of the local plot range.
                   If no valid local range is found, the range of the view rectangle is returned.
        """
        mins, maxs = [], []
        for item in self.plotted_items:
            if hasattr(item, 'get_local_plot_range'):
                local_range = item.get_local_plot_range(start, end)
                if local_range is not None:
                    mins.append(local_range[0])
                    maxs.append(local_range[1])
        if len(mins) > 0:
            return min(mins), max(maxs)
        else:
            return self.viewRect().top(), self.viewRect().bottom()

    def update_plot(self, x_loc:Optional[float]=None, x_range:Optional[float]=None):
        """
        Update the plot with new x-location and x-range values.

        Parameters:
        - x_loc Optional[float]: The x-location of the plot. If None, the leftmost x-coordinate of the view rectangle is used.
        - x_range Optional[float]: The x-range of the plot. If None, the width of the view rectangle is used.

        Returns:
        None
        """
        if x_loc is None and x_range is not None:
            if self.zoom_loc_model == SCALE_LOC_MODEL.CENTRAL:
                x_loc = (self.viewRect().left() + self.viewRect().right()) / 2 - x_range / 2
            elif self.zoom_loc_model == SCALE_LOC_MODEL.LEFT:
                x_loc = self.viewRect().left()
            elif self.zoom_loc_model == SCALE_LOC_MODEL.RIGHT:
                x_loc = self.viewRect().right() - x_range
        else:
            if x_loc is None:
                x_loc = self.viewRect().left()
            if x_range is None:
                x_range = self.viewRect().width()
        x_range = limit_in_range(x_range, self.x_range_min, self.x_range_max)
        x_loc = limit_in_range(x_loc, self.x_start, self.x_end - x_range)
        x_right = x_loc + x_range
        view_rect = self.viewRect()
        y_loc = view_rect.top()
        y_range = view_rect.height()
        y_center = y_loc + y_range / 2
        # calculate the yzoom
        if self.zoom_model == ZOOM_MODEL.AUTO_RANGE:
            y_loc, y_top = self.get_local_range(x_loc, x_right)
            y_range_bounding = self.y_autorange_bounding_factor * (y_top - y_loc)
            y_loc -= y_range_bounding / 2
            y_top += y_range_bounding / 2
            y_range = y_top - y_loc
        elif self.zoom_model == ZOOM_MODEL.FIXED_RATIO or self.zoom_model == ZOOM_MODEL.FIXED_YRANGE:
            if self.zoom_model == ZOOM_MODEL.FIXED_RATIO:
                y_range = x_range * self.fixed_yx_ratio
            else:
                y_range = self.fixed_y_range
            # make sure the zoom is in y center in fixed ratio model
            if self.y_loc_model == YLOC_MODEL.DATA_CENTERED:
                y_start, y_end = self.get_local_range(x_loc, x_right)
                y_loc = (y_start + y_end) / 2 - y_range / 2
            elif self.y_loc_model == YLOC_MODEL.FREE:
                y_loc = y_center - y_range / 2
            elif self.y_loc_model == YLOC_MODEL.FIXED:
                y_loc = self.fixed_y_loc
            else:
                raise Exception("Invalid y_loc model")
        else:
            raise Exception("Invalid zoom model")
        # make sure the yzoom is in the range
        y_loc = limit_in_range(y_loc, self.y_start, self.y_end - y_range)
        y_range = limit_in_range(y_range, self.y_range_min, self.y_range_max)
        self.move_from_code = True
        self.setRange(QRectF(x_loc, y_loc, x_range, y_range), padding=0)

    def move_y_loc(self, y_loc):
        """
        Move the y location of the plot.

        Parameters:
            y_loc (float): The new y location.

        Raises:
            Exception: If the y_loc_model is not YLOC_MODEL.FREE.
            Exception: If the zoom_model is ZOOM_MODEL.AUTO_RANGE.

        Returns:
            None
        """
        if self.y_loc_model != YLOC_MODEL.FREE:
            raise Exception("you can only move y in y_loc free model")
        if self.zoom_model == ZOOM_MODEL.AUTO_RANGE:
            raise Exception("you can not move y in auto_range model")
        y_loc = limit_in_range(y_loc, self.y_start, self.y_end - self.viewRect().height())
        self.move_from_code = True
        self.setRange(QRectF(self.viewRect().left(), y_loc, self.viewRect().width(), self.viewRect().height()), padding=0)

    def set_zoom_model(self, zoom_model):
        """
        Set the y range model for the plotter.

        Parameters:
            zoom_model (int): The zoom model to set. Should be one of the values from the ZOOM_MODEL enum.

        Raises:
            Exception: If an invalid zoom model is provided.
        """
        if zoom_model == ZOOM_MODEL.AUTO_RANGE:
            self.zoom_model = ZOOM_MODEL.AUTO_RANGE
            self.__update_zoom_loc_menu()
            self.update_plot()
        elif zoom_model == ZOOM_MODEL.FIXED_RATIO:
            new_yx_ratio = select_value(parent=self.window(), title="Set aspect ratio", allowed_min=0.1, current=self.viewRect().height()/self.viewRect().width())
            if new_yx_ratio is not None:
                self.fixed_yx_ratio = new_yx_ratio
                self.zoom_model = ZOOM_MODEL.FIXED_RATIO
            self.__update_zoom_loc_menu()
            self.update_plot()
        elif zoom_model == ZOOM_MODEL.FIXED_YRANGE:
            new_y_range = select_value(parent=self.window(), title="Set y range", allowed_min=self.y_range_min, allowed_max=self.y_range_max, current=self.viewRect().height())
            if new_y_range is not None:
                self.fixed_y_range = new_y_range
                self.zoom_model = ZOOM_MODEL.FIXED_YRANGE
            self.__update_zoom_loc_menu()
            self.update_plot()
        else:
            raise Exception("Invalid zoom model")
        self.sigZoomModelChanged.emit()

    def set_y_loc_model(self, y_loc_model):
        """
        Set the y location model for the plotter.

        Parameters:
            y_loc_model (YLOC_MODEL): The y location model to set.

        Returns:
            None
        """
        if y_loc_model == YLOC_MODEL.FREE:
            self.y_loc_model = YLOC_MODEL.FREE
            self.__update_zoom_loc_menu()
            self.update_plot()
        elif y_loc_model == YLOC_MODEL.DATA_CENTERED:
            self.y_loc_model = YLOC_MODEL.DATA_CENTERED
            self.__update_zoom_loc_menu()
            self.update_plot()
        elif y_loc_model == YLOC_MODEL.FIXED:
            new_y_loc = select_value(parent=self.window(), title="Set y start location", allowed_min=self.y_start, allowed_max=self.y_end, current=self.viewRect().top())
            if new_y_loc is not None:
                self.y_loc = new_y_loc
                self.fixed_y_loc = new_y_loc
                self.y_loc_model = YLOC_MODEL.FIXED
            self.__update_zoom_loc_menu() 
            self.update_plot()
        else:
            raise Exception("Invalid y_loc model")  
        self.sigYLocModelChanged.emit()

    def add_context_menu(self,item:Union[Action,RoundMenu]):
        if isinstance(item,Action):
            self.context_menu.addAction(item)
        elif isinstance(item,RoundMenu):
            self.context_menu.addMenu(item)
    
    def insert_context_menu(self, item: Union[Action, RoundMenu]):
        """
        Inserts an item into the context menu.

        Parameters:
            item (Union[Action, RoundMenu]): The item to be inserted into the context menu.

        Returns:
            None
        """
        if isinstance(item, Action):
            item = self.context_menu._createActionItem(item, before=None)
            self.context_menu.view.insertItem(0, item)
            self.context_menu.adjustSize()
        elif isinstance(item, RoundMenu):
            item, w = self.context_menu._createSubMenuItem(item)
            self.context_menu.view.insertItem(0, item)
            self.context_menu.view.setItemWidget(item, w)

    def set_full_range_enabled(self, enabled: bool):
        """
        Set whether the full range is enabled.

        Parameters:
            enabled (bool): Whether the full range is enabled.

        Returns:
            None
        """
        if enabled:
            self.plotItem.hideButtons()
        else:
            self.plotItem.showButtons()