from qfluentwidgets import ToggleButton,isDarkTheme,FluentIconBase,qconfig,FluentStyleSheet
from qfluentwidgets.common.overload import singledispatchmethod
from PyQt6.QtGui import QColor,QIcon
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from typing import Union
from enum import Enum
from ..libs.helpers import color_to_rbg_tuple

# modified from pyqtgraph.style_sheet
class CustomThemeColor(Enum):
    """ Theme color type """

    PRIMARY = "ThemeColorPrimary"
    DARK_1 = "ThemeColorDark1"
    DARK_2 = "ThemeColorDark2"
    DARK_3 = "ThemeColorDark3"
    LIGHT_1 = "ThemeColorLight1"
    LIGHT_2 = "ThemeColorLight2"
    LIGHT_3 = "ThemeColorLight3"

    def name(self):
        return self.color().name()

    def color(self,color):

        # transform color into hsv space
        h, s, v, _ = color.getHsvF()

        if isDarkTheme():
            s *= 0.84
            v = 1
            if self == self.DARK_1:
                v *= 0.9
            elif self == self.DARK_2:
                s *= 0.977
                v *= 0.82
            elif self == self.DARK_3:
                s *= 0.95
                v *= 0.7
            elif self == self.LIGHT_1:
                s *= 0.92
            elif self == self.LIGHT_2:
                s *= 0.78
            elif self == self.LIGHT_3:
                s *= 0.65
        else:
            if self == self.DARK_1:
                v *= 0.75
            elif self == self.DARK_2:
                s *= 1.05
                v *= 0.5
            elif self == self.DARK_3:
                s *= 1.1
                v *= 0.4
            elif self == self.LIGHT_1:
                v *= 1.05
            elif self == self.LIGHT_2:
                s *= 0.75
                v *= 1.05
            elif self == self.LIGHT_3:
                s *= 0.65
                v *= 1.05

        return QColor.fromHsvF(h, min(s, 1), min(v, 1))

class ColorfulToggleButton(ToggleButton):
    """
    A custom toggle button with colorful styling.

    Inherits from ToggleButton class.

    Attributes:
        color (QColor): The color of the button.

    Methods:
        set_color(): Sets the color of the button based on the current theme.
    """
    
    def set_color(self):
        """
        Sets the color of the button based on the current theme.
        """
        if self.color is not None:
            style_sheet = "ColorfulToggleButton:checked {background-color: rgb"\
                +"{}".format(color_to_rbg_tuple(CustomThemeColor.PRIMARY.color(self.color)))\
                    +";border: 1px solid rgb"+"{}".format(color_to_rbg_tuple(CustomThemeColor.LIGHT_1.color(self.color)))\
                        +";border-bottom: 1px solid rgb"+"{}".format(color_to_rbg_tuple(CustomThemeColor.DARK_1.color(self.color)))\
                            +";}"
            style_sheet += "ColorfulToggleButton:checked:hover {background-color: rgb"\
                +"{}".format(color_to_rbg_tuple(CustomThemeColor.LIGHT_1.color(self.color)))\
                    +";border: 1px solid rgb"+"{}".format(color_to_rbg_tuple(CustomThemeColor.LIGHT_2.color(self.color)))\
                        +";border-bottom: 1px solid rgb"+"{}".format(color_to_rbg_tuple(CustomThemeColor.DARK_1.color(self.color)))\
                            +";}"
            style_sheet += "ColorfulToggleButton:checked:pressed {background-color: rgb"\
                +"{}".format(color_to_rbg_tuple(CustomThemeColor.LIGHT_3.color(self.color)))\
                +";border: 1px solid rgb"\
                    +"{}".format(color_to_rbg_tuple(CustomThemeColor.LIGHT_3.color(self.color)))\
                        +";}"
            self.setStyleSheet(
                FluentStyleSheet.BUTTON.content()
                +
                style_sheet)

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.color=None
        qconfig.themeChangedFinished.connect(self.set_color)

    @__init__.register
    def _(self, color:QColor, text: str, parent: QWidget = None, icon: Union[QIcon, FluentIconBase, str] = None):
        self.__init__(parent)
        self.setText(text)
        self.setIcon(icon)
        self.color=color
        self.set_color()

    @__init__.register
    def _(self, icon: QIcon, color:QColor, text: str, parent: QWidget = None):
        self.__init__(color, text, parent, icon)

    @__init__.register
    def _(self, icon: FluentIconBase,color:QColor, text: str, parent: QWidget = None):
        self.__init__(color, text, parent, icon)