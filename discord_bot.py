# 导入 os 库，用来读取环境变量
import os
import discord
import google.generativeai as genai
import asyncio

# --- 配置 ---
# 从 Heroku 的环境变量中读取密钥
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 检查密钥是否存在，如果不存在则打印错误并退出
if not DISCORD_TOKEN or not GEMINI_API_KEY:
    print("错误：请在 Heroku 的 Config Vars 中设置 DISCORD_TOKEN 和 GEMINI_API_KEY！")
    exit()


# --- Gemini AI 初始化 ---
# 配置 Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # 创建一个指向 gemini-pro 模型的对象
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    print(f"Gemini AI 配置失败: {e}")
    gemini_model = None

# --- Discord 机器人核心代码 ---

# 创建一个 Intents 对象，告诉 Discord 我们需要哪些权限
# discord.Intents.default() 包含了很多默认权限
# message_content=True 是我们手动开启的，为了能读取消息内容
intents = discord.Intents.default()
intents.message_content = True

# 创建一个机器人客户端实例
client = discord.Client(intents=intents)

# 1. 定义一个事件处理函数，当机器人成功连接到 Discord 时触发
@client.event
async def on_ready():
    """当机器人成功登录后，在后台打印确认信息"""
    print(f'机器人已成功登录，用户名为: {client.user}')
    print('------')

# 2. 定义另一个事件处理函数，当机器人收到消息时触发
@client.event
async def on_message(message):
    """处理收到的消息"""
    # a. 避免机器人回复自己，否则会陷入无限循环
    if message.author == client.user:
        return

    # b. 确保 Gemini 模型已成功初始化
    if not gemini_model:
        return

    # c. 打印收到的消息，方便在后台调试
    print(f"收到来自 '{message.author}' 的消息: '{message.content}'")

    # d. 进入核心的 AI 回复逻辑
    try:
        # 在 Discord 中显示“机器人正在输入...”的状态，提升用户体验
        async with message.channel.typing():
            # 调用 Gemini API 生成内容
            # 使用 asyncio.to_thread 来异步运行同步的 Gemini 代码，防止阻塞
            response = await asyncio.to_thread(
                gemini_model.generate_content,
                message.content
            )
            ai_reply = response.text

        # 发送 Gemini 的回复到 Discord 频道
        await message.channel.send(ai_reply)

    except Exception as e:
        print(f"处理消息时发生错误: {e}")
        # 如果出错，也发送一条消息告知用户
        await message.channel.send("抱歉，我的大脑好像短路了，请稍后再试。")

# --- 启动机器人 ---
def main():
    """主函数，用于启动机器人"""
    if not DISCORD_TOKEN or DISCORD_TOKEN == "在这里替换成你的_DISCORD_BOT_TOKEN":
        print("错误：请在代码中填入你的 DISCORD_TOKEN！")
        return

    if not GEMINI_API_KEY or GEMINI_API_KEY == "在这里替换成你的_GEMINI_API_KEY":
        print("错误：请在代码中填入你的 GEMINI_API_KEY！")
        return
    
    if not gemini_model:
        print("错误：Gemini 模型未能初始化，请检查您的 API Key 和网络连接。")
        return

    print("机器人启动中...")
    try:
        client.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        print("错误：Discord Token 无效。请检查你粘贴的 DISCORD_TOKEN 是否正确。")
    except Exception as e:
        print(f"启动机器人时发生未知错误: {e}")

if __name__ == '__main__':
    main()