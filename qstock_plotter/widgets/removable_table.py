from qfluentwidgets import FluentIcon,Action,Flyout,FlyoutAnimationType,TableWidget,CommandBarView,TableItemDelegate
from PyQt6.QtWidgets import QHBoxLayout, QTableView,QTableWidgetItem
from PyQt6.QtCore import Qt,pyqtSignal,QEvent,QModelIndex
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QWidget,QStyleOptionViewItem

# https://forum.qt.io/topic/97628/qlistwidget-item-editing/13
class JEditableListStyledItemDelegate(TableItemDelegate):
    # class variable for "editStarted" signal, with QModelIndex parameter
    editStarted = pyqtSignal(QModelIndex, name='editStarted')
    # class variable for "editFinished" signal, with QModelIndex parameter
    editFinished = pyqtSignal(QModelIndex, name='editFinished')
    
    def __init__(self, parent: QTableView):
        super().__init__(parent)
        self.edit_created = False

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        editor = super().createEditor(parent, option, index)
        self.edit_created = True
        if editor is not None:
            self.editStarted.emit(index)
        return editor

    def destroyEditor(self, editor: QWidget, index: QModelIndex):
        if self.edit_created:
            self.editFinished.emit(index)
            self.edit_created = False
        return super().destroyEditor(editor, index)


