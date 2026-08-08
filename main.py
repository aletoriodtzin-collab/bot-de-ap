import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Armazena os dados na memória
fila_jogadores = []
fila_mediadores = []  # Fila de mediadores rotativa
dados_pix = {}        # Guarda o Pix de cada usuário: {user_id: {"nome": ..., "chave": ..., "qr": ...}}

# Variável para salvar a mensagem da fila de mediadores para poder atualizar na hora
mensagem_painel_mediador = None

TAMANHO_MAXIMO_JOGADORES = 2  # 1v1

# Emojis personalizados configurados
EMOJI_CONTROLE = "<:emoji_1:1535450507160846506>"
EMOJI_DINHEIRO = "<:emoji_2:1535453860947034193>"
EMOJI_BONECO   = "<:emoji_3:1535462271906746408>"
EMOJI_GELO     = "<:emoji_4:1535465191481810954>"

# ------------------------------------------------------------------
# EVENTO PARA APAGAR MENSAGENS DE SISTEMA (Ex: "adicionou alguém")
# ------------------------------------------------------------------
@bot.event
async def on_message(message):
    if message.type in [
        discord.MessageType.recipient_add,
        discord.MessageType.thread_starter_message
    ]:
        try:
            await message.delete()
        except Exception:
            pass
    
    await bot.process_commands(message)

