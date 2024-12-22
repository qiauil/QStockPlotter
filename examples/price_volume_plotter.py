from qstock_plotter import PriceVolumePlotter
from qstock_plotter.libs.data_handler import *
from qstock_plotter.libs.plot_item import *
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import setTheme,setThemeColor,Theme
import sys

app = QApplication(sys.argv)
app.setApplicationName("QStockPlotter")
sample_stock_data=HandlerCandlestickHDF5("./sample_stock_data.h5")
widget=PriceVolumePlotter()
widget.show()
widget.plot_price_volume(sample_stock_data.month_data.prices,sample_stock_data.month_data.volume)
#setTheme(Theme.DARK) #switch to dark theme
#setThemeColor("#0065d5") #change the theme color
sys.exit(app.exec())