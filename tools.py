"""
工具类
"""
from langchain_core.tools import tool
import math
from datetime import datetime

@tool
def calculator(expression: str) -> str:
    """
    计算给定的数学表达式

    支持基本运算符：+ - * / % ** sqrt

    Args：
        expression (str): 数学表达式 如 "2+2" 或者 "sqrt(4)"

    Returns：
        计算结果

    Example：
        calculator("2+2") 返回 "4.0"
        calculator("sqrt(4)") 返回 "2.0"
    """
    try:
        # 安全的数学运算
        safe_dict = {
            "sqrt": math.sqrt,
            "+": lambda x, y: x + y,
            "-": lambda x, y: x - y,
            "*": lambda x, y: x * y,
            "/": lambda x, y: x / y,
            "%": lambda x, y: x % y,
            "**": lambda x, y: x ** y,
            "datetime": datetime.now,
            "sqrt": math.sqrt,
            "pow": math.pow,
            "abs": math.fabs,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
            "degrees": math.degrees,
        }
        result = eval(expression, {"_builtins_": {}}, safe_dict)
        return str(result)
    except Exception as e:
        return f"计算错误：{e}"

@tool
def get_current_time(timezone: str = "Asia/Shanghai") -> str:
    """
    获取当前时间

    Args：
        timezone (str, optional): 时区，默认为 "Asia/Shanghai"。

    Returns：
        格式化的当前时间字符串
    """

    now = datetime.now()
    # datetime.now() 已经返回 datetime 对象，不能再写成 now() 调用。
    return now.strftime("%Y年%m月%d日 %H:%M:%S")

@tool
def search_product(keyword: str) -> str:
    """
    搜索产品

    Args：
        keyword (str): 产品关键词

    Returns：
        搜索结果
    """
    # 模拟产品数据库
    products = {
        "手机": "iPhone 13 Pro: 5999元, 小米 11 Pro: 4999元, 华为 P40 Pro: 4999元, 苹果 MacBook Pro: 14999元",
        "电脑": "MacBook Pro: 14999元, 联想 ThinkPad X1 Carbon: 12999元, 惠普 Pavilion: 8999元, 戴尔 XPS: 14999元",
        "耳机": "Apple AirPods Pro: 699元, beats Studio3: 499元, 索尼 WH-1000XM4: 899元, 苹果 EarPods: 49元"
    }

    for key, value in products.items():
        if keyword in key:
            return f"搜索到相关结果：{value}"

    return f"未找到关于{keyword}产品"

@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """
    转换货币
    支持人民币（CNY），美元（USD）,欧元（EUR）,英镑（GBP）,日元（JPY）,澳元（AUD）,港币（HKD）,


    Args：
        amount (float): 金额
        from_currency (str): 源货币
        to_currency (str): 目标货币

    Returns：
        转换后的金额
    """
    # 模拟汇率数据
    exchange_rates = {
        "CNY": 1.0,
        "USD": 0.14,
        "EUR": 0.12,
        "GBP": 0.1,
        "JPY": 1.5,
        "AUD": 0.2,
        "HKD": 0.2,
    }
    try:
        # 先转换CNY,再转换为目标货币
        cny_amount = amount / exchange_rates[from_currency]
        result = cny_amount * exchange_rates[to_currency]
        return f"{amount} {from_currency} = {result:.2f} {to_currency}"
    except KeyError:
        return f"不支持的货币：{from_currency}或者{to_currency}"

@tool
def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息

    Args:
        city (str): 城市名称
    """

    weather_data = {
        "北京": "晴转多云，温度23℃，相对湿度70%",
        "上海": "阴转小雨，温度18℃，相对湿度60%",
        "广州": "多云，温度25℃，相对湿度80%",
        "深圳": "雷阵雨，温度27℃，相对湿度70%",
        "杭州": "阴转小雨，温度19℃，相对湿度60%",
        "南京": "晴转多云，温度23℃，相对湿度70%",
    }
    return weather_data.get(city, f"{city}的天气信息未找到")

@tool
def calculator(expression: str) -> str:
    """
    计算数学表达式

    Args:
        expression (str): 数学表达式 "2 + 2 * 4”
    """
    try:
        result = eval(expression, {"_builtins_": {}}, {})
        return str(result)
    except Exception as e:
        return f"计算错误：{e}"
