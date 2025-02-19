import pandas as pd
from abc import *
from typing import Union
from dataclasses import dataclass,field
from copy import deepcopy

class ChildDataFrame():
    """
    A class representing a child DataFrame.

    Attributes:
        data_frame (pd.DataFrame): The parent DataFrame.
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

    def __init__(self, data_frame: pd.DataFrame, data_keys: Union[str, list], max_y_key=None, min_y_key=None, x_label_key=None) -> None:
        """
        Initialize the DataHandler object.

        Args:
            data_frame (pd.DataFrame): The parent DataFrame containing the data.
            data_keys (Union[str, list]): The key(s) to access the data in the parent DataFrame.
            max_y_key (str, optional): The key to access the maximum y-value data. Defaults to None.
            min_y_key (str, optional): The key to access the minimum y-value data. Defaults to None.
            x_label_key (str, optional): The key to access the x-label data. Defaults to None.
        """
        data_keys = data_keys if isinstance(data_keys, list) else [data_keys]
        self.data_keys = deepcopy(data_keys)
        if max_y_key is not None:
            if max_y_key not in data_keys:
                data_keys.append(max_y_key)
        else:
            max_y_key = data_keys[0]
        self.max_y_key = max_y_key
        if min_y_key is not None:
            if min_y_key not in data_keys:
                data_keys.append(min_y_key)
        else:
            min_y_key = data_keys[0]
        self.min_y_key = min_y_key
        x_label_key = x_label_key if x_label_key is not None else "date"
        if x_label_key not in data_keys:
            data_keys.append(x_label_key)
        self.data_frame = data_frame[data_keys]
        print(f"Data keys: {data_keys}")
        print("self.data_keys:")
        print(self.data_keys)
        self.x_ticks : dict = {i: str(self.data_frame[x_label_key][i]) for i in self.data_frame.index}
        self.__index_start = self.get_min_x()

    def get_min_x(self):
        """
        Returns the minimum x-value in the parent DataFrame.

        Returns:
            int: The minimum x-value.

        """
        return self.data_frame.index[0]

    def get_max_x(self):
        """
        Returns the maximum x-value in the parent DataFrame.

        Returns:
            int: The maximum x-value.

        """
        return self.data_frame.index[-1]

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
        return pd.to_numeric(self.data_frame.loc[x_start:x_end, self.min_y_key]).min(), pd.to_numeric(self.data_frame.loc[x_start:x_end, self.max_y_key]).max()

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
        return len(self.data_frame)

    def __getitem__(self, idx):
        """
        Returns a tuple of data values at the given index.

        Args:
            idx (int): The index.

        Returns:
            tuple: A tuple containing the index value and data values.

        """

        return tuple([self.data_frame.index[idx]]) + tuple(pd.to_numeric(self.data_frame[key][self.__index_start + idx],errors='coerce') for key in self.data_keys)

class PricesDataFrame(ChildDataFrame):
    """
    A class representing a DataFrame containing prices data.

    Parameters:
    data_frame (pd.DataFrame): The parent DataFrame containing the prices data.
    """

    def __init__(self, data_frame: pd.DataFrame):
        super().__init__(data_frame, data_keys=["open","close","high","low"],
                         max_y_key="high",
                         min_y_key="low",
                         x_label_key="date")

class VolumeDataFrame(ChildDataFrame):
    """
    A class representing a volume data frame.

    This class inherits from the ChildDataFrame class and provides additional functionality
    for handling volume data.

    Args:
        data_frame (pd.DataFrame): The parent data frame from which the volume data frame is derived.

    Attributes:
        data_keys (list): A list of data keys for the volume data.
        x_label_key (str): The key for the x-axis label in the volume data frame.

    """

    def __init__(self, data_frame: pd.DataFrame):
        super().__init__(data_frame, data_keys=["volume"], x_label_key="date")

@dataclass
class TradeData:
    prices:PricesDataFrame
    volume:VolumeDataFrame

class DataHandler():

    def __init__(self):
        self.day_data:TradeData=None
        self.week_data:TradeData=None
        self.month_data:TradeData=None

    def save(self, hdf5_path):
        for key,data in zip(["day_data","week_data","month_data"],[self.day_data,self.week_data,self.month_data]):
            price=data.prices.data_frame
            volume=data.volume.data_frame
            volume=volume.drop(columns=['date'])
            df=price.join(volume)
            df.to_hdf(hdf5_path,key=key)

    def load(self, hdf5_path):
        #self.__df_day = pd.read_hdf(hdf5_path, key="day_data")
        #self.__df_week = pd.read_hdf(hdf5_path, key="week_data")
        #self.__df_month = pd.read_hdf(hdf5_path, key="month_data")
        self.day_data=self._load_data(hdf5_path,"day_data")
        self.week_data=self._load_data(hdf5_path,"week_data")
        self.month_data=self._load_data(hdf5_path,"month_data")
    
    def _load_data(self, path, key):
        try:
            df=pd.read_hdf(path,key=key)
        except Exception as e:
            print(f"Error loading data from {path} with key {key}: {e}")
            return None
        return TradeData(PricesDataFrame(df),VolumeDataFrame(df))

class HDF5Handler(DataHandler):
    """
    A class that handles candlestick data from an HDF5 file.

    Attributes:
        day_data (TradeData): Candlestick data for daily intervals.
        week_data (TradeData): Candlestick data for weekly intervals.
        month_data (TradeData): Candlestick data for monthly intervals.

    Methods:
        __init__(hdf5_path): Initializes the HDF5Handler object.

    """

    def __init__(self, hdf5_path:str) -> None:
        super().__init__()
        self.load(hdf5_path)

