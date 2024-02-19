from qfluentwidgets import FluentIcon,Action,RoundMenu,MessageBox
import pyqtgraph as pg
import numpy as np
from ..widgets.q_plot_widget import QPlotWidget
from ..widgets.value_select_box import select_str,select_limited_str
from ..widgets.removable_table import RemovableTable

class SavedFrameTable(RemovableTable):
    """
    Table widget for displaying saved frames.
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent, show_row_index=False, 
                         resize_columns_to_contents=False, 
                         show_move_up_down_buttons=False, 
                         show_delete_button=True, 
                         show_rename_button=True, 
                         accept_name="Jump to", accept_icon=FluentIcon.CHEVRON_RIGHT,
                         link_default_slot=True)
        self.set_header_labels(["Name", "Location", "Range"])
        self.setColumnWidth(0, 100)
        self.setColumnWidth(1, 150)
        self.setColumnWidth(2, 150)


class FrameRecorderComponent():
    """
    A Component for recording and managing frames in a plot widget.
    """

    def __init__(self, plot_widget: QPlotWidget, parent=None) -> None:
        """
        Initialize the FrameRecorderComponent.

        Args:
            plot_widget (QPlotWidget): The plot widget to record frames from.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        self.parent = parent
        self.plot_widget = plot_widget
        view_rect = self.plot_widget.viewRect()
        self.current_x_loc = view_rect.left()
        self.current_x_range = view_rect.width()
        self.record_current_frame_change = True
        self.previous_frame = []
        self.saved_frame = []
        self.num_previous_frame = 30
        self.full_range_action = Action(FluentIcon.FULL_SCREEN, 'Full range')
        self.latest_frame_action = Action(FluentIcon.RIGHT_ARROW, 'Latest')
        self.previous_frame_action = Action(FluentIcon.CANCEL, 'Previous frame')
        self.given_frame_action = Action(FluentIcon.LABEL, 'Input coordinate')
        self.record_current_frame_action = Action(FluentIcon.ADD_TO, 'Record current frame')
        self.jump_to_menu = RoundMenu("Jump to", self.parent)
        self.jump_to_menu.setIcon(FluentIcon.CHEVRON_RIGHT)
        self.jump_to_menu.addAction(self.previous_frame_action)
        self.jump_to_menu.addAction(self.full_range_action)
        self.jump_to_menu.addAction(self.latest_frame_action)
        self.jump_to_menu.addAction(self.given_frame_action)
        self.saved_frame_table = SavedFrameTable(self.parent)
        self.saved_frame_table.sigAcceptClicked.connect(self.__on_table_jump_to_clicked)
        self.saved_frame_table.sigRowClicked.connect(self.__on_table_jump_to_clicked)
        self.saved_frame_table.sigNameEdited.connect(self.__on_table_name_changed)
        self.saved_frame_table.sigDeleteClicked.connect(self.__on_table_row_deleted)
        self.saved_frame_table.hide()

        self.__init_connections()

    def __init_connections(self):
        """
        Initialize the signal connections.
        """
        self.full_range_action.triggered.connect(
            lambda: self.plot_widget.update_plot(x_loc=self.plot_widget.x_start, x_range=self.plot_widget.x_range_max))
        self.latest_frame_action.triggered.connect(
            lambda: self.plot_widget.update_plot(x_loc=self.plot_widget.x_end - self.plot_widget.x_range_min,
                                                 x_range=self.plot_widget.x_range_min))
        self.previous_frame_action.triggered.connect(self.__on_previous_frame_clicked)
        self.given_frame_action.triggered.connect(self.__on_given_frame_clicked)
        self.record_current_frame_action.triggered.connect(self.__on_record_current_frame_clicked)
        self.pg_plotter_view_changed_slot = pg.SignalProxy(self.plot_widget.sigRangeChanged, rateLimit=100,
                                                           slot=self.__on_pg_plotter_view_changed)

    def __on_pg_plotter_view_changed(self, event):
        """
        Handle the event when the plot view changes.

        Args:
            event: The event object.

        Returns:
            None
        """
        if self.record_current_frame_change:  # move plot will also trigger this event
            view_rect = self.plot_widget.viewRect()
            if view_rect.left() != self.current_x_loc or view_rect.width() != self.current_x_range:
                self.current_x_loc = view_rect.left()
                self.current_x_range = view_rect.width()
                if len(self.previous_frame) == self.num_previous_frame:
                    self.previous_frame.pop(0)
                    self.previous_frame.append((self.current_x_loc, self.current_x_range))
                else:
                    self.previous_frame.append((self.current_x_loc, self.current_x_range))
                if len(self.previous_frame) > 1:
                    self.previous_frame_action.setVisible(True)
        self.record_current_frame_change = True

    def __on_previous_frame_clicked(self):
        """
        Move the plot to the previous frame and update the previous_frame list.
        If there is only one frame left in the previous_frame list, hide the 'previous_frame' option in the context menu.
        """
        if len(self.previous_frame) > 1:
            self.record_current_frame_change = False
            self.plot_widget.update_plot(x_loc=self.previous_frame[-2][0], x_range=self.previous_frame[-2][1])
            self.previous_frame.pop(-1)
            if len(self.previous_frame) == 1:
                self.previous_frame_action.setVisible(False)

    def __on_record_current_frame_clicked(self):
        """
        Records the current frame by prompting the user to input a frame name and saves it to the `saved_frame` list.
        Updates the saved frame menu afterwards.
        """
        frame_name = select_str(self.parent.window(), "Input frame name", "saved_frame_{}".format(len(self.saved_frame) + 1))
        if frame_name is not None:
            view_rect = self.plot_widget.viewRect()
            self.saved_frame.append([frame_name, view_rect.left(), view_rect.width()])
            self.saved_frame_table.add_row_data(
                [frame_name, self.plot_widget.getAxis('bottom').tick_str(view_rect.left()), str(view_rect.width())])

    def __on_given_frame_clicked(self):
        """
        Handle the event when a frame is clicked.

        This method prompts the user to input a coordinate and moves the plot accordingly.

        Returns:
            None
        """
        if self.plot_widget.getAxis('bottom').plot_strs is None:
            MessageBox("Error", content="There is no support coordinate system in the plot!",
                       parent=self.parent.window()).exec()
        else:
            items = list(self.plot_widget.getAxis('bottom').plot_strs.values())
            select_x = select_limited_str(self.parent.window(), "Input coordinate", items)
            if select_x is not None:
                self.plot_widget.update_plot(
                    x_loc=items.index(select_x) - self.plot_widget.x_range_min / 2,
                    x_range=self.plot_widget.x_range_min)

    def __on_table_jump_to_clicked(self, row: int):
        """
        Handle the event when a frame is clicked.

        This method moves the plot to the selected frame.

        Args:
            row (int): The row index of the selected frame.

        Returns:
            None
        """
        self.plot_widget.update_plot(x_loc=self.saved_frame[row][1], x_range=self.saved_frame[row][2])

    def __on_table_name_changed(self, row: int, new_name: str):
        """
        Handle the event when the name of a frame is changed.

        Args:
            row (int): The row index of the frame.
            new_name (str): The new name for the frame.

        Returns:
            None
        """
        if new_name != "":
            self.saved_frame[row][0] = new_name
            self.saved_frame_table.set_row_data_item(row, 0, new_name)
        else:
            self.saved_frame_table.set_row_data_item(row, 0, self.saved_frame[row][0])

    def __on_table_row_deleted(self, row: int):
        """
        Handle the event when a frame is deleted.

        Args:
            row (int): The row index of the frame to be deleted.

        Returns:
            None
        """
        self.saved_frame.pop(row)

    def get_widget(self):
        """
        Get the widget associated with the FrameRecorderComponent.

        Returns:
            QWidget: The widget associated with the FrameRecorderComponent.
        """
        return self.saved_frame_table