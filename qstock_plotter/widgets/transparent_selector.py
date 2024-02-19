from qfluentwidgets import (TransparentDropDownPushButton,Action,FluentIcon,CheckableMenu,ColorDialog,MenuIndicatorType)
from qfluentwidgets.common.icon import toQIcon
from PyQt6.QtGui import QColor,QPixmap,QIcon
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QApplication
import sys

TRADITIONAL_COLORS = {
    "Black":QColor(45, 45, 45),
    "White":QColor(255, 255, 255),
    "Red":QColor(255, 0, 0),
    "Green":QColor(0, 255, 0),
    "Blue":QColor(0, 0, 255),
    "Yellow":QColor(255, 255, 0),
    "Cyan":QColor(0, 255, 255),
    "Magenta":QColor(255, 0, 255),
    "Gray":QColor(128, 128, 128),
    "Dark gray":QColor(64, 64, 64),
    "Light gray":QColor(192, 192, 192),
    "Orange":QColor(255, 165, 0),
    "Purple":QColor(128, 0, 128),
    "Brown":QColor(165, 42, 42),
}

SCIENTIFIC_COLORS={
    "Black":QColor(0, 0, 0),
    "Red":QColor('#FF1F5B'),
    "Blue":QColor('#009ADE'),
    "Yellow":QColor('#FFC61E'),
    "Purple":QColor('#AF58BA'),
    "Orange":QColor('#F28522'),
    "Green":QColor('#00CD6C'),
    "Brown":QColor('#A6761D'),
}

DEFAULT_LINE_WIDTHS = {
    "0.25 pt":0.25*2,
    "0.5 pt":0.5*2,
    "0.75 pt":0.75*2,
    "1 pt":1*2,
    "1.5 pt":1.5*2,
    "2.25 pt":2.25*2,
    "3 pt":3*2,
    "4.5 pt":4.5*2,
    "6 pt":6*2,
}

DEFAULT_DASH_TYPE={
"——————":[],
"——  ——  ":[5,5],
"⋅⋅⋅⋅⋅⋅⋅⋅":[1,1],
"-  ⋅  ":[3,5,1,5],
"-  ⋅  ⋅":[3,5,1,5,1,5],
"————  ":[10,3],
"——   ":[5,10],
"-    ⋅":[3,10,1,10],
"-    ⋅    ⋅":[3,10,1,10,1,10],
"- ⋅ ⋅":[3,1,1,1,1,1],
}
class TransparentSelector(TransparentDropDownPushButton):

    item_selected = pyqtSignal(str)

    def __init__(self, items:dict,allow_custom=True,default_index=0,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_custom=allow_custom
        self.items=items
        self.item_menu_actions=[]
        def generate_item_select_action(item_name):
            item_action=Action(item_name)
            item_action.setCheckable(True)
            item_action.setChecked(False)
            item_action.triggered.connect(lambda:self.on_item_menu_action_clicked(item_action))
            return item_action
        self.item_menu_actions=[
            {"name":item_name,
            "value":value,
             "action":generate_item_select_action(item_name)}
             for item_name,value in self.items.items()]
        if self.allow_custom:
            self.customized_item=None
            self.item_menu_actions.append(
                {"name":"customized",
                    "value":self.customized_item,
                    "action":generate_item_select_action("customized")}
                    )
        self.item_menu_actions[default_index]["action"].setChecked(True)
        self.current_item=self.item_menu_actions[default_index]["value"]
        self.default_item=self.item_menu_actions[default_index]["value"]
        self.item_menu=CheckableMenu(indicatorType=MenuIndicatorType.RADIO)
        self.item_menu.addActions([item["action"] for item in self.item_menu_actions])
        self.setMenu(self.item_menu)
        self.setText(self.item_menu_actions[default_index]["action"].text())
    
    def on_item_menu_action_clicked(self,action,emit=True):
        if self.allow_custom and action.text()=="customized":
            if self.get_custom_item():
                self.current_item=self.customized_item
            else:
                self.set_item(self.current_item)
                return False
        else:
            self.current_item=self.items[action.text()]
        self.setText(action.text())
        if emit:
            self.item_selected.emit(action.text())
        for other_action in self.item_menu_actions:
            other_action["action"].setChecked(False)
        action.setChecked(True)
        return True
    
    def set_item(self,item):
        for action in self.item_menu_actions:
            if action["value"]==item:
                self.on_item_menu_action_clicked(action["action"],emit=False)
                return 0
        if self.allow_custom:
            self.customized_item=item
            self.current_item=item
            action=self.item_menu_actions[-1]["action"]
            self.setText(action.text())
            for other_action in self.item_menu_actions:
                other_action["action"].setChecked(False)
            action.setChecked(True)
            return 1
        else:
            raise ValueError("No such item in the menu")

    def get_value(self,selected_text):
        for action in self.item_menu_actions:
            if action["name"]==selected_text:
                return action["value"]
        raise ValueError("No such item in the menu")

    def get_custom_item(self):
        return True

class TransparentColorSelector(TransparentSelector):

    def __init__(self, color_icon_width=24,color_icon_height=8,colors=SCIENTIFIC_COLORS, *args, **kwargs):
        super().__init__(items=colors, allow_custom=True, *args, **kwargs)
        self.color_icon_width=color_icon_width
        self.color_icon_height=color_icon_height
        for action in self.item_menu_actions[0:-1]:
            action["action"].setIcon(self.__color_icon(colors[action["name"]]))
        self.item_menu_actions[-1]["action"].setIcon(toQIcon(FluentIcon.PALETTE))
        self.setIcon(self.__color_icon(self.current_item))

    def on_item_menu_action_clicked(self, action, emit=True):
        re=super().on_item_menu_action_clicked(action, emit)
        if re:
            self.setIcon(action.icon())
        return re

    def __color_icon(self,color):
        pixmap = QPixmap(self.color_icon_width,self.color_icon_height)
        pixmap.fill(color)
        return QIcon(pixmap)

    def set_item(self, item):
        re = super().set_item(item)
        if re == 1:
            icon=toQIcon(self.__color_icon(item))
            self.setIcon(icon)
            self.item_menu_actions[-1]["action"].setIcon(icon)
        return re

    def get_custom_item(self):
        if self.customized_item is not None:
            default_color=self.customized_item
        else:
            default_color=self.current_item
        w = ColorDialog(default_color, "Select Color", self.window())
        if w.exec():
            self.customized_item=w.color
            self.item_menu_actions[-1]["value"]=self.customized_item
            self.item_menu_actions[-1]["action"].setIcon(self.__color_icon(self.customized_item))
            return True
        else:
            return False    

class TransparentLineWidthSelector(TransparentSelector):

    def __init__(self, *args, **kwargs):
        super().__init__(items=DEFAULT_LINE_WIDTHS,default_index=3, allow_custom=False, *args, **kwargs)

class TransparentDashTypeSelector(TransparentSelector):

    def __init__(self, *args, **kwargs):
        super().__init__(items=DEFAULT_DASH_TYPE,default_index=0, allow_custom=False, *args, **kwargs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = TransparentColorSelector()
    widget.show()
    sys.exit(app.exec())