# ------------------------------------------------------------------
# FORMULÁRIO (MODAL) DE CADASTRO DO PIX
# ------------------------------------------------------------------
class FormularioPixModal(discord.ui.Modal, title="Cadastrar Pix"):
    chave_pix = discord.ui.TextInput(
        label="cadastrar Pix ( aceita CPF,chave aleatória",
        placeholder="Digite sua chave Pix aqui...",
        style=discord.TextStyle.short,
        required=True
    )

    nome_conta = discord.ui.TextInput(
        label="Nome : digite o nome da sua conta no seu app.",
        placeholder="Ex: Bruno Raffael",
        style=discord.TextStyle.short,
        required=True
    )

    link_qr = discord.ui.TextInput(
        label="Link QR Code : coloque o link do seu QR",
        placeholder="Cole o link da imagem do seu QR Code aqui...",
        style=discord.TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        dados_pix[user_id] = {
            "chave": self.chave_pix.value,
            "nome": self.nome_conta.value,
            "qr": self.link_qr.value if self.link_qr.value else "https://cdn.discordapp.com/embed/avatars/0.png"
        }

        await interaction.response.send_message(
            f"✅ **Pix cadastrado com sucesso!**\n"
            f"📌 **Nome:** {self.nome_conta.value}\n"
            f"🔑 **Chave:** {self.chave_pix.value}\n"
            f"🖼️ **Link QR Code:** {self.link_qr.value if self.link_qr.value else 'Não informado'}",
            ephemeral=True
        )

class PixView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cadastrar Pix", style=discord.ButtonStyle.success, emoji="💳")
    async def abrir_formulario(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FormularioPixModal())

@bot.command(name="pix")
async def gerar_pix(ctx):
    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = discord.Embed(
        description="clique nesse botão para cadastrar seu Pix, caso ao contrário não terá como os jogadores adivinharem.",
        color=discord.Color.green()
    )
    embed.set_image(url="https://cdn.discordapp.com/embed/avatars/0.png")
    view = PixView()
    await ctx.send(embed=embed, view=view)

# ------------------------------------------------------------------
# SISTEMA DE FILA DE MEDIADORES ROTATIVA
# ------------------------------------------------------------------
def criar_embed_mediador():
    embed = discord.Embed(
        title="fila de mediador",
        description="Quando quiser entrar na fila basta clicar no botão abaixo! E necessário pra cair e mediar numa fila",
        color=discord.Color.gold()
    )
    
    if not fila_mediadores:
        texto_meds = "*Nenhum mediador na fila no momento.*"
    else:
        texto_meds = "\n".join([f"{i+1}- {med.mention}" for i, med in enumerate(fila_mediadores)])

    embed.add_field(name="📋 Fila Atual", value=texto_meds, inline=False)
    return embed

async def atualizar_painel_mediador():
    global mensagem_painel_mediador
    if mensagem_painel_mediador:
        try:
            embed_atualizado = criar_embed_mediador()
            await mensagem_painel_mediador.edit(embed=embed_atualizado, view=FilaMediadorView())
        except Exception:
            pass

class FilaMediadorView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.success, emoji="🛡️")
    async def entrar_fila_med(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user in fila_mediadores:
            await interaction.response.send_message("⚠️ Você já está na fila de mediadores!", ephemeral=True)
            return

        fila_mediadores.append(user)
        await interaction.response.edit_message(embed=criar_embed_mediador(), view=self)
        await interaction.followup.send("✅ Você entrou na fila de mediadores!", ephemeral=True)

    @discord.ui.button(label="Sair da Fila", style=discord.ButtonStyle.danger, emoji="🚪")
    async def sair_fila_med(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user in fila_mediadores:
            fila_mediadores.remove(user)
            await interaction.response.edit_message(embed=criar_embed_mediador(), view=self)
            await interaction.followup.send("🚪 Você saiu da fila de mediadores.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Você não está na fila de mediadores!", ephemeral=True)

@bot.command(name="med")
async def gerar_fila_mediador(ctx):
    global mensagem_painel_mediador
    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = criar_embed_mediador()
    view = FilaMediadorView()
    mensagem_painel_mediador = await ctx.send(embed=embed, view=view)

# ------------------------------------------------------------------
# ESTRUTURA DA FILA DE PARTIDA E CONFIRMAÇÃO
# ------------------------------------------------------------------
def criar_embed_fila():
    embed = discord.Embed(
        title="➔ 1x1 — Fila de Partida",
        color=discord.Color.green()
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

class ConfirmarPartidaView(discord.ui.View):
    def __init__(self, jogadores, modo_gelo):
        super().__init__(timeout=None)
        self.jogadores = jogadores
        self.modo_gelo = modo_gelo
        self.confirmados = set()

    @discord.ui.button(label="Continuar", style=discord.ButtonStyle.success, emoji="✅")
    async def continuar(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user not in self.jogadores:
            await interaction.response.send_message("❌ Você não faz parte desta partida!", ephemeral=True)
            return

        if user.id in self.confirmados:
            await interaction.response.send_message("⚠️ Você já confirmou!", ephemeral=True)
            return

        self.confirmados.add(user.id)

        if len(self.confirmados) < len(self.jogadores):
            embed_confirmacao = discord.Embed(
                title="✅ Partida Confirmada",
                description=f"{user.mention} confirmou a aposta!\nO outro jogador precisa confirmar para continuar.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed_confirmacao)
        else:
            # 1. LIMPA TODO O TÓPICO ANTES DE MANDAR O PIX (Apaga as confirmações e conversas)
            try:
                await interaction.channel.purge(limit=100)
            except Exception:
                pass

            # 2. ROTATIVIDADE DO MEDIADOR
            mediador_sorteado = None
            if fila_mediadores:
                mediador_sorteado = fila_mediadores.pop(0)
                fila_mediadores.append(mediador_sorteado)
                await atualizar_painel_mediador()
                try:
                    await interaction.channel.add_user(mediador_sorteado)
                except Exception:
                    pass

            # 3. PEGA DADOS DO PIX
            pix_info = dados_pix.get(
                mediador_sorteado.id if mediador_sorteado else None,
                {
                    "nome": "Não cadastrado",
                    "chave": "Aguardando cadastro do mediador...",
                    "qr": "https://cdn.discordapp.com/embed/avatars/0.png"
                }
            )

            # 4. PREPARA OS EMBEDS
            embed_aposta = discord.Embed(title="✅ Partida Confirmada", color=discord.Color.dark_theme())
            embed_aposta.add_field(name="🎮 Estilo de Jogo", value=f"1x1 ({self.modo_gelo})", inline=False)
            med_text = mediador_sorteado.mention if mediador_sorteado else "Nenhum mediador na fila"
            embed_aposta.add_field(name="Informações da Aposta", value=f"Valor da Sala: R$ 0,15\nMediador:\n{med_text}", inline=False)
            embed_aposta.add_field(name="💰 Valor da Aposta", value="R$ 0,50", inline=False)
            j1, j2 = self.jogadores[0], self.jogadores[1]
            embed_aposta.add_field(name="👤 Jogadores", value=f"{j1.mention}\n{j2.mention}", inline=False)

            embed_pix = discord.Embed(color=discord.Color.dark_theme())
            embed_pix.set_image(url=pix_info["qr"])
            embed_pix.set_footer(text=f"Valor a pagar: R$ 0,65\nNome: {pix_info['nome']}\nChave:\n{pix_info['chave']}")

            texto_chamada = f"🔔 **Mediador Sorteado:** {mediador_sorteado.mention}" if mediador_sorteado else "⚠️ Nenhum mediador disponível."

            # 5. ENVIA TUDO NO TÓPICO JÁ LIMPO COM O PINGO DIRETO NO TEXTO
            await interaction.channel.send(content=texto_chamada, embeds=[embed_aposta, embed_pix])

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, emoji="✖️")
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user not in self.jogadores:
            await interaction.response.send_message("❌ Você não faz parte desta partida!", ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        embed_cancelado = discord.Embed(
            title="❌ Partida Cancelada",
            description=f"{user.mention} cancelou a partida.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=embed_cancelado)

class FilaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Gelo Normal", style=discord.ButtonStyle.success, emoji=EMOJI_GELO)
    async def gelo_normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.entrar_na_fila(interaction, "Gelo Normal")

    @discord.ui.button(label="Gelo Infinito", style=discord.ButtonStyle.success, emoji=EMOJI_GELO)
    async def gelo_infinito(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.entrar_na_fila(interaction, "Gelo Infinito")

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

    async def entrar_na_fila(self, interaction: discord.Interaction, modo_gelo: str):
        user = interaction.user

        if user in fila_jogadores:
            await interaction.response.send_message("⚠️ Você já está na fila!", ephemeral=True)
            return

        if len(fila_jogadores) >= TAMANHO_MAXIMO_JOGADORES:
            await interaction.response.send_message("❌ A fila já está cheia!", ephemeral=True)
            return

        fila_jogadores.append(user)

        if len(fila_jogadores) == TAMANHO_MAXIMO_JOGADORES:
            jogadores_partida = fila_jogadores.copy()
            fila_jogadores.clear()

            await interaction.response.edit_message(embed=criar_embed_fila(), view=self)
            await interaction.followup.send(f"✅ Fila lotada! Criando partida...", ephemeral=True)

            channel = interaction.channel
            j1, j2 = jogadores_partida[0], jogadores_partida[1]

            # Cria Tópico Privado
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

            # Adiciona os Jogadores
            await topico.add_user(j1)
            await topico.add_user(j2)

            embed_partida = criar_embed_partida(jogadores_partida, modo_gelo)
            view_confirmacao = ConfirmarPartidaView(jogadores_partida, modo_gelo)

            await topico.send(
                content=f"🔔 {j1.mention} {j2.mention}",
                embed=embed_partida,
                view=view_confirmacao
            )
        else:
            embed_atualizado = criar_embed_fila()
            await interaction.response.edit_message(embed=embed_atualizado, view=self)
            await interaction.followup.send(f"✅ {user.mention} entrou na fila ({modo_gelo})!", ephemeral=True)

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
    
