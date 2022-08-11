"""
调试器
"""
import functools
import typing


class AddDebuggerFunction:
    """
    装饰器，用于设置 Debugger 的特殊函数添加方法。 应该这样"@AddDebuggerFunction.set_register_function(XXX)"使用。
    加这个装饰器是为了在C对象中挂载装饰器可以直接添加信息，为了直接添加信息就需要装饰器为对象，我本来想的是在debugger里定义一个对象不优雅，
    可其实现在这么做也挺不优雅的😅当时没想到可以将挂载装饰器定义成返回装饰器的函数。。。不过已经这样了。
    当被作为装饰器调用时，执行顺序如下：
    1. .set_register_function 方法  (此时为初始化）
    2. 定义被装饰方法
    3. .__init__                   (初始化，传入的 func 为刚才定义的被装饰的方法）
    之后，被装饰的函数作为 Debugger 类实例(下称 debugger)的方法被作为装饰器调用时：
    Example:
        @debugger.register_important_function("message")
        def an_important_function(self):
            ...
    1. .__get__ -> 此时获得 debugger, 使 self.my_debugger = debugger
    2. .__call__ -> 输入为被装饰信息, 类型为 str
        2.1 函数将该信息“入栈”
        2.2 返回自身
    3. 定义被装饰方法
    4. .__call__ -> 输入为刚才定义的被装饰的方法
        4.1 .make_function -> 将信息“出栈”
        4.2 调用 ._func, 即在初始化时传入的被装饰函数的debugger方法, 该方法返回值即为被装饰的函数
        4.3 根据初始化时的设置为该函数添加方法, 如“add_messagebox” 为 True 则为该函数添加"send_message"方法
        4.4 返回 被装饰后的函数
    """

    def __init__(self, registration_type, func, **kwargs):  # 这个 func 是被装饰的函数。别忘了也是个装饰器
        self.my_debugger: Debugger
        self.function = None
        self.notelist = []
        self.registration_type = registration_type
        self._func = func
        self.kwargs = kwargs
        functools.update_wrapper(self, func)

    @classmethod
    def set_register_function(cls, registration_type: str, add_messagebox=False):
        """用于装饰方法
        registration_type: str 自定义的登记等级
        add_message: bool 若为 True 则在最后被装饰的方法中添加`send_message`方法用于发送消息。
        |send_message 方法在函数发送信息时优先调用解释器中名为 f"{registration_type}_messagebox".replace(" ", "_") 的方法。
        |例如， registration_type = "test function"，那 AddDebuggerFunction 会先找 debugger中有没有 test_function_messagebox
        |如果有，则会将该函数传给该方法，否则将 send_message 赋值为 debugger.registered_function_messagebox。
        """
        # 说真的我也不知道这里应该用partial还是partial-method但是后者会报not callable错误
        # 可能是因为partial-method使用的是__get__属性，而此情况没有被代理。
        return functools.partial(cls, registration_type, add_messagebox=add_messagebox)

    def __get__(self, instance, owner):
        """用这个方法来获取 Debugger，虽然说这个类型是唯一的。。。"""
        if instance is not None:
            self.my_debugger = instance
        return self

    def __call__(self, note_or_func):  # TODO: 添加函数显示消息的功能
        if isinstance(note_or_func, str):
            self.notelist.append(note_or_func)
            return self
        elif callable(note_or_func):
            return self.make_function(note_or_func)
        else:
            raise TypeError("note_or_func 应当为字符或可调用对象")

    def make_function(self, func):
        note = self.notelist.pop()
        res = self._func(self.my_debugger, note, func)  # self属性需要手动传入
        functools.update_wrapper(res, func)

        if self.kwargs.get("add_messagebox"):
            box = getattr(self.my_debugger, self.registration_type.replace(" ", "_") + "_messagebox", None)
            if box is None:
                box = getattr(self.my_debugger, "registered_function_messagebox")
            # 如果已经被有了 send_message 方法，则被覆盖
            res.send_message = functools.partial(box, self.registration_type, note)

        return res


class Debugger:
    """通过重写 __new__, 调试器具有唯一性。

    """
    _debugger = None

    def __new__(cls, *args, **kwargs):
        dg = cls._debugger
        if dg is None:
            dg = cls._debugger = super().__new__(cls, *args, **kwargs)
        return dg

    def enter_important_function(self, message, func):  # TODO
        return

    def exit_important_function(self, message, func):  # TODO
        return

    def registered_function_messagebox(self, registration_type, registered_function_note,
                                       message, args=None, kwargs=None):  # TODO
        """
        被标记函数信息输出函数，当某被标记的函数输出信息时被调用，此函数由 AddDebuggerFunction 传给被登记的函数。
        在函数发送信息时优先调用解释器中名为 f"{registration_type}_messagebox".replace(" ", "_") 的方法。
        例如， registration_type = "test function"，那 AddDebuggerFunction 会先找 debugger中有没有 test_function_messagebox
        如果有，则会将信息传给该方法，否则才调用此方法。
        """
        print(type(self).__name__, ":", registration_type, registered_function_note, message)
        return

    @AddDebuggerFunction.set_register_function("important function", add_messagebox=True)
    def register_important_function(self, message, func) -> typing.Callable:  # TODO: 支持多种模式
        """设置重要函数，当开启调试时自动显示。
        调用时使用 ${方法名}.send_message 方法可以发送 "important function" 级别的消息。
        若被装饰的方法已经被有了 send_message 方法，则覆盖原方法。
        """

        def rst(*args, **kargs):
            self.enter_important_function(message, func)  # TODO: 根据返回值实现不同功能
            ret = func(*args, **kargs)
            self.exit_important_function(message, func)
            return ret

        return rst


debugger = Debugger()

__all__ = ["debugger", "Debugger", "AddDebuggerFunction"]
