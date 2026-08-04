
from langchain.agents import create_agent
from model_qwen import model
from tools import *

class SmartAssistant:
    """多功能智能助手"""
    def __init__(self):
        self.agent = create_agent(
            model = model,
            tools = [
                    get_weather,
                    calculator,
                    search_product,
                    convert_currency,
                    get_current_time
                    ],
            # debug=True,
            system_prompt = """
            你是一个多功能智能助手，可以查询天气、数学计算、搜索商品、转换货币、获取当前时间。
            你必须使用以下工具来完成你的任务：
            1. get_weather: 获取天气信息，参数为城市名称，返回格式为JSON。
            2. calculator: 数学计算，参数为数学表达式，返回计算结果。
            3. search_product: 搜索商品，参数为关键词，返回商品信息。
            4. convert_currency: 转换货币，参数为金额、原货币、目标货币，返回转换结果。
            5. get_current_time: 获取当前时间，参数为时区，返回格式为ISO860
            重要提示：
            1.仔细阅读用户问题，确定需要并确定使用哪个工具。
            2.使用工具时，请确保参数正确，并返回格式正确。
            3.请勿重复使用工具，请勿重复使用工具。
            4.请勿使用工具来处理非工具相关的问题
            5.如果无法完成任务，诚实地告诉用户原因。
            """,
        )

        self.messages = []

    def chat(self, user_input: str) -> str:
        """对话接口"""
        # 添加用户消息
        self.messages.append({"role": "user", "content": user_input})

        # 调用agent
        result = self.agent.invoke({"messages": self.messages})

        # 更新消息历史
        self.messages = result["messages"]

        # 获取最后一条AI回复
        for msg in reversed(self.messages):
            if msg.type == "ai" and msg.content:
                return msg.content

        return "我无法回答你的问题。"

    def reset(self) -> None:
        """重置对话"""
        self.messages = []


    def main():
        assistant = SmartAssistant()

        print("欢迎使用多功能智能助手！")
        print("="*80)
        print("我可以帮你查询天气、数学计算、搜索商品、转换货币、获取当前时间。")
        print("输入quit退出,输入reset重置对话。")
        print("请输入你的问题：")

        # # 示例演示
        # print("【示例演示】")
        # demos = [
        #     "今天天气如何？",
        #     "计算1+1",
        #     "搜索手机",
        #     "将100元转换成欧元",
        #     "现在几点",
        #     "重置",
        # ]

        # for demo in demos:
        #     print(f"【输入】{demo}")
        #     print(f"【输出】{assistant.chat(demo)}")
        #     print("-"*80)

        # 交互模式
        print("【交互模式】")
        print("=="*80)
        while True:
            user_input = input("请输入你的问题：")
            if user_input.lower() == "quit":
                print("感谢使用，再见！")
                break
            elif user_input.lower() == "reset":
                assistant.reset()
                print("已重置对话。")
            else:
                print(f"【输入】{user_input}")
                print(f"【输出】{assistant.chat(user_input)}")
                print()

if __name__ == "__main__":
    SmartAssistant.main()