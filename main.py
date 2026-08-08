import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Armazena os dados da fila na memória
fila_jogadores = []
TAMANHO_MAXIMO = 2  # 1v1

# Todos os seus emojis personalizados configurados!
EMOJI_CONTROLE = "<:emoji_1:1535450507160846506>"
EMOJI_DINHEIRO = "<:emoji_2:1535453860947034193>"
EMOJI_BONECO   = "<:emoji_3:1535457054507139203>"

# ------------------------------------------------------------------
# Função que gera a Embed da Fila no Chat (Painel Público)
# ------------------------------------------------------------------
def criar_embed_fila():
    embed = discord.Embed(
        title="➔ 1x1 — Fila de Partida",
        color=discord.Color.green()  # Barra verde na lateral
    )
    embed.add_field(name=f"{EMOJI_CONTROLE} Modo", value="1x1 Mobile", inline=False)
    embed.add_field(name=f"{EMOJI_DINHEIRO} Valor", value="R$ 0,50", inline=False)

    if not fila_jogadores:
        texto_jogadores = "*Aguardando jogador...*"
    else:
        texto_jogadores = "\n".join([f"• {j.mention}" for j in fila_jogadores])

    embed.add_field(name=f"{EMOJI_BONECO} Jogadores", value=texto_jogadores, inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
    return embed

# ------------------------------------------------------------------
# Função que gera a Embed para o Tópico Privado da Partida
# ------------------------------------------------------------------
def criar_embed_partida(jogadores, modo_gelo):
    j1, j2 = jogadores[0], jogadores[1]
    embed = discord.Embed(
        title="⚔️ Partida Confirmada — 1x1",
        color=discord.Color.green()
    )
    embed.add_field(name=f"{EMOJI_CONTROLE} Modo de Jogo", value=f"{modo_gelo}", inline=False)
    embed.add_field(name=f"{EMOJI_DINHEIRO} Aposta", value="R$ 0,50", inline=False)
    embed.add_field(name=f"{EMOJI_BONECO} Jogadores", value=f"{j1.mention} vs {j2.mention}", inline=False)
    embed.add_field(name="🔥 Regra", value="Quem ganha come o BLUG comecem", inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
    return embed

# ------------------------------------------------------------------
# Botões interativos do painel
# ------------------------------------------------------------------
class FilaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # Botão: Gelo Normal
    @discord.ui.button(label="Gelo Normal", style=discord.ButtonStyle.success, emoji="🧊")
    async def gelo_normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.entrar_na_fila(interaction, "Gelo Normal")

    # Botão: Gelo Infinito
    @discord.ui.button(label="Gelo Infinito", style=discord.ButtonStyle.success, emoji="🧊")
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

    # Lógica de entrada e criação do tópico privado
    async def entrar_na_fila(self, interaction: discord.Interaction, modo_gelo: str):
        user = interaction.user

        if user in fila_jogadores:
            await interaction.response.send_message("⚠️ Você já está na fila!", ephemeral=True)
            return

        if len(fila_jogadores) >= TAMANHO_MAXIMO:
            await interaction.response.send_message("❌ A fila já está cheia!", ephemeral=True)
            return

        fila_jogadores.append(user)

        # Quando lotar a fila (2/2)
        if len(fila_jogadores) == TAMANHO_MAXIMO:
            jogadores_partida = fila_jogadores.copy()
            
            # Reset automático da fila
            fila_jogadores.clear()

            # Reseta o painel público do chat para "Aguardando jogador..."
            await interaction.response.edit_message(embed=criar_embed_fila(), view=self)
            await interaction.followup.send(f"✅ Fila lotada! Criando partida...", ephemeral=True)

            channel = interaction.channel
            j1, j2 = jogadores_partida[0], jogadores_partida[1]

            # Criar o tópico privado para a partida
            try:
                topico = await channel.create_thread(
                    name=f"🎮-1x1-{j1.name}-vs-{j2.name}",
                    type=discord.ChannelType.private_thread,
                    auto_archive_duration=60
                )
            except Exception:
                topico = await channel.create_thread(
                    name=f"🎮-1x1-{j1.name}-vs-{j2.name}",
                    auto_archive_duration=60
                )

            # Adiciona os 2 jogadores no tópico privado
            await topico.add_user(j1)
            await topico.add_user(j2)

            # Envia a embed bonita dentro do tópico privado
            embed_partida = criar_embed_partida(jogadores_partida, modo_gelo)
            await topico.send(
                content=f"🔔 {j1.mention} {j2.mention}",
                embed=embed_partida
            )
        else:
            # Caso falte jogador (1/2), apenas atualiza a Embed no canal
            embed_atualizado = criar_embed_fila()
            await interaction.response.edit_message(embed=embed_atualizado, view=self)
            await interaction.followup.send(f"✅ {user.mention} entrou na fila ({modo_gelo})!", ephemeral=True)

# ------------------------------------------------------------------
# Evento e Comando principal
# ------------------------------------------------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot online com sucesso como: {bot.user}")

@bot.command(name="fila")
async def gerar_fila(ctx):
    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = criar_embed_fila()
    view = FilaView()
    await ctx.send(embed=embed, view=view)

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ ERRO: A variável 'TOKEN' não existe no Railway!")
else:
    bot.run(TOKEN)
            
