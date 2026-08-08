import os
import asyncio
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Armazena os dados da fila na memória
fila_jogadores = []
TAMANHO_MAXIMO = 2  # 1v1

# Emojis personalizados
EMOJI_CONTROLE = "<:emoji_1:1535450507160846506>"
EMOJI_DINHEIRO = "<:emoji_2:1535453860947034193>"
EMOJI_BONECO = "<:emoji_3:1535462271906746408>"
EMOJI_GELO = "<:emoji_4:1535465191481810954>"


# ------------------------------------------------------------------
# Embed da Fila
# ------------------------------------------------------------------
def criar_embed_fila():
    embed = discord.Embed(
        title="➔ 1x1 — Fila de Partida",
        color=discord.Color.green()
    )

    embed.add_field(
        name=f"{EMOJI_CONTROLE} Modo",
        value="1x1 Mobile",
        inline=False
    )

    embed.add_field(
        name=f"{EMOJI_DINHEIRO} Valor",
        value="R$ 0,50",
        inline=False
    )

    if not fila_jogadores:
        texto_jogadores = "*Aguardando jogador...*"
    else:
        texto_jogadores = "\n".join(
            [f"• {j.mention}" for j in fila_jogadores]
        )

    embed.add_field(
        name=f"{EMOJI_BONECO} Jogadores",
        value=texto_jogadores,
        inline=False
    )

    embed.set_thumbnail(
        url="https://cdn.discordapp.com/embed/avatars/0.png"
    )

    return embed


# ------------------------------------------------------------------
# Embed da Partida
# ------------------------------------------------------------------
def criar_embed_partida(jogadores, modo_gelo):
    j1, j2 = jogadores[0], jogadores[1]

    embed = discord.Embed(
        title="⚔️ Partida Confirmada — 1x1",
        color=discord.Color.green()
    )

    embed.add_field(
        name=f"{EMOJI_CONTROLE} Modo de Jogo",
        value=modo_gelo,
        inline=False
    )

    embed.add_field(
        name=f"{EMOJI_DINHEIRO} Aposta",
        value="R$ 0,50",
        inline=False
    )

    embed.add_field(
        name=f"{EMOJI_BONECO} Jogadores",
        value=f"{j1.mention} vs {j2.mention}",
        inline=False
    )

    embed.add_field(
        name="🔥 Regra",
        value="Quem ganha come o BLUG comecem",
        inline=False
    )

    embed.set_thumbnail(
        url="https://cdn.discordapp.com/embed/avatars/0.png"
    )

    return embed


# ------------------------------------------------------------------
# View dos Botões de Confirmação
# ------------------------------------------------------------------
class ConfirmarPartidaView(discord.ui.View):

    def __init__(self, jogadores):
        super().__init__(timeout=None)

        self.jogadores = jogadores
        self.confirmados = set()

    # --------------------------------------------------------------
    # Botão Continuar
    # --------------------------------------------------------------
    @discord.ui.button(
        label="Continuar",
        style=discord.ButtonStyle.success,
        emoji="✅"
    )
    async def continuar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        user = interaction.user

        if user not in self.jogadores:
            await interaction.response.send_message(
                "❌ Você não faz parte desta partida!",
                ephemeral=True
            )
            return

        if user.id in self.confirmados:
            await interaction.response.send_message(
                "⚠️ Você já confirmou!",
                ephemeral=True
            )
            return

        self.confirmados.add(user.id)

        # Apenas um confirmou
        if len(self.confirmados) < len(self.jogadores):

            embed_confirmacao = discord.Embed(
                title="✅ Partida Confirmada",
                description=(
                    f"{user.mention} confirmou a aposta!\n"
                    "O outro jogador precisa confirmar para continuar."
                ),
                color=discord.Color.green()
            )

            await interaction.response.send_message(
                embed=embed_confirmacao
            )

        # Os dois confirmaram
        else:

            embed_final = discord.Embed(
                title="🚀 Ambos Confirmaram!",
                description=(
                    "Todos os jogadores confirmaram! "
                    "A partida está liberada. Boa sorte!"
                ),
                color=discord.Color.green()
            )

            # Desativa todos os botões
            for item in self.children:
                item.disabled = True

            await interaction.response.edit_message(
                view=self
            )

            await interaction.followup.send(
                embed=embed_final
            )

    # --------------------------------------------------------------
    # Botão Cancelar
    # --------------------------------------------------------------
    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.danger,
        emoji="✖️"
    )
    async def cancelar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        user = interaction.user

        if user not in self.jogadores:
            await interaction.response.send_message(
                "❌ Você não faz parte desta partida!",
                ephemeral=True
            )
            return

        # Desativa todos os botões
        for item in self.children:
            item.disabled = True

        embed_cancelado = discord.Embed(
            title="❌ Partida Cancelada",
            description=f"{user.mention} cancelou a partida.",
            color=discord.Color.red()
        )

        await interaction.response.edit_message(
            view=self
        )

        await interaction.followup.send(
            embed=embed_cancelado
        )


