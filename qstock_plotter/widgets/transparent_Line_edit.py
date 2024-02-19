from PyQt6.QtCore import QEvent, QObject
from qfluentwidgets import TransparentPushButton,LineEdit
from PyQt6.QtWidgets import QWidget,QVBoxLayout
from PyQt6.QtCore import pyqtSignal,Qt


class TransparentLineEdit(QWidget):
    
    sigTextEditFinished=pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.main_layout=QVBoxLayout()
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        self.line_edit=LineEdit(parent=self)
        self.push_button=TransparentPushButton(parent=self)
        self.main_layout.addWidget(self.line_edit)
        self.main_layout.addWidget(self.push_button)
        self.line_edit.setVisible(False)
        self.setLayout(self.main_layout)
        self.push_button.clicked.connect(self.__show_line_edit)
        self.line_edit.installEventFilter(self)
    
    def set_text(self, text):
        self.line_edit.setText(text)
        self.push_button.setText(text)
    
    def get_text(self):
        return self.line_edit.text()
    
    def __show_line_edit(self):
        self.push_button.setVisible(False)
        self.line_edit.setVisible(True)
        self.line_edit.setFocus()
    
    def __finish_edit(self):
        self.sigTextEditFinished.emit()
        self.push_button.setText(self.line_edit.text())
        self.line_edit.setVisible(False)
        self.push_button.setVisible(True)
    
    def eventFilter(self, a0: QObject, a1: QEvent) -> bool:
        if a0==self.line_edit: 
            if a1.type()==QEvent.Type.FocusOut:
                self.__finish_edit()
                return False
            if a1.type()==QEvent.Type.KeyPress:
                if a1.key() in (Qt.Key.Key_Enter,Qt.Key.Key_Return):
                    self.__finish_edit()
                    return False
                elif a1.key()==Qt.Key.Key_Escape:
                    self.line_edit.setVisible(False)
                    self.push_button.setVisible(True)
                    return False
        return super().eventFilter(a0, a1)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    if __name__ == "__main__":
        app = QApplication(sys.argv)
        window=QWidget()
        widget=TransparentLineEdit()
        window.setLayout(QVBoxLayout())
        window.layout().addWidget(widget)
        window.show()
        sys.exit(app.exec())