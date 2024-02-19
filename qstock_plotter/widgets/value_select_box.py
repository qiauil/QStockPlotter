from PyQt6.QtGui import QDoubleValidator, QIntValidator
from qfluentwidgets import (MessageBox,EditableComboBox,MessageBoxBase,SubtitleLabel,LineEdit,FluentIcon,RoundMenu,Action,DropDownToolButton,TableWidget,CommandBarView,Flyout,FlyoutAnimationType)
from PyQt6.QtWidgets import QHBoxLayout,QTableWidgetItem,QCompleter
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import pyqtSignal
from .transparent_selector import TransparentColorSelector
class ValueSelectBox(MessageBoxBase):
    """ Custom message box """

    def __init__(self, parent=None, title="Set aspect ratio",allowed_min=None,allowed_max=None,current=None):
        super().__init__(parent)
        if allowed_min is not None and allowed_max is not None:
            if allowed_min > allowed_max:
                raise ValueError("allowed_min must be less than allowed_max")
        #print(allowed_min,allowed_max,current)

        self.title_label = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.title_label)

        validator=QDoubleValidator(allowed_min,allowed_max,2)
        self.value_edit=LineEdit(self)
        self.value_edit.setValidator(validator)
        self.value_edit.setClearButtonEnabled(True)
        self.value_edit.textChanged.connect(self.__validate_value)
        if current is not None:
            self.__set_value(current)
        else:
            self.yesButton.setDisabled(True)
        if allowed_min is not None and allowed_max is not None:
            self.value_edit.setPlaceholderText("{:.2f}~{:.2f}".format(allowed_min,allowed_max))
        elif allowed_min is not None and allowed_max is None:
            self.value_edit.setPlaceholderText(">{:.2f}".format(allowed_min))
        elif allowed_min is None and allowed_max is not None:
            self.value_edit.setPlaceholderText("<{:.2f}".format(allowed_max))
        else:
            self.value_edit.setPlaceholderText("input value here")

        if allowed_min is not None or allowed_max is not None or current is not None:
            self.tag_button=DropDownToolButton(self)
            self.tag_button.setIcon(FluentIcon.TAG)
            self.tag_menu=RoundMenu(self)
            if current is not None:
                current_action=Action("current value ({:.2f})".format(current))
                current_action.triggered.connect(lambda: self.__set_value(current))
                self.tag_menu.addAction(current_action)
            if allowed_min is not None:
                min_action=Action("min value ({:.2f})".format(allowed_min))
                min_action.triggered.connect(lambda: self.__set_value(allowed_min))
                self.tag_menu.addAction(min_action)
            if allowed_max is not None:
                max_action=Action("max value ({:.2f})".format(allowed_max))
                max_action.triggered.connect(lambda: self.__set_value(allowed_max))
                self.tag_menu.addAction(max_action)
            self.tag_button.setMenu(self.tag_menu)
            Hlayout=QHBoxLayout()
            Hlayout.addWidget(self.value_edit)
            Hlayout.addWidget(self.tag_button)
            self.viewLayout.addLayout(Hlayout)
        else:
            self.viewLayout.addLayout(self.value_edit)

        # change the text of button
        self.yesButton.setText('Confirm')
        self.cancelButton.setText('Cancel')

        self.widget.setMinimumWidth(400)

        # self.hideYesButton()
    
    def __set_value(self,value):
        self.value_edit.setText("{:.2f}".format(value))
        self.__validate_value("")

    def __validate_value(self, text):
        self.yesButton.setEnabled(self.value_edit.hasAcceptableInput())
        
class StrSelectBox(MessageBoxBase):
    """ Custom message box """

    def __init__(self, parent=None, title="Set text",default_str=None):
        super().__init__(parent)
        self.title_label = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.title_label)
        self.value_edit=LineEdit(self)
        self.value_edit.setClearButtonEnabled(True)
        if default_str is not None:
            self.value_edit.setText(default_str)
        else:
            self.yesButton.setDisabled(True)
        self.viewLayout.addWidget(self.value_edit)
        # change the text of button
        self.yesButton.setText('Confirm')
        self.cancelButton.setText('Cancel')
        self.widget.setMinimumWidth(400)

class LimitedStrSelectBox(StrSelectBox):

    def __init__(self, parent=None, title="Set text",allowed_strs=None):
        super().__init__(parent,title,allowed_strs[-1])
        self.allowed_strs=allowed_strs
        self.value_edit.textChanged.connect(self.__validate_value)
    
    def __validate_value(self, text):
        self.yesButton.setEnabled(self.value_edit.text() in self.allowed_strs)

