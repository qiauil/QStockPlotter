from qstock_plotter import QStockPlotter
from qstock_plotter.libs.data_handler import *
from qstock_plotter.libs.plot_item import *
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import setTheme,setThemeColor,Theme
import sys

app = QApplication(sys.argv)
app.setApplicationName("QStockPlotter")
sample_stock_data=HandlerCandlestickHDF5("./sample_stock_data.h5")
graph_item=get_plot_item(sample_stock_data.month_data.prices) 
#graph_item=get_plot_item(sample_stock_data.day_data.volume) #for volume
widget=QStockPlotter()
widget.show()
widget.add_main_item(graph_item,x_ticks=graph_item.get_x_ticks())
#widget.main_plotter.update_plot(x_loc=widget.main_plotter.x_end-5, x_range=5) # move to the end
#setTheme(Theme.DARK) #switch to dark theme
#setThemeColor("#0065d5") #change the theme color
sys.exit(app.exec())