import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Armazena os dados da fila na memória
fila_jogadores = []
TAMANHO_MAXIMO = 2  # 1v1

# ------------------------------------------------------------------
# Função que gera a Embed bonita idêntica à do seu print
# ------------------------------------------------------------------
def criar_embed_fila():
    embed = discord.Embed(
        title="➔ 1x1 — Fila de Partida",
        color=discord.Color.red()  # Barra vermelha na lateral
    )
    embed.add_field(name="🎮 Modo", value="1x1 Mobile", inline=False)
    embed.add_field(name="💰 Valor", value="R$ 0,50", inline=False)

    if not fila_jogadores:
        texto_jogadores = "*Aguardando jogador...*"
    else:
        texto_jogadores = "\n".join([f"• {j.mention}" for j in fila_jogadores])

    embed.add_field(name="👤 Jogadores", value=texto_jogadores, inline=False)
    
    # Imagem/Thumbnail no canto (opcional)
    embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
    return embed

# ------------------------------------------------------------------
# Botões interativos do painel
# ------------------------------------------------------------------
class FilaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # O painel não expira

    # Botão: Gelo Normal
    @discord.ui.button(label="Gelo Normal", style=discord.ButtonStyle.secondary, emoji="🧊")
    async def gelo_normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.entrar_na_fila(interaction, "Gelo Normal")

    # Botão: Gelo Infinito
    @discord.ui.button(label="Gelo Infinito", style=discord.ButtonStyle.secondary, emoji="🧊")
    async def gelo_infinito(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.entrar_na_fila(interaction, "Gelo Infinito")

    # Botão: Sair Fila
    @discord.ui.button(label="Sair Fila", style=discord.ButtonStyle.danger, emoji="❌")
    async def sair_fila(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user in fila_jogadores:
            fila_jogadores.remove(user)
            embed_atualizado = criar_embed_fila()
            await interaction.response.edit_message(embed=embed_atualizado, view=self)
            await interaction.followup.send(f"🚪 {user.mention} saiu da fila.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Você não está na fila!", ephemeral=True)

    # Lógica ao clicar em qualquer um dos botões de entrar
    async def entrar_na_fila(self, interaction: discord.Interaction, modo_gelo: str):
        user = interaction.user

        if user in fila_jogadores:
            await interaction.response.send_message("⚠️ Você já está na fila!", ephemeral=True)
            return

        if len(fila_jogadores) >= TAMANHO_MAXIMO:
            await interaction.response.send_message("❌ A fila já está cheia!", ephemeral=True)
            return

        fila_jogadores.append(user)
        embed_atualizado = criar_embed_fila()

        # Atualiza a mensagem da fila no chat
        await interaction.response.edit_message(embed=embed_atualizado, view=self)
        await interaction.followup.send(f"✅ {user.mention} entrou na fila ({modo_gelo})!", ephemeral=True)

        # Se a fila lotar (2/2)
        if len(fila_jogadores) == TAMANHO_MAXIMO:
            jogadores_mencao = " vs ".join([j.mention for j in fila_jogadores])
            await interaction.channel.send(f"🔥 **PARTIDA ENCONTRADA!** ({modo_gelo})\n{jogadores_mencao}\n\n*Organizem a sala!*")
            fila_jogadores.clear()

# ------------------------------------------------------------------
# Evento e Comando principal
# ------------------------------------------------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot online com sucesso como: {bot.user}")

@bot.command(name="fila")
async def gerar_fila(ctx):
    # Deleta o comando do usuário se tiver permissão, pra manter o chat limpo
    try:
        await ctx.message.delete()
    except:
        pass

    embed = criar_embed_fila()
    view = FilaView()
    await ctx.send(embed=embed, view=view)

# Pega o token do Railway
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ ERRO: A variável 'TOKEN' não existe no Railway!")
else:
    bot.run(TOKEN)
        
