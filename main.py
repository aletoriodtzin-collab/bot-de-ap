import os
import discord
from discord.ext import commands

# Configuração dos intents do bot
intents = discord.Intents.default()
intents.message_content = True  # Lembre-se de ativar essa permissão no Discord Developer Portal

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online com sucesso como: {bot.user}")

# Pega o token configurado nas variáveis do Railway
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ ERRO: A variável 'TOKEN' não foi encontrada nas variáveis de ambiente do Railway!")
else:
    bot.run(TOKEN)
    
