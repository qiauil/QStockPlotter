from PyQt6.QtCore import Qt,pyqtSignal,QObject,QEvent
from pyqtgraph import PlotCurveItem
import pyqtgraph as pg
import numpy as np
from qfluentwidgets import CommandBar,setFont,FluentIcon,Action
from ..widgets.transparent_selector import TransparentColorSelector,TransparentDashTypeSelector,TransparentLineWidthSelector
from ..widgets.q_plot_widget import QPlotWidget
from ..widgets.value_select_box import confirmation_dialog
from ..widgets.removable_table import RemovableTable
from ..widgets.line_card import LineCard
from ..widgets.transparent_Line_edit import TransparentLineEdit
from ..libs.constant import ZOOM_MODEL,YLOC_MODEL



class DrawLineCommandBar(CommandBar):
    """
    Command bar for drawing lines.
    """

    def __init__(self, parent=None, show_text_editor=True):
        """
        Initialize the DrawLineCommandBar.

        Args:
            parent: The parent widget. Defaults to None.
            show_text_editor: Flag to show the text editor. Defaults to True.
        """
        super().__init__(parent)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        # set up editor
        if show_text_editor:
            self.line_name_editor = TransparentLineEdit(parent=self)
            self.line_name_editor.line_edit.setClearButtonEnabled(True)
            self.line_name_editor.line_edit.setPlaceholderText("Line name")
            self.line_name_editor.setFixedWidth(140)
            self.line_name_editor.setFixedHeight(34)
            self.addWidget(self.line_name_editor)
        # set up selectors
        self.line_color_selector = TransparentColorSelector(parent=self)
        self.line_color_selector.setFixedWidth(140)
        self.line_dash_type_selector = TransparentDashTypeSelector(parent=self)
        self.line_width_selector = TransparentLineWidthSelector(parent=self)
        for selector in [
            self.line_color_selector,
            self.line_dash_type_selector,
            self.line_width_selector,
        ]:
            selector.setFixedHeight(34)
            setFont(selector, 12)
            self.addWidget(selector)
        self.addSeparator()
        # set up buttons
        self.draw_line_cancel_action = Action(FluentIcon.CANCEL, 'Cancel', parent=self)
        self.draw_line_accept_action = Action(FluentIcon.SAVE, 'Save', parent=self)
        self.draw_line_close_action = Action(FluentIcon.CLOSE, 'Close', parent=self)
        self.draw_line_delete_action = Action(FluentIcon.DELETE, 'Delete', parent=self)
        for action_i in [
            self.draw_line_cancel_action,
            self.draw_line_delete_action,
            self.draw_line_accept_action,
            self.draw_line_close_action
        ]:
            self.addAction(action_i)
            if action_i is self.draw_line_delete_action:
                self.addSeparator()
        

