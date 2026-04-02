import discord
from discord.ext import commands
from discord.ui import Button, View
from google import genai
from google.genai import types
import os
import io
import requests
import base64
from dotenv import load_dotenv
from pathlib import Path
from deep_translator import GoogleTranslator

# 1. 環境設定
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_TOKEN:
    print("エラー: .envからDISCORD_TOKENを読み込めませんでした。")
    exit()

# 2. Gemini（チャット・相談用）
client = genai.Client(api_key=GEMINI_API_KEY)
ACTIVE_MODEL = "gemini-2.0-flash" # 最新モデルに修正

# 3. Discord Bot設定
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)
TARGET_CHANNEL_NAME = "画像生成"

# --- 再生成ボタンの処理 ---
class RegenerateView(View):
    def __init__(self, prompt):
        super().__init__(timeout=None) # ボタンを永続的に有効にする
        self.prompt = prompt

    @discord.ui.button(label="再生成", style=discord.ButtonStyle.primary, emoji="🔄")
    async def regenerate(self, interaction: discord.Interaction, button: Button):
        # 実行中メッセージを表示（本人にだけ見える）
        await interaction.response.send_message(f"「{self.prompt}」で再生成を開始します...", ephemeral=True)
        # genコマンドを再実行
        ctx = await bot.get_context(interaction.message)
        await ctx.invoke(bot.get_command('gen'), prompt=self.prompt)

# --- 翻訳関数 ---
def translate_to_english(japanese_text):
    return GoogleTranslator(source='ja', target='en').translate(japanese_text)

@bot.event
async def on_ready():
    print(f"--- Bot起動 ---")
    print(f"ログイン名: {bot.user.name}")
    print(f"監視チャンネル: {TARGET_CHANNEL_NAME}")

# --- コマンド部分 ---

@bot.command()
async def chat(ctx, *, message):
    """通常のチャット（Geminiを使用）"""
    if ctx.channel.name != TARGET_CHANNEL_NAME: return
    async with ctx.typing():
        try:
            response = client.models.generate_content(model=ACTIVE_MODEL, contents=message)
            await ctx.send(response.text)
        except Exception as e:
            await ctx.send(f"Geminiエラー: {e}")

@bot.command()
async def gen(ctx, *, prompt):
    """画像生成（ボタン付き）"""
    if ctx.channel.name != TARGET_CHANNEL_NAME: return

    status_msg = await ctx.send(f"翻訳中...")
    
    try:
        # 1. 翻訳
        en_prompt = translate_to_english(prompt)
        
        # 実写クオリティ呪文を自動合成
        full_prompt = f"{en_prompt}, RAW photo, 8k uhd, high quality, film grain, photorealistic"
        await status_msg.edit(content=f"生成中...\nPrompt: `{en_prompt}`")

        # 2. 4070 (Stable Diffusion API) へリクエスト
        payload = {
            "prompt": full_prompt,
            "negative_prompt": "(worst quality, low quality:1.4), (bad anatomy), (illustration, anime:1.2), long neck, deformed, extra fingers",
            "steps": 25,
            "cfg_scale": 7,
            "width": 512,
            "height": 512,
            "enable_hr": True,      
            "hr_scale": 2,
            "hr_upscaler": "R-ESRGAN 4x+",
            "denoising_strength": 0.45
        }
        
        url = "http://127.0.0.1:7860/sdapi/v1/txt2img"
        response = requests.post(url, json=payload, timeout=120)
        r = response.json()

        # 3. 画像を送信（ボタンを添えて）
        image_data = base64.b64decode(r['images'][0])
        file = discord.File(io.BytesIO(image_data), filename="output.png")
        
        # 再生成ボタン付きのViewを作成
        view = RegenerateView(prompt=prompt)
        
        await ctx.send(
            content=f"生成完了！\n`{prompt}` -> `{en_prompt}`", 
            file=file, 
            view=view
        )
        await status_msg.delete()

    except Exception as e:
        if status_msg:
            await status_msg.edit(content=f"エラーが発生しました。\n詳細: {e}")
        else:
            await ctx.send(f"エラーが発生しました。\n詳細: {e}")

# 実行
bot.run(DISCORD_TOKEN)