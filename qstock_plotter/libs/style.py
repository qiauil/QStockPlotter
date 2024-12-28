#from pyqtgraph import QtGui
from typing import Any
from PyQt6 import QtGui
from PyQt6.QtWidgets import QWidget
#from dataclasses import dataclass,field
from .helpers import *
from qfluentwidgets import StyleSheetBase, Theme, qconfig,FluentIconBase,getIconColor,isDarkTheme
from enum import Enum

LIGHT_BACKGROUND_COLOR=QtGui.QColor(251,251,251)
DARK_BACKGROUND_COLOR=QtGui.QColor(30,30,30)

def default_style_configs() -> ConfigurationsHandler:
    configs_handler = ConfigurationsHandler()
    configs_handler.add_config_item("positive_color",
                                        default_value=(254, 109, 115),
                                        value_type=tuple,
                                        in_func=lambda x,other_config:tuple_to_color(x),out_func=lambda x,other_config:color_to_rbg_tuple(x),
                                        description="color of the positive bars")
    configs_handler.add_config_item("volume_color",
                                        default_value=(254, 109, 115),
                                        value_type=tuple,
                                        in_func=lambda x,other_config:tuple_to_color(x),out_func=lambda x,other_config:color_to_rbg_tuple(x),
                                        description="color of the positive bars")
    configs_handler.add_config_item("negative_color",
                                        default_value=(23, 195, 178),
                                        value_type=tuple,
                                        in_func=lambda x,other_config:tuple_to_color(x),out_func=lambda x,other_config:color_to_rbg_tuple(x),
                                        description="color of the negative bars")
    configs_handler.add_config_item("bar_width",
                                        default_value=0.3,
                                        value_type=float,
                                        description="width of the bars,the distance between two bars is 1")
    configs_handler.add_config_item("shadow_width",
                                        default_value=0.03,
                                        value_type=float,
                                        description="width of the shadowline,the distance between two shadowlines is 1")
    configs_handler.add_config_item("line_width",
                                        default_value=2.0,
                                        value_type=float,
                                        description="width of other lines, like average line. Note that the unit here is pixel")
    configs_handler.add_config_item("average_line_color",
                                    default_value={
                                         5:(76, 201, 240),
                                        20:(67, 97, 238),
                                        60:(58, 12, 163),
                                        120:(114, 9, 183),
                                        250:(247, 37, 133)
                                    },
                                    value_type=dict,
                                    in_func=lambda x,other_config:{key_i:tuple_to_color(x[key_i]) for key_i in x.keys()},
                                    out_func=lambda x,other_config:{key_i:color_to_rbg_tuple(x[key_i]) for key_i in x.keys()},
                                    description="color of the average lines")
    return configs_handler

def make_style(style_yaml_file="",**kwargs):
    configs_handler=default_style_configs()
    if style_yaml_file != "":
            configs_handler.set_config_items_from_yaml(style_yaml_file)
    configs_handler.set_config_items(**kwargs)
    return configs_handler.configs()


class StyleSheet(StyleSheetBase, Enum):
    """ Style sheet  """
    NAVIGATION_VIEW_INTERFACE = "navigation_view_interface"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return project_path_qfile()+"resources/qss/"+theme.value.lower()+"/"+self.value+".qss"

class QStockIcon(FluentIconBase, Enum):
    """ Fluent icon """

    CHEVRON_LEFT = "ChevronLeft"
    
    def path(self, theme=Theme.AUTO):
        return project_path_qfile()+"resources/icons/"+f'{self.value}_{getIconColor(theme)}.svg'

def set_background_with_theme(widget:QWidget, theme=None):
    def set_background_color(color):
        palette = widget.palette()
        palette.setColor(widget.backgroundRole(), color)
        widget.setPalette(palette)

    if theme == Theme.DARK:
        set_background_color(DARK_BACKGROUND_COLOR)
    elif theme == Theme.LIGHT:
        set_background_color(LIGHT_BACKGROUND_COLOR)
    else:
        if isDarkTheme():
            set_background_color(DARK_BACKGROUND_COLOR)
        else:
            set_background_color(LIGHT_BACKGROUND_COLOR)

DEFAULT_STYLE=make_style()