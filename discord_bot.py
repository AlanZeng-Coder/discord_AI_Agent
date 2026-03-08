# 导入 os 库，用来读取环境变量
import os
import json
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

# --- 内容审查 Prompt ---
MODERATION_SYSTEM_PROMPT = """你是一个基督教教会 Discord 群的内容审查助手。

你的唯一任务是判断用户发送的消息是否在**推广、宣传、或劝人信仰基督教以外的宗教**。

以下情况 **不算违规**（flagged = false）：
- 正常的日常聊天（天气、问候、生活分享等）
- 讨论或提问任何宗教话题（包括比较不同宗教）
- 分享个人信仰经历（如 "我以前信佛，后来接触了基督教"）
- 学术性地提到其他宗教
- 表情包、图片描述、链接分享（除非内容明显是宣传）

以下情况 **算违规**（flagged = true）：
- 主动向群友推广其他宗教（如 "大家来念阿弥陀佛，佛祖保佑你们"）
- 试图说服、劝导他人信仰基督教以外的宗教
- 发送其他宗教的传教材料或宣传内容
- 贬低基督教并推崇其他宗教

请严格按以下 JSON 格式回复，不要回复任何其他内容：
{"flagged": true/false}
"""

# --- Gemini AI 初始化 ---
# 配置 Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # 创建一个专门用于内容审查的模型，配置 system instruction
    moderation_model = genai.GenerativeModel(
        'gemini-2.5-flash',
        system_instruction=MODERATION_SYSTEM_PROMPT
    )
except Exception as e:
    print(f"Gemini AI 配置失败: {e}")
    moderation_model = None

# --- 警告消息 ---
WARNING_MESSAGE = (
    "⚠️ **温馨提醒** ⚠️\n\n"
    "本群是基督信仰交流群，请勿在群内宣传其他宗教内容。\n"
    "如有疑问，欢迎联系管理员。谢谢配合！🙏"
)

# --- Discord 机器人核心代码 ---

# 创建一个 Intents 对象，告诉 Discord 我们需要哪些权限
intents = discord.Intents.default()
intents.message_content = True

# 创建一个机器人客户端实例
client = discord.Client(intents=intents)

# 1. 当机器人成功连接到 Discord 时触发
@client.event
async def on_ready():
    """当机器人成功登录后，在后台打印确认信息"""
    print(f'机器人已成功登录，用户名为: {client.user}')
    print('内容审查模式已启动 🛡️')
    print('------')

# 2. 当机器人收到消息时触发 — 内容审查逻辑
@client.event
async def on_message(message):
    """审查收到的每条消息"""
    # a. 忽略机器人自己的消息
    if message.author == client.user:
        return

    # b. 忽略其他机器人的消息
    if message.author.bot:
        return

    # c. 确保审查模型已初始化
    if not moderation_model:
        return

    # d. 忽略空消息或太短的消息（少于 3 个字符不太可能是宣传）
    if not message.content or len(message.content.strip()) < 3:
        return

    # e. 打印收到的消息，方便调试
    print(f"审查消息 - {message.author}: '{message.content}'")

    # f. 调用 Gemini 进行内容审查
    try:
        response = await asyncio.to_thread(
            moderation_model.generate_content,
            message.content
        )
        result_text = response.text.strip()
        print(f"审查结果: {result_text}")

        # 解析 Gemini 返回的 JSON
        result = json.loads(result_text)

        # g. 如果被标记为违规，发送警告
        if result.get("flagged", False):
            print(f"⚠️ 违规消息被检测到！来自: {message.author}")
            await message.reply(WARNING_MESSAGE)

    except json.JSONDecodeError:
        # Gemini 返回的不是有效 JSON，忽略
        print(f"审查返回非 JSON 格式: {result_text}")
    except Exception as e:
        # 审查出错时静默处理，不影响群聊
        print(f"内容审查时发生错误: {e}")

# --- 启动机器人 ---
def main():
    """主函数，用于启动机器人"""
    if not DISCORD_TOKEN or DISCORD_TOKEN == "在这里替换成你的_DISCORD_BOT_TOKEN":
        print("错误：请在代码中填入你的 DISCORD_TOKEN！")
        return

    if not GEMINI_API_KEY or GEMINI_API_KEY == "在这里替换成你的_GEMINI_API_KEY":
        print("错误：请在代码中填入你的 GEMINI_API_KEY！")
        return

    if not moderation_model:
        print("错误：Gemini 模型未能初始化，请检查您的 API Key 和网络连接。")
        return

    print("机器人启动中（内容审查模式）...")
    try:
        client.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        print("错误：Discord Token 无效。请检查你粘贴的 DISCORD_TOKEN 是否正确。")
    except Exception as e:
        print(f"启动机器人时发生未知错误: {e}")

if __name__ == '__main__':
    main()