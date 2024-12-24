import pandas as pd
from abc import *
from typing import Union
from dataclasses import dataclass,field

class ChildDataFrame():
    """
    A class representing a child DataFrame.

    Attributes:
        parent_df (pd.DataFrame): The parent DataFrame.
        data_keys (list): The key(s) of the data column(s) in the parent DataFrame.
        max_y_key (str): The key of the maximum y-value column.
        min_y_key (str): The key of the minimum y-value column.
        x_ticks (dict): A dictionary mapping index values to x-labels.
        __index_start (int): The starting index of the child DataFrame.

    Methods:
        get_min_x(): Returns the minimum x-value in the parent DataFrame.
        get_max_x(): Returns the maximum x-value in the parent DataFrame.
        get_local_range(x_start, x_end): Returns the local range of y-values between x_start and x_end.
        get_x_ticks(): Returns the x-ticks dictionary.
        __len__(): Returns the length of the child DataFrame.
        __getitem__(idx): Returns a tuple of data values at the given index.

    """

    def __init__(self, parent_df: pd.DataFrame, data_keys: Union[str, list], max_y_key=None, min_y_key=None, x_label_key=None) -> None:
        """
        Initialize the DataHandler object.

        Args:
            parent_df (pd.DataFrame): The parent DataFrame containing the data.
            data_keys (Union[str, list]): The key(s) to access the data in the parent DataFrame.
            max_y_key (str, optional): The key to access the maximum y-value data. Defaults to None.
            min_y_key (str, optional): The key to access the minimum y-value data. Defaults to None.
            x_label_key (str, optional): The key to access the x-label data. Defaults to None.
        """
        self.parent_df = parent_df
        self.data_keys = data_keys if isinstance(data_keys, list) else [data_keys]
        self.max_y_key = max_y_key if max_y_key is not None else data_keys[0]
        self.min_y_key = min_y_key if min_y_key is not None else data_keys[0]
        x_label_key = x_label_key if x_label_key is not None else "date"
        self.x_ticks : dict = {i: str(self.parent_df[x_label_key][i]) for i in self.parent_df.index}
        self.__index_start = self.get_min_x()

    def get_min_x(self):
        """
        Returns the minimum x-value in the parent DataFrame.

        Returns:
            int: The minimum x-value.

        """
        return self.parent_df.index[0]

    def get_max_x(self):
        """
        Returns the maximum x-value in the parent DataFrame.

        Returns:
            int: The maximum x-value.

        """
        return self.parent_df.index[-1]

    def get_local_range(self, x_start, x_end):
        """
        Returns the local range of y-values between x_start and x_end.

        Args:
            x_start (int): The starting x-value.
            x_end (int): The ending x-value.

        Returns:
            tuple: A tuple containing the minimum and maximum y-values.

        """
        x_start = int(x_start)
        x_end = int(x_end)
        return pd.to_numeric(self.parent_df.loc[x_start:x_end, self.min_y_key]).min(), pd.to_numeric(self.parent_df.loc[x_start:x_end, self.max_y_key]).max()

    def get_x_ticks(self):
        """
        Returns the x-ticks dictionary.

        Returns:
            dict: A dictionary mapping index values to x-labels.

        """
        return self.x_ticks

    def __len__(self):
        """
        Returns the length of the child DataFrame.

        Returns:
            int: The length of the child DataFrame.

        """
        return len(self.parent_df)

    def __getitem__(self, idx):
        """
        Returns a tuple of data values at the given index.

        Args:
            idx (int): The index.

        Returns:
            tuple: A tuple containing the index value and data values.

        """

        return tuple([self.parent_df.index[idx]]) + tuple(pd.to_numeric(self.parent_df[key][self.__index_start + idx],errors='coerce') for key in self.data_keys)

class PricesDataFrame(ChildDataFrame):
    """
    A class representing a DataFrame containing prices data.

    Parameters:
    parent_df (pd.DataFrame): The parent DataFrame containing the prices data.
    """

    def __init__(self, parent_df: pd.DataFrame):
        super().__init__(parent_df, data_keys=["open","close","high","low"],
                         max_y_key="high",
                         min_y_key="low",
                         x_label_key="date")

class VolumeDataFrame(ChildDataFrame):
    """
    A class representing a volume data frame.

    This class inherits from the ChildDataFrame class and provides additional functionality
    for handling volume data.

    Args:
        parent_df (pd.DataFrame): The parent data frame from which the volume data frame is derived.

    Attributes:
        data_keys (list): A list of data keys for the volume data.
        x_label_key (str): The key for the x-axis label in the volume data frame.

    """

    def __init__(self, parent_df: pd.DataFrame):
        super().__init__(parent_df, data_keys=["volume"], x_label_key="date")

@dataclass
class TradeData:
    prices:PricesDataFrame
    volume:VolumeDataFrame

class HandlerCandlestickHDF5():
    """
    A class that handles candlestick data from an HDF5 file.

    Attributes:
        day_data (TradeData): Candlestick data for daily intervals.
        week_data (TradeData): Candlestick data for weekly intervals.
        month_data (TradeData): Candlestick data for monthly intervals.

    Methods:
        __init__(hdf5_path): Initializes the HandlerCandlestickHDF5 object.

    """

    def __init__(self, hdf5_path) -> None:
        self.__df_day = pd.read_hdf(hdf5_path, key="day_data")
        self.__df_week = pd.read_hdf(hdf5_path, key="week_data")
        self.__df_month = pd.read_hdf(hdf5_path, key="month_data")
        self.day_data = TradeData(PricesDataFrame(self.__df_day), VolumeDataFrame(self.__df_day))
        self.week_data = TradeData(PricesDataFrame(self.__df_week), VolumeDataFrame(self.__df_week))
        self.month_data = TradeData(PricesDataFrame(self.__df_month), VolumeDataFrame(self.__df_month))
