import os
import discord
from discord.ext import commands

# Configuração dos intents
intents = discord.Intents.default()
intents.message_content = True

# Definição do bot
bot = commands.Bot(command_prefix="#", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online com sucesso como: {bot.user}")

# Comando #quem e gay?🏳️‍🌈 (ou #quem)
@bot.command(name="quem")
async def quem_gay(ctx, *, args=None):
    # Verifica se o restante da mensagem é "e gay?🏳️‍🌈" ou similar
    if args and "e gay" in args.lower():
        await ctx.send("E o Davy aquele viado")

# Pega o token direto das variáveis do Railway
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ ERRO: A variável 'TOKEN' não existe no Railway!")
else:
    bot.run(TOKEN)
    
