from . import c_reader, qtui, data
from .C_platform import *
from .qtui import *

if not data.has_global_config():
    data.init_global_config()

__version__ = data.get_variables().get("version", "读取失败")