class RemovableTable(TableWidget):

    sigAcceptClicked=pyqtSignal(int)
    sigRowClicked=pyqtSignal(int)
    sigDeleteClicked=pyqtSignal(int)
    sigMoveUpClicked=pyqtSignal(int)
    sigMoveDownClicked=pyqtSignal(int)
    sigNameEdited=pyqtSignal(int,str)
    
    def __init__(self, parent=None,
                 show_row_index=False,
                 resize_columns_to_contents=True,
                 show_move_up_down_buttons=True,
                 show_delete_button=True,
                 show_rename_button=True,
                 accept_name="Select",
                 accept_icon=FluentIcon.ACCEPT,
                 link_default_slot=True):
        super().__init__(parent)
        self.setBorderVisible(True)
        self.setBorderRadius(8)
        self.setWordWrap(False)
        self.viewport().installEventFilter(self)
        styledItemDelegate = JEditableListStyledItemDelegate(self)
        styledItemDelegate.editFinished.connect(self.__on_name_changed)
        self.setItemDelegate(styledItemDelegate)
        self.current_item=None
        self.show_row_index=show_row_index
        self.resize_columns_to_contents=resize_columns_to_contents
        self.show_move_up_down_buttons=show_move_up_down_buttons
        self.show_delete_button=show_delete_button
        self.show_rename_button=show_rename_button
        self.accept_name=accept_name
        self.accept_icon=accept_icon
        self.act_from_self=False
        if not self.show_row_index:
            self.verticalHeader().hide()
        if link_default_slot:
            self.sigAcceptClicked.connect(self.accept_row_data)
            self.sigDeleteClicked.connect(self.delete_row_data)
            self.sigMoveUpClicked.connect(self.move_up_row_data)
            self.sigMoveDownClicked.connect(self.move_down_row_data)
    
    def show_menu_bar(self):
        """
        Show the menu bar with various actions such as accept, rename, move up, move down, and delete.
        NOTE: Must specify the current item before calling this method.
        """
        self.command_bar=CommandBarView(self)
        select_action=Action(self.accept_icon, self.accept_name)
        select_action.triggered.connect(self.__on_accept_clicked)
        self.command_bar.addAction(select_action)
        if self.show_rename_button:
            edit_action=Action(FluentIcon.FONT, 'Rename')
            edit_action.triggered.connect(self.__on_edit_row_clicked)
            self.command_bar.addAction(edit_action)
        if self.show_move_up_down_buttons:
            if self.current_item.row()>0:  
                move_up_action=Action(FluentIcon.UP, 'Move up')
                move_up_action.triggered.connect(self.__on_move_up_row_clicked)
                self.command_bar.addAction(move_up_action) 
            if self.current_item.row()<self.rowCount()-1: 
                move_down_action=Action(FluentIcon.DOWN, 'Move down')
                move_down_action.triggered.connect(self.__on_move_down_row_clicked)
                self.command_bar.addAction(move_down_action)
        if self.show_delete_button:
            delete_action=Action(FluentIcon.DELETE, 'Delete')
            delete_action.triggered.connect(self.__on_delete_row_clicked)
            self.command_bar.addAction(delete_action)  
        self.command_bar.resizeToSuitableWidth()
        self.shown_cbar=Flyout.make(self.command_bar, QCursor.pos(), self, FlyoutAnimationType.FADE_IN,True)
        
    
    def accept_row_data(self,row_index):
        pass

    def __on_accept_clicked(self):
        if self.current_item is not None:
            self.clearSelection()
            self.shown_cbar.close()
            self.sigAcceptClicked.emit(self.current_item.row())
            self.current_item=None

    def delete_row_data(self, row_index):
        """
        Delete a row of data from the table.

        Args:
            row_index (int): The index of the row to be deleted.
        """
        self.removeRow(row_index)
    def delete_row_data(self,row_index):      
        self.removeRow(row_index)
    
    def __on_delete_row_clicked(self):
        if self.current_item is not None:
            self.clearSelection()
            self.shown_cbar.close()
            self.sigDeleteClicked.emit(self.current_item.row())
            self.current_item=None

    def move_up_row_data(self, row_index):
        """
        Moves the data in the specified row up by one row.

        Args:
            row_index (int): The index of the row to move up.

        Returns:
            None
        """
        for j in range(self.columnCount()):
            temple = self.item(row_index, j).text()
            self.item(row_index, j).setText(self.item(row_index - 1, j).text())
            self.item(row_index - 1, j).setText(temple)
    def move_up_row_data(self,row_index):
        for j in range(self.columnCount()):
            temple=self.item(row_index,j).text()
            self.item(row_index,j).setText(self.item(row_index-1,j).text())
            self.item(row_index-1,j).setText(temple)
    
    def __on_move_up_row_clicked(self):
        if self.current_item is not None:
            self.clearSelection()
            self.shown_cbar.close()
            self.sigMoveUpClicked.emit(self.current_item.row())
            self.current_item=None

    def move_down_row_data(self, row_index, mute_signal=False):
        """
        Move the data in the specified row down by one row.

        Args:
            row_index (int): The index of the row to move down.
            mute_signal (bool, optional): Whether to mute the signal emitted during the move. Defaults to False.
        """
        for j in range(self.columnCount()):
            temple = self.item(row_index, j).text()
            self.item(row_index, j).setText(self.item(row_index + 1, j).text())
            self.item(row_index + 1, j).setText(temple)
    def move_down_row_data(self,row_index,mute_signal=False):
        for j in range(self.columnCount()):
            temple=self.item(row_index,j).text()
            self.item(row_index,j).setText(self.item(row_index+1,j).text())
            self.item(row_index+1,j).setText(temple)
  
    def __on_move_down_row_clicked(self):
        if self.current_item is not None:
            self.clearSelection()
            self.shown_cbar.close()
            self.sigMoveDownClicked.emit(self.current_item.row())
            self.current_item=None

    def rename(self,row_index):
        self.editItem(self.item(row_index,0))

    def __on_edit_row_clicked(self):
        if self.current_item is not None:
            self.rename(self.current_item.row())
            self.shown_cbar.close()

    def __on_name_changed(self, index):
        self.sigNameEdited.emit(index.row(),index.data())

    def set_header_labels(self, labels):
        """
        Set the header labels for the table.

        Args:
            labels (list): A list of strings representing the header labels.

        Returns:
            None
        """
        self.setColumnCount(len(labels))
        self.setHorizontalHeaderLabels(labels)
        if self.resize_columns_to_contents:
            self.resizeColumnsToContents()
    
    def set_row_data_item(self, row_index, col_index, item):
        """
        Sets the data item for a specific row and column in the table.

        Parameters:
            row_index (int): The index of the row.
            col_index (int): The index of the column.
            item (QWidget or any): The item to be set in the table.

        Returns:
            None
        """
        if isinstance(item, QWidget):
            item_text = " "
            self.setItem(row_index, col_index, QTableWidgetItem(item_text))
            self.setCellWidget(row_index, col_index, item)
        else:
            item = QTableWidgetItem(str(item))
            if col_index != 0:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row_index, col_index, item)
    
    def add_row_data(self, data_i):
        """
        Add a new row to the table and populate it with the given data.

        Args:
            data_i (list): The data to be added to the new row.

        Returns:
            None
        """
        row_count = self.rowCount()
        self.setRowCount(row_count + 1)
        for j, content in enumerate(data_i):
            self.set_row_data_item(row_count, j, content)
        if self.resize_columns_to_contents:
            self.resizeColumnsToContents()
    def add_row_data(self,data_i):
        row_count=self.rowCount()
        self.setRowCount(row_count+1)
        for j,content in enumerate(data_i):
            self.set_row_data_item(row_count,j,content)
        if self.resize_columns_to_contents:
            self.resizeColumnsToContents()

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            item=self.itemAt(event.pos())
            if item is not None:
                self.current_item=item
                self.clearSelection()
                self.selectRow(self.current_item.row())   
                if event.button() == Qt.MouseButton.LeftButton:
                    self.sigRowClicked.emit(self.current_item.row())
                elif event.button() == Qt.MouseButton.RightButton:   
                    self.show_menu_bar()
        return super().eventFilter(source, event)