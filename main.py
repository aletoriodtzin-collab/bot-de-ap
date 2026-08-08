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

bot.run("f5244c878494111ea81468c378c7ec108ba63b86f97d576a6730bf78cdb119bb")