class ItemSelectBox(MessageBoxBase):
    """ Custom message box """

    def __init__(self, parent=None, title="Set text",items=None,current_index=-1):
        super().__init__(parent)
        self.items=items
        self.title_label = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.title_label)
        self.com_box=EditableComboBox(self)
        self.com_box.addItems(items)
        self.com_box.setCurrentIndex(current_index)
        self.completer = QCompleter(items, self)
        self.com_box.setCompleter(self.completer)
        self.com_box.currentTextChanged.connect(self.__validate_value)
        self.viewLayout.addWidget(self.com_box)
        # change the text of button
        self.yesButton.setText('Confirm')
        self.cancelButton.setText('Cancel')
        self.widget.setMinimumWidth(400)

    def __validate_value(self):
        self.yesButton.setEnabled(self.com_box.currentText() in self.items)

    def current_text(self):
        return self.com_box.currentText()

class RemovableTableWidget(TableWidget):

    selected=pyqtSignal(QTableWidgetItem)
    
    def __init__(self, parent=None,show_row_index=False,resize_columns_to_contents=True):
        super().__init__(parent)
        self.setBorderVisible(True)
        self.setBorderRadius(8)
        self.setWordWrap(False)
        self.itemClicked.connect(self.__on_item_clicked)
        self.current_item=None
        self.show_row_index=show_row_index
        self.resize_columns_to_contents=resize_columns_to_contents
    
    def __on_item_clicked(self, item):
        self.current_item=item
        self.command_bar=CommandBarView(self)
        select_action=Action(FluentIcon.ACCEPT, 'Select')
        select_action.triggered.connect(self.on_item_selected_clicked)
        self.command_bar.addAction(select_action)
        edit_action=Action(FluentIcon.EDIT, 'Rename')
        edit_action.triggered.connect(self.on_edit_row_clicked)
        self.command_bar.addAction(edit_action)
        if item.row()>0:  
            move_up_action=Action(FluentIcon.UP, 'Move up')
            move_up_action.triggered.connect(self.on_move_up_row_clicked)
            self.command_bar.addAction(move_up_action) 
        if item.row()<self.rowCount()-1: 
            move_down_action=Action(FluentIcon.DOWN, 'Move down')
            move_down_action.triggered.connect(self.on_move_down_row_clicked)
            self.command_bar.addAction(move_down_action)
        delete_action=Action(FluentIcon.DELETE, 'Delete')
        delete_action.triggered.connect(self.on_delete_row_clicked)
        self.command_bar.addAction(delete_action)  
        self.command_bar.resizeToSuitableWidth()
        Flyout.make(self.command_bar, QCursor.pos(), self, FlyoutAnimationType.FADE_IN)
    
    def on_delete_row_clicked(self):
        if self.current_item is not None:
            self.removeRow(self.current_item.row())
            self.current_item=None
            self.clearSelection()
            self.command_bar.close()
    
    def on_move_up_row_clicked(self):
        if self.current_item is not None:
            for j in range(self.columnCount()):
                temple=self.item(self.current_item.row(),j).text()
                self.item(self.current_item.row(),j).setText(self.item(self.current_item.row()-1,j).text())
                self.item(self.current_item.row()-1,j).setText(temple)
            self.current_item=None
            self.clearSelection()
            self.command_bar.close()
    
    def on_move_down_row_clicked(self):
        if self.current_item is not None:
            for j in range(self.columnCount()):
                temple=self.item(self.current_item.row(),j).text()
                self.item(self.current_item.row(),j).setText(self.item(self.current_item.row()+1,j).text())
                self.item(self.current_item.row()+1,j).setText(temple)
            self.current_item=None
            self.clearSelection()
            self.command_bar.close()

    def on_item_selected_clicked(self):
        if self.current_item is not None:
            self.selected.emit(self.item(self.current_item.row(),0))
            self.command_bar.close()

    def on_edit_row_clicked(self):
        if self.current_item is not None:
            self.editItem(self.item(self.current_item.row(),0))
            self.command_bar.close()

    def collect_items(self):
        items=[]
        for i in range(self.rowCount()):
            item=[]
            for j in range(self.columnCount()):
                item.append(self.item(i,j).text())
            items.append(item)
        return items

    def set_data(self,data,labels=None):
        num_rows=len(data)
        num_cols=len(data[0])
        self.setRowCount(num_rows)
        self.setColumnCount(num_cols)
        for i, songInfo in enumerate(data):
            for j in range(num_cols):
                self.setItem(i, j, QTableWidgetItem(songInfo[j]))
        if not self.show_row_index:
            self.verticalHeader().hide()
        if self.resize_columns_to_contents:
            self.resizeColumnsToContents()
        if labels is not None:
            self.setHorizontalHeaderLabels(labels)

