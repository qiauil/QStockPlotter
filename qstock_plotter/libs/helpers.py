import yaml
from PyQt6 import QtGui
import os

def limit_in_range(value, min_value, max_value):
    """
    Limits the given value within the specified range.

    Args:
        value (float): The value to be limited.
        min_value (float): The minimum value of the range.
        max_value (float): The maximum value of the range.

    Returns:
        float: The limited value within the range.
    """
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value

def color_to_rbg_tuple(color: QtGui.QColor) -> tuple:
    """
    Converts a QColor object to an RGB tuple.

    Args:
        color (QtGui.QColor): The QColor object to convert.

    Returns:
        tuple: The RGB tuple representing the color, in the format (red, green, blue).
    """
    return (color.red(), color.green(), color.blue())

def tuple_to_color(color_tuple: tuple) -> QtGui.QColor:
    """
    Converts a tuple of RGB values to a QColor object.

    Args:
        color_tuple (tuple): A tuple containing RGB values.

    Returns:
        QtGui.QColor: A QColor object representing the RGB values.
    """
    return QtGui.QColor(int(color_tuple[0]), int(color_tuple[1]), int(color_tuple[2]))

def project_path():
    """
    Returns the absolute path of the project directory.

    Return: 
        str: The absolute path of the project directory.
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+os.sep

def project_path_qfile():
    """
    Returns the project path with forward slashes instead of backslashes.
    
    Returns:
        str: The project path with forward slashes.
    """
    return project_path().replace("\\","/")

# from foxutils: https://github.com/qiauil/Foxutils/blob/dev/foxutils/helper/coding.py
class GeneralDataClass():
    """
    A general data class that allows dynamic attribute setting and retrieval.
    """

    def __init__(self, generation_dict=None, **kwargs) -> None:
        """
        Initializes a new instance of the GeneralDataClass.

        Args:
            generation_dict (dict): A dictionary containing attribute-value pairs to be set.
            **kwargs: Additional attribute-value pairs to be set.
        """
        if generation_dict is not None:
            for key, value in generation_dict.items():
                self.set(key, value)
        for key, value in kwargs.items():
            self.set(key, value)

    def __len__(self):
        """
        Returns the number of attributes in the GeneralDataClass.

        Returns:
            int: The number of attributes.
        """
        return len(self.__dict__)

    def __getitem__(self, key):
        """
        Retrieves the value of the specified attribute.

        Args:
            key (str): The name of the attribute.

        Returns:
            Any: The value of the attribute.
        """
        return self.__dict__[key]

    def __iter__(self):
        """
        Returns an iterator over the attribute-value pairs of the GeneralDataClass.

        Returns:
            Iterator: An iterator over the attribute-value pairs.
        """
        return iter(self.__dict__.items())

    def keys(self):
        """
        Returns a list of attribute names in the GeneralDataClass.

        Returns:
            list: A list of attribute names.
        """
        return self.__dict__.keys()

    def set(self, key, value):
        """
        Sets the value of the specified attribute.

        Args:
            key (str): The name of the attribute.
            value (Any): The value to be set.
        """
        setattr(self, key, value)

    def set_items(self, **kwargs):
        """
        Sets multiple attribute-value pairs.

        Args:
            **kwargs: Attribute-value pairs to be set.
        """
        for key, value in kwargs.items():
            self.set(key, value)

    def remove(self, *args):
        """
        Removes the specified attributes.

        Args:
            *args: Names of the attributes to be removed.
        """
        for key in args:
            delattr(self, key)

    def add(self, **kwargs):
        """
        Adds additional attribute-value pairs.

        Args:
            **kwargs: Additional attribute-value pairs to be added.
        """
        for k, v in kwargs.items():
            setattr(self, k, v)
            
class ConfigurationsHandler():
    """
    A class that handles configurations for a specific application or module.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance of the ConfigurationsHandler class.
        """
        self.__configs_feature={}
        self.__configs=GeneralDataClass()
        
    def add_config_item(self,name,default_value=None,default_value_func=None,mandatory=False,description="",value_type=None,option=None,in_func=None,out_func=None):
        """
        Adds a new configuration item to the handler.

        Args:
            name (str): The name of the configuration item.
            default_value (Any, optional): The default value for the configuration item. Defaults to None.
            default_value_func (Callable, optional): A function that returns the default value for the configuration item. Defaults to None.
            mandatory (bool, optional): Indicates whether the configuration item is mandatory. Defaults to False.
            description (str, optional): The description of the configuration item. Defaults to "".
            value_type (type, optional): The expected type of the configuration item. Defaults to None.
            option (List[Any], optional): The list of possible values for the configuration item. Defaults to None.
            in_func (Callable, optional): A function to transform the input value of the configuration item. Defaults to None.
            out_func (Callable, optional): A function to transform the output value of the configuration item. Defaults to None.
        """
        if not mandatory and default_value is None and default_value_func is None:
            raise Exception("Default value or default value func must be set for non-mandatory configuration.")
        if mandatory and (default_value is not None or default_value_func is not None):
            raise Exception("Default value or default value func must not be set for mandatory configuration.")
        if default_value is not None and type(default_value)!=value_type:
            raise Exception("Default value must be {}, but find {}.".format(value_type,type(default_value)))
        if option is not None:
            if type(option)!=list:
                raise Exception("Option must be list, but find {}.".format(type(option)))
            if len(option)==0:
                raise Exception("Option must not be empty.")
            for item in option:
                if type(item)!=value_type:
                    raise Exception("Option must be list of {}, but find {}.".format(value_type,type(item)))
        self.__configs_feature[name]={
            "default_value_func":default_value_func, #default_value_func must be a function with one parameter, which is the current configures
            "mandatory":mandatory,
            "description":description,
            "value_type":value_type,
            "option":option,
            "in_func":in_func,
            "out_func":out_func,
            "default_value":default_value,
            "in_func_ran":False,
            "out_func_ran":False
        }
    
    def get_config_features(self,key):
        """
        Retrieves the features of a specific configuration item.

        Args:
            key (str): The name of the configuration item.

        Returns:
            dict: A dictionary containing the features of the configuration item.
        """
        if key not in self.__configs_feature.keys():
            raise Exception("{} is not a supported configuration.".format(key))
        return self.__configs_feature[key]
    
    def set_config_features(self,key,feature):
        """
        Sets the features of a specific configuration item.

        Args:
            key (str): The name of the configuration item.
            feature (dict): A dictionary containing the features of the configuration item.
        """
        self.add_config_item(key,default_value=feature["default_value"],
                             default_value_func=feature["default_value_func"],
                             mandatory=feature["mandatory"],
                             description=feature["description"],
                             value_type=feature["value_type"],
                             option=feature["option"],
                             in_func=feature["in_func"],
                             out_func=feature["out_func"])

    def set_config_items(self,**kwargs):
        """
        Sets the values of multiple configuration items.

        Args:
            kwargs (Any): Keyword arguments representing the configuration items and their values.
        """
        for key in kwargs.keys():
            if key not in self.__configs_feature.keys():
                raise Exception("{} is not a supported configuration.".format(key))
            if self.__configs_feature[key]["value_type"] is not None and type(kwargs[key])!=self.__configs_feature[key]["value_type"]:
                raise Exception("{} must be {}, but find {}.".format(key,self.__configs_feature[key]["value_type"],type(kwargs[key])))
            if self.__configs_feature[key]["option"] is not None and kwargs[key] not in self.__configs_feature[key]["option"]:
                raise Exception("{} must be one of {}, but find {}.".format(key,self.__configs_feature[key]["option"],kwargs[key]))
            self.__configs.set(key,kwargs[key])
            self.__configs_feature[key]["in_func_ran"]=False
            self.__configs_feature[key]["out_func_ran"]=False
    
    def configs(self):
        """
        Retrieves the current configurations.

        Returns:
            GeneralDataClass: An instance of the GeneralDataClass containing the current configurations.
        """
        for key in self.__configs_feature.keys():
            not_set=False
            if not hasattr(self.__configs,key):
                not_set=True
            elif self.__configs[key] is None:
                not_set=True
            if not_set:
                if self.__configs_feature[key]["mandatory"]:
                    raise Exception("Configuration {} is mandatory, but not set.".format(key))
                elif self.__configs_feature[key]["default_value"] is not None:
                    self.__configs.set(key,self.__configs_feature[key]["default_value"])
                    self.__configs_feature[key]["in_func_ran"]=False
                    self.__configs_feature[key]["out_func_ran"]=False
                elif self.__configs_feature[key]["default_value_func"] is not None:
                    self.__configs.set(key,None)        
                else:
                    raise Exception("Configuration {} is not set.".format(key))
        #default_value_func and infunc may depends on other configurations
        for key in self.__configs.keys():
            if self.__configs[key] is None and self.__configs_feature[key]["default_value_func"] is not None:
                self.__configs.set(key,self.__configs_feature[key]["default_value_func"](self.__configs))
                self.__configs_feature[key]["in_func_ran"]=False
                self.__configs_feature[key]["out_func_ran"]=False
        for key in self.__configs_feature.keys():
            if self.__configs_feature[key]["in_func"] is not None and not self.__configs_feature[key]["in_func_ran"]:
                self.__configs.set(key,self.__configs_feature[key]["in_func"](self.__configs[key],self.__configs))
                self.__configs_feature[key]["in_func_ran"]=True
        return self.__configs

    def set_config_items_from_yaml(self,yaml_file):
        """
        Sets the values of configuration items from a YAML file.

        Args:
            yaml_file (str): The path to the YAML file.
        """
        with open(yaml_file,"r") as f:
            yaml_configs=yaml.safe_load(f)
        self.set_config_items(**yaml_configs)
    
    def save_config_items_to_yaml(self,yaml_file,only_optional=False):
        """
        Saves the values of configuration items to a YAML file.

        Args:
            yaml_file (str): The path to the YAML file.
            only_optional (bool, optional): Indicates whether to save only the optional configuration items. Defaults to False.
        """
        config_dict=self.configs().__dict__
        if only_optional:
            output_dict={}
            for key in config_dict.keys():
                if self.__configs_feature[key]["mandatory"]:
                    continue
                output_dict[key]=config_dict[key]    
        else:
            output_dict=config_dict
        for key in output_dict.keys():
            if self.__configs_feature[key]["out_func"] is not None and not self.__configs_feature[key]["out_func_ran"]:
                output_dict[key]=self.__configs_feature[key]["out_func"](self.__configs[key],self.__configs)
                self.__configs_feature[key]["out_func_ran"]=True
        with open(yaml_file,"w") as f:
            yaml.dump(output_dict,f)
    
    def show_config_features(self):
        """
            Displays the features of all configuration items.
        """
        mandatory_configs=[]
        optional_configs=[]
        for key in self.__configs_feature.keys():
            text="    "+str(key)
            texts=[]
            if self.__configs_feature[key]["value_type"] is not None:
                texts.append(str(self.__configs_feature[key]["value_type"].__name__))
            if self.__configs_feature[key]["option"] is not None:
                texts.append("possible option: "+str(self.__configs_feature[key]["option"]))
            if self.__configs_feature[key]["default_value"] is not None:
                texts.append("default value: "+str(self.__configs_feature[key]["default_value"]))
            if len(texts)>0:
                text+=" ("+", ".join(texts)+")"
            text+=": "
            text+=str(self.__configs_feature[key]["description"])
            if self.__configs_feature[key]["mandatory"]:
                mandatory_configs.append(text)
            else:
                optional_configs.append(text)
        print("Mandatory Configuration:")
        for key in mandatory_configs:
            print(key)
        print("")
        print("Optional Configuration:")
        for key in optional_configs:
            print(key)
   
    def show_config_items(self):
        """
            Displays the values of all configuration items.
        """
        for key,value in self.configs().__dict__.items():
            print("{}: {}".format(key,value))