class DrawnLineTable(RemovableTable):
    """
    A table widget for displaying and editing drawn lines.
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent, show_row_index=False, 
                         resize_columns_to_contents=False, 
                         show_move_up_down_buttons=False, 
                         show_delete_button=True, 
                         show_rename_button=True, 
                         accept_name="Edit", accept_icon=FluentIcon.EDIT,
                         link_default_slot=False)
        self.set_header_labels(["Name", "Line"])
        self.setColumnWidth(0,100)
        self.setColumnWidth(1,200)
        #self.setFixedWidth(300)

class DrawLineComponent(QObject):
    """
    A component for drawing lines on a plot widget.
    """

    sigLineRemoved=pyqtSignal(int)
    
    def __init__(self,plot_widget:QPlotWidget,parent=None) -> None:
        """
        Initializes a DrawLineComponent object.

        Args:
            plot_widget (QPlotWidget): The plot widget on which the lines will be drawn.
            parent (QObject, optional): The parent object. Defaults to None.
        """
        super().__init__(parent=parent)
        self.parent=parent
        self.custom_lines=[]
        self.current_custom_line=None
        self.is_current_line_new=True
        self.num_new_added_points=0
        self.clicked_from_line=False
        self.dynamic_line=None
        self.menu_action=Action(FluentIcon.PENCIL_INK, 'Draw line')
        self.plot_widget=plot_widget
        self.command_bar=DrawLineCommandBar(parent=parent,show_text_editor=True)
        self.command_bar.hide()
        self.line_table=DrawnLineTable(parent=parent)
        self.line_table.hide()
        self.__init_connections()
    
    def __init_connections(self):
        """
        Initializes the signal-slot connections for the DrawLineComponent object.
        """
        self.menu_action.triggered.connect(self.add_new_line)
        self.command_bar.draw_line_accept_action.triggered.connect(self.__on_draw_line_accept_clicked)
        self.command_bar.draw_line_cancel_action.triggered.connect(self.__on_draw_line_cancel_clicked)
        self.command_bar.draw_line_close_action.triggered.connect(self.__on_draw_line_close_clicked)
        
        self.command_bar.draw_line_delete_action.triggered.connect(self.remove_current_line)
        self.line_table.sigDeleteClicked.connect(self.remove_saved_line)
        self.sigLineRemoved.connect(lambda x:self.__deactivate_command_bar())
        self.sigLineRemoved.connect(self.line_table.delete_row_data)
        
        self.line_table.sigAcceptClicked.connect(self.__on_line_table_accept_clicked)
        self.line_table.sigRowClicked.connect(self.jump_to_line)
        self.line_table.sigNameEdited.connect(self.__on_line_table_name_changed)
        
        self.command_bar.line_color_selector.item_selected.connect(self.__on_line_color_selector_selected)
        self.command_bar.line_dash_type_selector.item_selected.connect(self.__on_line_dash_type_selector_selected)
        self.command_bar.line_width_selector.item_selected.connect(self.__on_line_width_selector_selected)
        self.command_bar.line_name_editor.sigTextEditFinished.connect(self.__on_line_name_editor_text_changed)
        self.plot_widget_clicked_slot = pg.SignalProxy(self.plot_widget.scene().sigMouseClicked, rateLimit=50, slot=self.__on_plot_widget_mouse_clicked)
        self.plot_widget_mouse_move_slot = pg.SignalProxy(self.plot_widget.scene().sigMouseMoved, rateLimit=50, slot=self.__on_plot_widget_mouse_moved)
        self.plot_widget_mouse_leave_slot = pg.SignalProxy(self.plot_widget.sigMouseLeaved, rateLimit=50, slot=self.__on_plot_widget_mouse_leaved)
        self.plot_widget.installEventFilter(self)

    def __activate_command_bar(self):
        """
        Activates the line command bar for the current custom line.

        Raises:
            Exception: If there is no current line.
        """
        if self.current_custom_line is None:
            raise Exception("No current line")
        self.is_current_line_new=not (self.current_custom_line in self.custom_lines)
        if self.is_current_line_new:
            self.command_bar.draw_line_delete_action.setEnabled(False)
        else:   
            self.command_bar.draw_line_delete_action.setEnabled(True)
        self.command_bar.line_name_editor.set_text(self.current_custom_line["name"])
        self.command_bar.line_color_selector.set_item(self.current_custom_line["color"])
        self.command_bar.line_width_selector.set_item(self.current_custom_line["width"])
        self.command_bar.line_dash_type_selector.set_item(self.current_custom_line["dash"])
        self.command_bar.draw_line_cancel_action.setEnabled(False)
        self.command_bar.draw_line_accept_action.setEnabled(False)
        self.command_bar.show()

    def __deactivate_command_bar(self):
        """
        Deactivates the line command bar and performs necessary cleanup.

        This method hides the draw line command bar, removes the dynamic line from the plot widget,
        resets the current custom line, and resets the number of new added points. It also adjusts
        the position of the zoom card.

        Note: The resize event doesn't work here for an unknown reason.

        Returns:
            None
        """
        self.command_bar.hide()
        self.current_custom_line = None
        if self.dynamic_line is not None:
            self.plot_widget.remove_item(self.dynamic_line)
            self.dynamic_line = None
        self.num_new_added_points = 0

    def __on_draw_line_cancel_clicked(self):
        """
        Callback method for handling the click event of the 'Cancel' button in the draw line functionality.
        Removes the last point from the current custom line, updates the data, and disables the accept and cancel buttons if no new points are added.
        """
        xs, ys = self.current_custom_line["line_item"].getData()
        self.current_custom_line["line_item"].setData(x=xs[0:-1], y=ys[0:-1])
        self.num_new_added_points -= 1
        if self.num_new_added_points == 0:
            self.command_bar.draw_line_cancel_action.setEnabled(False)
            self.command_bar.draw_line_accept_action.setEnabled(False)

    def __on_draw_line_accept_clicked(self):
        """
        Callback method for the 'Accept' button click event in the draw line functionality.
        Updates the properties of the current custom line based on the selected color, width, and dash type.
        If the current line is new, it appends it to the list of custom lines.
        Deactivates the line command bar.
        """
        self.current_custom_line["name"] = self.command_bar.line_name_editor.get_text()
        self.current_custom_line["color"] = self.command_bar.line_color_selector.current_item
        self.current_custom_line["width"] = self.command_bar.line_width_selector.current_item
        self.current_custom_line["dash"] = self.command_bar.line_dash_type_selector.current_item
        if self.is_current_line_new:
            self.current_custom_line["line_item"].setClickable(True)
            self.current_custom_line["line_item"].sigClicked.connect(self.__on_new_line_clicked)
            self.custom_lines.append(self.current_custom_line)
            self.line_table.add_row_data([self.current_custom_line["name"],
                                         LineCard(line_color=self.current_custom_line["color"],
                                                  line_width=self.current_custom_line["width"],
                                                  dash_type=self.current_custom_line["dash"])])
        else:
            row_index = self.custom_lines.index(self.current_custom_line)
            self.line_table.set_row_data_item(row_index,0,self.current_custom_line["name"])
            self.line_table.set_row_data_item(row_index,1,LineCard(line_color=self.current_custom_line["color"],
                                                  line_width=self.current_custom_line["width"],
                                                  dash_type=self.current_custom_line["dash"]))
        self.__deactivate_command_bar()

    def __on_draw_line_close_clicked(self):
        """
        Handles the event when the "Close" button is clicked in the draw line mode.

        If the current line is new and has unsaved points, a confirmation dialog is shown to ask if the user wants to leave without saving.
        If the user chooses to leave, the current line is removed from the plot widget.
        If the current line is not new but has unsaved points, a confirmation dialog is shown to ask if the user wants to leave without saving.
        If the user chooses to leave, the last added points are removed from the current line.
        The line command bar is deactivated after the operation.

        Returns:
            True if the operation is successful, False otherwise.
        """
        if self.is_current_line_new and self.num_new_added_points>0:
            if not confirmation_dialog(self.parent.window(),"Current line is not saved",
                                "The line you are editing now is not saved yet. Do you still want to leave?"):
                return False
            self.plot_widget.remove_item(self.current_custom_line["line_item"])
        elif self.num_new_added_points>0:
            if not confirmation_dialog(self.parent.window(),"Current line is not saved",
                            "The line you are editing now is not saved yet. Do you still want to leave?"):
                return False
            xs,ys=self.current_custom_line["line_item"].getData()
            self.current_custom_line["line_item"].setData(x=xs[0:-1*self.num_new_added_points],y=ys[0:-1*self.num_new_added_points])
        self.__deactivate_command_bar()
        return True

    def __on_new_line_clicked(self, line):
        """
        Event handler for when a new line is clicked.

        Args:
            line: The line that was clicked.

        Returns:
            False if the current line is not saved and the user chooses not to edit another line, True otherwise.
        """
        self.clicked_from_line = True

        if self.current_custom_line is not None:
            if not self.__on_draw_line_close_clicked():
                return False
        for line_item in self.custom_lines:
            if line_item["line_item"] is line:
                self.current_custom_line = line_item
                self.__activate_command_bar()
                break

    def __on_line_name_editor_text_changed(self):
        """
        Callback method for handling the text changed event of the line name editor.
        """
        pass
        current_text=self.command_bar.line_name_editor.line_edit.text()
        if current_text=="":
            self.command_bar.line_name_editor.set_text(self.current_custom_line["name"])
        elif current_text!=self.current_custom_line["name"]:
            xs,ys=self.current_custom_line["line_item"].getData()
            if len(xs)>0:
                self.command_bar.draw_line_accept_action.setEnabled(True)

    def __on_line_color_selector_selected(self, item):
        """
        Callback method triggered when a line color is selected in the color selector.

        Args:
            item: The selected item from the color selector.

        """
        if self.current_custom_line["color"]!=self.command_bar.line_color_selector.get_value(item):
            self.current_custom_line["line_item"].setPen(pg.mkPen(self.command_bar.line_color_selector.get_value(item), 
                            dash=self.command_bar.line_dash_type_selector.current_item,
                            width=self.command_bar.line_width_selector.current_item))
            self.current_custom_line["color"] = self.command_bar.line_color_selector.get_value(item)
            if self.dynamic_line is not None:
                self.dynamic_line.setPen(pg.mkPen(self.command_bar.line_color_selector.get_value(item), 
                            dash=self.command_bar.line_dash_type_selector.current_item,
                            width=self.command_bar.line_width_selector.current_item))
            xs,ys=self.current_custom_line["line_item"].getData()
            if len(xs)>0:
                self.command_bar.draw_line_accept_action.setEnabled(True)
    
    def __on_line_width_selector_selected(self, item):
        """
        Callback function for the line width selector.

        Args:
            item: The selected item from the line width selector.

        """
        if self.current_custom_line["width"]!=self.command_bar.line_width_selector.get_value(item):
            self.current_custom_line["line_item"].setPen(pg.mkPen(self.command_bar.line_color_selector.current_item, 
                            dash=self.command_bar.line_dash_type_selector.current_item,
                            width=self.command_bar.line_width_selector.get_value(item)))
            self.current_custom_line["width"] = self.command_bar.line_width_selector.get_value(item)
            if self.dynamic_line is not None:
                self.dynamic_line.setPen(pg.mkPen(self.command_bar.line_color_selector.current_item, 
                            dash=self.command_bar.line_dash_type_selector.current_item,
                            width=self.command_bar.line_width_selector.get_value(item)))
            xs,ys=self.current_custom_line["line_item"].getData()
            if len(xs)>0:
                self.command_bar.draw_line_accept_action.setEnabled(True)

    def __on_line_dash_type_selector_selected(self, item):
        """
        Callback method triggered when a line dash type is selected in the line dash type selector.

        Args:
            item: The selected line dash type item.

        """
        if self.current_custom_line["dash"]!=self.command_bar.line_dash_type_selector.get_value(item):
            self.current_custom_line["line_item"].setPen(pg.mkPen(self.command_bar.line_color_selector.current_item, 
                            dash=self.command_bar.line_dash_type_selector.get_value(item),
                            width=self.command_bar.line_width_selector.current_item))
            self.current_custom_line["dash"] = self.command_bar.line_dash_type_selector.get_value(item)
            if self.dynamic_line is not None:
                self.dynamic_line.setPen(pg.mkPen(self.command_bar.line_color_selector.current_item, 
                            dash=self.command_bar.line_dash_type_selector.get_value(item),
                            width=self.command_bar.line_width_selector.current_item))
            xs,ys=self.current_custom_line["line_item"].getData()
            if len(xs)>0:
                self.command_bar.draw_line_accept_action.setEnabled(True)

    def __on_line_table_name_changed(self, row_index, new_name):
        """
        Callback method triggered when the name of a line in the line table is changed.

        Args:
            row_index: The index of the row in the line table.
            new_name: The new name of the line.
        """
        if new_name=="":
            self.line_table.set_row_data_item(row_index,0,self.custom_lines[row_index]["name"])
        else:
            self.custom_lines[row_index]["name"] = new_name
            if self.custom_lines[row_index] == self.current_custom_line and self.command_bar.isVisible():
                self.command_bar.line_name_editor.set_text(new_name)

    def __on_line_table_accept_clicked(self, row_index):
        """
        Handles the event when the accept button is clicked in the line table.

        Args:
            row_index (int): The index of the selected row in the line table.
        """
        if self.jump_to_line(row_index):
            self.current_custom_line = self.custom_lines[row_index]
            self.__activate_command_bar()

    def __on_plot_widget_mouse_moved(self, event):
        """
        Handle the mouse moved event on the plot widget.

        Args:
            event: The mouse moved event.
        """
        pos = event[0]
        mouse_point=self.plot_widget.plotItem.vb.mapSceneToView(pos)
        if self.current_custom_line is not None:
            line_item=self.current_custom_line["line_item"]
            xs,ys=line_item.getData()
            if len(xs)>0:
                if self.dynamic_line is None:
                    self.dynamic_line=PlotCurveItem(
                        pen=pg.mkPen(self.current_custom_line["color"], 
                                    dash=self.current_custom_line["dash"],
                                    width=self.current_custom_line["width"]
                        ),
                        clickable=False
                    )
                    self.plot_widget.add_item(self.dynamic_line)
                self.dynamic_line.updateData(x=np.array([xs[-1],mouse_point.x()]),y=np.array([ys[-1],mouse_point.y()]))

    def __on_plot_widget_mouse_clicked(self,event=None):
        """
        Handle the mouse click event on the plotter.
        Add a new point to the current custom line if the left button is clicked.

        Parameters:
        - event (QMouseEvent): The mouse click event.

        """
        if self.current_custom_line is not None and event[0].button() == Qt.MouseButton.LeftButton:
            if not self.clicked_from_line:
                mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(event[0].scenePos())
                if self.plot_widget.viewRect().contains(mouse_point):
                    xs,ys=self.current_custom_line["line_item"].getData()
                    if len(xs)==0:
                        xs=np.array([mouse_point.x()])
                        ys=np.array([mouse_point.y()])
                    else:
                        xs=np.append(xs,mouse_point.x())
                        ys=np.append(ys,mouse_point.y())
                    self.__on_plot_widget_mouse_leaved(None)
                    self.current_custom_line["line_item"].setData(x=xs,y=ys)
                    self.command_bar.draw_line_cancel_action.setEnabled(True)
                    self.command_bar.draw_line_accept_action.setEnabled(True)
                    self.num_new_added_points+=1
                    #print(self.current_custom_line["line_item"].getData())
            else:
                self.clicked_from_line=False
    
    def __on_plot_widget_mouse_leaved(self, event):
        """
        Removes the dynamic line from the plot widget when the mouse leaves.

        Parameters:
        - event: The mouse leave event.

        """
        if self.dynamic_line is not None:
            self.plot_widget.remove_item(self.dynamic_line)
            self.dynamic_line = None

    def eventFilter(self, a0: QObject, a1: QEvent) -> bool:
        """
        Filters events for the specified object.

        Args:
            a0 (QObject): The object to filter events for.
            a1 (QEvent): The event to be filtered.

        Returns:
            bool: True if the event was filtered and should be ignored, False otherwise.
        """
        if a0 == self.plot_widget and a1.type() == QEvent.Type.KeyPress and self.command_bar.isVisible():
            if a1.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return) and self.command_bar.draw_line_accept_action.isEnabled():
                self.__on_draw_line_accept_clicked()
                return False
            elif a1.key() == Qt.Key.Key_Escape:
                self.__on_draw_line_close_clicked()
                return False
        return super().eventFilter(a0, a1)
  
    def get_widget(self):
        """
        Returns the command bar and line table as a tuple.

        Returns:
            tuple: A tuple containing the command bar and line table widgets.
        """
        return self.command_bar, self.line_table


    def add_new_line(self):
        """
        Adds a new line to the plot.

        If there is a current custom line being edited and it has unsaved changes, a confirmation dialog is displayed.
        If the user chooses to add a new line, the current line is closed and a new line is created with default settings.
        The new line is added to the plot and the line command bar is activated.
        """
        if self.current_custom_line is not None:
            if not self.__on_draw_line_close_clicked():
                return False
        line_item_now=PlotCurveItem(
            pen=pg.mkPen(self.command_bar.line_color_selector.default_item, 
                        dash=self.command_bar.line_dash_type_selector.default_item,
                        width=self.command_bar.line_width_selector.default_item
            ),
            clickable=False
        )
        self.current_custom_line={
            "name":"Line "+str(len(self.custom_lines)+1),
            "line_item":line_item_now,
            "color":self.command_bar.line_color_selector.default_item,
            "width":self.command_bar.line_width_selector.default_item,
            "dash":self.command_bar.line_dash_type_selector.default_item
        }
        self.__activate_command_bar()
        self.plot_widget.add_item(line_item_now)

    def remove_current_line(self):
        """
        Removes the current line from the list of custom lines.

        Raises:
            Exception: If the current line is new.
        
        Returns:
            bool: True if the line is successfully removed, False otherwise.
        """
        if self.is_current_line_new:
            raise Exception("Current line is new")
        row_index = self.custom_lines.index(self.current_custom_line)
        return self.remove_saved_line(row_index)
    
    def remove_saved_line(self,row_index):
        """
        Removes a saved line from the plot.

        Args:
            row_index (int): The index of the line to be removed.

        Returns:
            bool: True if the line was successfully removed, False otherwise.
        """
        if not confirmation_dialog(self.parent.window(),"Delete confirmation",
                                "Are you sure to delete the current line?"):
            return False
        else:
            self.plot_widget.remove_item(self.custom_lines[row_index]["line_item"])
            self.custom_lines.pop(row_index)
            self.sigLineRemoved.emit(row_index)
            return True

    def jump_to_line(self, row_index):
        """
        Jumps to the specified line in the plot.

        Args:
            row_index (int): The index of the line to jump to.

        Returns:
            bool: True if the jump was successful, False otherwise.
        """
        if self.current_custom_line is not None:
            if self.current_custom_line == self.custom_lines[row_index]:
                return True
            if not self.__on_draw_line_close_clicked():
                return False

        bounding_rect = self.custom_lines[row_index]["line_item"].boundingRect()
        x_range = bounding_rect.width()
        x_loc = bounding_rect.x()
        y_loc = bounding_rect.y()

        self.plot_widget.update_plot(x_loc=x_loc, x_range=x_range)

        if self.plot_widget.zoom_model != ZOOM_MODEL.AUTO_RANGE and self.plot_widget.y_loc_model == YLOC_MODEL.FREE:
            self.plot_widget.move_y_loc(y_loc)

        return True
