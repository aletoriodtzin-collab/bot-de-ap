import os
import discord
from discord.ext import commands

# Configuração dos intents necessários para o bot
intents = discord.Intents.default()
intents.message_content = True  # Ative no Discord Dev Portal em 'Bot' -> 'Message Content Intent'

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online com sucesso como: {bot.user}")

# Lendo a variável TOKEN do Railway
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ ERRO: A variável de ambiente 'TOKEN' não foi encontrada no Railway!")

bot.run("MTUzNTQyMTk3MTEwNDUzNDY3MQ.Gh8Jr8.hvMyoHkB6tbqSz_q3mROrEgoUlZyT2l5bOTsis")