# ------------------------------------------------------------------
# View da Fila
# ------------------------------------------------------------------
class FilaView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    # --------------------------------------------------------------
    # Gelo Normal
    # --------------------------------------------------------------
    @discord.ui.button(
        label="Gelo Normal",
        style=discord.ButtonStyle.success,
        emoji=EMOJI_GELO
    )
    async def gelo_normal(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.entrar_na_fila(
            interaction,
            "Gelo Normal"
        )

    # --------------------------------------------------------------
    # Gelo Infinito
    # --------------------------------------------------------------
    @discord.ui.button(
        label="Gelo Infinito",
        style=discord.ButtonStyle.success,
        emoji=EMOJI_GELO
    )
    async def gelo_infinito(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.entrar_na_fila(
            interaction,
            "Gelo Infinito"
        )

    # --------------------------------------------------------------
    # Sair da fila
    # --------------------------------------------------------------
    @discord.ui.button(
        label="Sair Fila",
        style=discord.ButtonStyle.danger,
        emoji="❌"
    )
    async def sair_fila(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        user = interaction.user

        if user in fila_jogadores:

            fila_jogadores.remove(user)

            embed_atualizado = criar_embed_fila()

            await interaction.response.edit_message(
                embed=embed_atualizado,
                view=self
            )

            await interaction.followup.send(
                f"🚪 {user.mention} saiu da fila.",
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                "❌ Você não está na fila!",
                ephemeral=True
            )

    # --------------------------------------------------------------
    # Entrada na fila
    # --------------------------------------------------------------
    async def entrar_na_fila(
        self,
        interaction: discord.Interaction,
        modo_gelo: str
    ):
        user = interaction.user

        if user in fila_jogadores:
            await interaction.response.send_message(
                "⚠️ Você já está na fila!",
                ephemeral=True
            )
            return

        if len(fila_jogadores) >= TAMANHO_MAXIMO:
            await interaction.response.send_message(
                "❌ A fila já está cheia!",
                ephemeral=True
            )
            return

        fila_jogadores.append(user)

        # ----------------------------------------------------------
        # Fila cheia
        # ----------------------------------------------------------
        if len(fila_jogadores) == TAMANHO_MAXIMO:

            jogadores_partida = fila_jogadores.copy()

            # Limpa a fila
            fila_jogadores.clear()

            # Atualiza painel público
            await interaction.response.edit_message(
                embed=criar_embed_fila(),
                view=self
            )

            await interaction.followup.send(
                "✅ Fila lotada! Criando partida...",
                ephemeral=True
            )

            channel = interaction.channel

            j1 = jogadores_partida[0]
            j2 = jogadores_partida[1]

            # ------------------------------------------------------
            # Cria o tópico privado
            # ------------------------------------------------------
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

            # ------------------------------------------------------
            # Adiciona os jogadores
            # ------------------------------------------------------
            await topico.add_user(j1)
            await topico.add_user(j2)

            # Pequeno intervalo para o Discord criar
            # as mensagens de sistema
            await asyncio.sleep(0.5)

            # ------------------------------------------------------
            # Limpeza inicial das mensagens de sistema
            # ------------------------------------------------------
            try:

                async for mensagem in topico.history(limit=20):

                    if mensagem.type != discord.MessageType.default:

                        try:
                            await mensagem.delete()
                        except Exception:
                            pass

            except Exception:
                pass

            # ------------------------------------------------------
            # Envia a partida
            # ------------------------------------------------------
            embed_partida = criar_embed_partida(
                jogadores_partida,
                modo_gelo
            )

            view_confirmacao = ConfirmarPartidaView(
                jogadores_partida
            )

            await topico.send(
                content=f"🔔 {j1.mention} {j2.mention}",
                embed=embed_partida,
                view=view_confirmacao
            )

        # ----------------------------------------------------------
        # Ainda falta jogador
        # ----------------------------------------------------------
        else:

            embed_atualizado = criar_embed_fila()

            await interaction.response.edit_message(
                embed=embed_atualizado,
                view=self
            )

            await interaction.followup.send(
                f"✅ {user.mention} entrou na fila ({modo_gelo})!",
                ephemeral=True
            )


# ------------------------------------------------------------------
# APAGA AUTOMATICAMENTE MENSAGENS DE SISTEMA DOS TÓPICOS
# ------------------------------------------------------------------
@bot.event
async def on_message(message):

    # Ignora mensagens enviadas pelo próprio bot
    if message.author == bot.user:
        return

    # Verifica se a mensagem está dentro de um tópico
    if isinstance(message.channel, discord.Thread):

        # Mensagens de sistema:
        # "Bot de AP adicionou fulano ao tópico"
        # "Bot de AP removeu fulano do tópico"
        # etc.
        if message.type != discord.MessageType.default:

            try:
                await message.delete()
            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException
            ):
                pass

            return

    # IMPORTANTE:
    # Mantém os comandos !fila funcionando
    await bot.process_commands(message)


# ------------------------------------------------------------------
# Bot online
# ------------------------------------------------------------------
@bot.event
async def on_ready():

    print(
        f"✅ Bot online com sucesso como: {bot.user}"
    )


# ------------------------------------------------------------------
# Comando !fila
# ------------------------------------------------------------------
@bot.command(name="fila")
async def gerar_fila(ctx):

    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = criar_embed_fila()

    view = FilaView()

    await ctx.send(
        embed=embed,
        view=view
    )


# ------------------------------------------------------------------
# TOKEN
# ------------------------------------------------------------------
TOKEN = os.getenv("TOKEN")

if not TOKEN:

    print(
        "❌ ERRO: A variável 'TOKEN' não existe no Railway!"
    )

else:

    bot.run(TOKEN)
