import re
import os
import setuptools
from setuptools.command.install import install

from importlib.util import find_spec


def ask_install_tk(to_install):
    from tkinter import Tk
    from tkinter.messagebox import askyesno
    root = Tk()
    root.withdraw()  # 隐藏主窗口
    root.wm_attributes('-topmost', 1)  # 置顶窗口，为了让弹窗在最顶端
    yes = askyesno("安装错误", "未安装 %s 模块，自动下载安装吗？" % " ,".join(to_install))  # 弹窗
    root.destroy()  # 关闭窗口
    return yes


class CustomInstallCommand(install):
    """Customized setuptools install command"""

    request_modules = {"PyQt5": "PyQt5", "yaml": "pyyaml"}

    def run(self):
        install.run(self)
        to_install = [imp for imp in self.request_modules if not find_spec(imp)]
        if to_install:
            yes = ask_install_tk(to_install)
            if yes:
                import pip
                for mod in to_install:
                    pip.main(["install", self.request_modules[mod], "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])


version = "3.0.0-alpha"


with open(os.path.join(os.path.dirname(__file__), "RM_UI_Simulator", "variables"), "r", encoding="utf-8") as fp:
    text = fp.read()
# Note: 下面这个正则表达式和data文件中的不同与此表达式会保留注释
variables = dict([(i, [v, a]) for i, v, a in re.findall(r'''(\w+) ?= ?['"]?(.*?)['"]?( *#.*[^'"])?$''', text, re.M)])
update = False

v = variables.get(version, (None, None))
if v[1] != version:
    update = True
    variables["version"] = [f"'{version}'", "版本号"]

if update:
    with open("RM_UI_Simulator/variables", "w", encoding="utf-8") as fp:
        for k, (v, a) in sorted(variables.items(), key=lambda x: x[0]):
            if a:
                fp.write(f"{k} = {v}  # {a}\n")
            else:
                fp.write(f"{k} = {v}\n")


setuptools.setup(
    name="RM_UI_Simulator",  # What about "usor" (Ui Simulator Of Robomaster)? "usor" likes "user".
    version=version,
    author="Juntong",
    author_email="jessica_ye2015@sine.com.cn",
    description="UI Simulator of Robomaster",
    python_requires='>=3',
    package_data={
        "RM_UI_Simulator": [
            "variables",
            "C_platform/*/*.c", "C_platform/*/*.h", "C_platform/*/*.lib", "C_platform/*/*.a"]},
    # platforms=["win32"],
    install_requires=["PyQt5", "pyyaml"],
    packages=setuptools.find_packages()
)