class ItemEditBox(MessageBoxBase):
    """ Custom message box """

    def __init__(self, parent=None, title="Set text",min_width=400,show_row_index=False,resize_columns_to_contents=True):
        super().__init__(parent)
        self.title_label = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.title_label)
        self.yesButton.setText('Confirm')
        self.cancelButton.setText('Cancel')
        self.tableView = RemovableTableWidget(self,show_row_index,resize_columns_to_contents)
        self.viewLayout.addWidget(self.tableView)
        self.widget.setMinimumWidth(min_width)
        self.selected_row=None
        self.tableView.selected.connect(self.on_item_selected)

    def set_data(self,data,labels):
        self.data=data
        self.tableView.set_data(data,labels)

    def on_item_selected(self,item):        
        self.accept()
        self.selected_row=item.row()
        self.accepted.emit()

    def accept(self) -> None:
        self.data=self.tableView.collect_items()
        return super().accept()

class NewAverageLineBox(MessageBoxBase):
    """ Custom message box """

    def __init__(self,num_data,existed_values, parent=None):
        super().__init__(parent)
        self.num_data=num_data
        self.existed_values=existed_values
        self.title_label = SubtitleLabel("Creative new average line", self)
        self.viewLayout.addWidget(self.title_label)
        self.yesButton.setText('Confirm')
        self.cancelButton.setText('Cancel')
        self.yesButton.setDisabled(True)
        self.value_edit=LineEdit(self)
        self.value_edit.setClearButtonEnabled(True)
        self.value_edit.textChanged.connect(self.__validate_value)
        self.value_edit.setPlaceholderText("average days")
        self.value_edit.setValidator(QIntValidator(1, num_data,self.value_edit))
        self.text_color_layout=QHBoxLayout()
        self.text_color_layout.addWidget(self.value_edit)
        self.color_selector=TransparentColorSelector(parent=self)
        self.color_selector.setFixedHeight(35)
        self.text_color_layout.addWidget(self.color_selector)
        self.viewLayout.addLayout(self.text_color_layout)
        

    def __validate_value(self, text):
        if self.value_edit.hasAcceptableInput():
            if int(text) in self.existed_values:
                self.yesButton.setDisabled(True)
                self.title_label.setText("Average Line existed")
            else:
                self.yesButton.setDisabled(False)
                self.title_label.setText("Creative new average line")

def select_value(parent=None, title="Set aspect ratio",allowed_min=0.1,allowed_max=100,current=50):
    """ Custom message box """
    msg = ValueSelectBox(parent,title,allowed_min,allowed_max,current)
    if msg.exec():
        return float(msg.value_edit.text())
    else:
        return None

def select_str(parent=None, title="Select str",default_str=None):
    """ Custom message box """
    msg = StrSelectBox(parent,title,default_str)
    if msg.exec():
        return msg.value_edit.text()
    else:
        return None

def select_limited_str(parent=None, title="Select str",allowed_strs=None):
    """ Custom message box """
    msg = LimitedStrSelectBox(parent,title,allowed_strs)
    if msg.exec():
        return msg.value_edit.text()
    else:
        return None

def edit_items(parent,items,label, title="Edit item",min_width=400,show_row_index=False,resize_columns_to_contents=True):
    """ Custom message box """
    msg = ItemEditBox(parent,title,min_width,show_row_index,resize_columns_to_contents)
    if len(label) != len(items[0]):
        raise ValueError("label must have the same length as items")
    msg.set_data(items,label)
    if msg.exec():
        return msg.data,msg.selected_row
    else:
        return None

def select_item(parent,items,title="Select item",current_index=-1):
    """ Custom message box """
    msg = ItemSelectBox(parent,title,items,current_index)
    if msg.exec():
        return msg.current_text()
    else:
        return None
    
def confirmation_dialog(parent,title,content):
    w = MessageBox(title, content, parent)
    if w.exec():
        return True
    else:
        return False