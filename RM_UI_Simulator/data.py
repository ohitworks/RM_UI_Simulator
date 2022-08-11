"""
为模拟器提供数据服务。

注意:
  - variables file在全局配置中为绝对路径，工作区配置中为相对(工作区文件夹的)路径
"""
import os
import re
import copy
import typing

import yaml

CONFIG_PATH = os.path.dirname(__file__) + os.path.sep + "config.yml"  # 全局设置路径

# 模块名
MODEL_NAME = __name__.split(".")[0]

# 基础全局设置，用于初始化全局设置
BASE_GLOBAL_CONFIG_DATA = {"variables file": None,  # 上次打开的变量文件
                           "working project path": None,  # 上次所在的项目位置
                           "project folder name": ".py" + MODEL_NAME,  # 局部设置路径
                           "default server port": 5510,  # 默认套接字服务器端口
                           }

# 基础局部设置，用于初始化项目
BASE_LOCAL_CONFIG_DATA = {"build": False,  # 是否已经构建
                          "build_path": "cmake-build",  # 构建目录(相对于项目目录)
                          "cmake_path": "cmake",
                          "c_compiler_path": "",
                          "cxx_compiler_path": "",
                          "inc_files": [],  # 路径为绝对路径
                          "src_files": [],
                          "link_files": [],
                          "project_name": "",
                          "variables file": None,  # 上次打开的变量文件
                          MODEL_NAME + " version": None,  # 版本
                          }

ENABLE_CACHE = True  # 是否使用数据缓存
CACHE = {"global config": None}


def get_local_config_path(working_path):
    """返回项目局部配置文件所在位置"""
    return working_path + "/" + get_global_config()["project folder name"] + "/config.yml"


def update_local_config(working_path, update=None, **kwargs):
    """将 update 和 kwargs 作为更新值写入working_path对应的局部设置"""
    if not update and not kwargs:
        return
    data = get_local_config(working_path)
    if not hasattr(data, "update"):
        raise TypeError("The local config need `update` method.")
    if update:
        data.update(update)
    if kwargs:
        data.update(kwargs)
    write_local_config(working_path, data)


def write_local_config(working_path, config_data):
    """将 config_data 写入working_path对应的局部设置, 此函数自动设置版本"""
    config_data[MODEL_NAME + " version"] = get_variables().get("version")
    with open(get_local_config_path(working_path), "w", encoding="utf-8") as fp:
        yaml.safe_dump(config_data, fp)


def get_local_config(working_path) -> dict:
    """返回项目局部配置"""
    with open(get_local_config_path(working_path), "r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    return data  # 存储格式一定为dict


def has_local_config(path):
    """返回路径是否存在局部配置"""
    name = get_global_config()["project folder name"]  # 项目配置文件夹名
    path = os.path.join(path, name)
    if not os.path.isdir(path):  # 没有项目配置文件
        return False
    path = os.path.join(path, "config.yml")  # 项目配置文件
    return os.path.isfile(path)


def has_global_config():
    """返回是否存在全局设置"""
    return os.path.isfile(CONFIG_PATH)


def init_local_config(working_path):
    """初始化局部设置"""
    d = working_path + "/" + get_global_config()["project folder name"]
    if not os.path.isdir(d):
        # 创建项目文件夹
        os.mkdir(d)
    write_local_config(working_path, BASE_LOCAL_CONFIG_DATA)


def init_global_config():
    """初始化全局设置"""
    write_global_config(BASE_GLOBAL_CONFIG_DATA)


def get_global_config(cache=True):
    """获得全局设置数据"""
    if ENABLE_CACHE and cache and CACHE["global config"] is not None:
        return copy.deepcopy(CACHE["global config"])
    with open(CONFIG_PATH, "r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    if ENABLE_CACHE:
        CACHE["global config"] = copy.deepcopy(data)
    return data


def write_global_config(config_data):
    """将 config_data 写入全局设置"""
    if ENABLE_CACHE:
        CACHE["global config"] = copy.deepcopy(config_data)
    with open(CONFIG_PATH, "w", encoding="utf-8") as fp:
        yaml.safe_dump(config_data, fp)


def update_global_config(update: typing.Optional = None, **kwargs):
    """将 update 和 kwargs 作为更新值写入全局设置"""
    if not update and not kwargs:
        # 没有更新，直接返回
        return
    if not ENABLE_CACHE or CACHE["global config"] is None:  # 这里 cache 就是全局设置
        cache = get_global_config(False)
    else:
        cache = CACHE["global config"]
    if not hasattr(cache, "update"):
        raise TypeError("The global config need `update` method.")
    if update:
        cache.update(update)  # 因为 write_global_config 中执行了copy.deepcopy因此这里无需执行复制
    if kwargs:
        cache.update(kwargs)

    write_global_config(cache)


def get_variables() -> dict:
    """
    获取并返回配置变量文件夹的内容； 若文件无法打开或者序列化失败，则返回空字典
    :return: dict
    """
    try:
        with open(os.path.join(os.path.dirname(__file__), "variables"), "r", encoding="utf-8") as fp:
            text = fp.read()
        variables = dict(re.findall(r'''(\w+) ?= ?['"]?(.*?)['"]?(?: *#.*[^'"])?$''', text, re.M))
    except (FileNotFoundError, PermissionError, AttributeError):
        return {}
    return variables
