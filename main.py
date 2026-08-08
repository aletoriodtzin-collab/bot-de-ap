import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Armazena os dados da fila na memória
fila_jogadores = []
fila_mediadores = []
TAMANHO_MAXIMO = 2  # 1v1

# Variável para armazenar a mensagem fixa do painel de mediadores e atualizar automaticamente
mensagem_painel_med = None

# Emojis personalizados configurados
EMOJI_CONTROLE = "<:emoji_1:1535450507160846506>"
EMOJI_DINHEIRO = "<:emoji_2:1535453860947034193>"
EMOJI_BONECO   = "<:emoji_3:1535462271906746408>"
EMOJI_GELO     = "<:emoji_4:1535465191481810954>"

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
        placeholder="Ex: João Silva",
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
        chave = self.chave_pix.value
        nome = self.nome_conta.value
        qr = self.link_qr.value if self.link_qr.value else "Não informado"

        await interaction.response.send_message(
            f"✅ **Pix cadastrado com sucesso!**\n"
            f"📌 **Nome:** {nome}\n"
            f"🔑 **Chave:** {chave}\n"
            f"🖼️ **Link QR Code:** {qr}",
            ephemeral=True
        )

# ------------------------------------------------------------------
# BOTÃO DE CADASTRO DO PIX
# ------------------------------------------------------------------
class PixView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cadastrar Pix", style=discord.ButtonStyle.success, emoji="💳")
    async def abrir_formulario(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FormularioPixModal())

# ------------------------------------------------------------------
# COMANDO DO PAINEL DO PIX (!pix)
# ------------------------------------------------------------------
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
# PAINEL DA FILA DE MEDIADORES (!med)
# ------------------------------------------------------------------
def criar_embed_mediadores():
    embed = discord.Embed(
        title="🛡️ Fila de Mediadores",
        description="Você tem que entrar na fila para começar a mediar, caso contrário nenhuma partida será iniciada!",
        color=discord.Color.blue()
    )
    
    if not fila_mediadores:
        texto = "*Nenhum mediador disponível no momento.*"
    else:
        texto = "\n".join([f"{i+1}- {m.mention}" for i, m in enumerate(fila_mediadores)])
    
    embed.add_field(name="Mediadores em espera:", value=texto, inline=False)
    return embed

async def atualizar_painel_mediadores():
    global mensagem_painel_med
    if mensagem_painel_med:
        try:
            await mensagem_painel_med.edit(embed=criar_embed_mediadores())
        except Exception:
            pass

class MedView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def entrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in fila_mediadores:
            await interaction.response.send_message("❌ Você já está na fila de mediadores!", ephemeral=True)
            return
        fila_mediadores.append(interaction.user)
        
        await interaction.response.edit_message(embed=criar_embed_mediadores())
        await interaction.followup.send("✅ Você entrou na fila de mediadores!", ephemeral=True)
        await atualizar_painel_mediadores()

    @discord.ui.button(label="Sair da Fila", style=discord.ButtonStyle.danger, emoji="❌")
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in fila_mediadores:
            fila_mediadores.remove(interaction.user)
            
            await interaction.response.edit_message(embed=criar_embed_mediadores())
            await interaction.followup.send("🚪 Você saiu da fila de mediadores.", ephemeral=True)
            await atualizar_painel_mediadores()
        else:
            await interaction.response.send_message("❌ Você não está na fila!", ephemeral=True)

@bot.command(name="med")
async def painel_med(ctx):
    global mensagem_painel_med
    try:
        await ctx.message.delete()
    except Exception:
        pass

    mensagem_painel_med = await ctx.send(embed=criar_embed_mediadores(), view=MedView())

# ------------------------------------------------------------------
# ESTRUTURA DA FILA DE PARTIDA
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

def criar_embed_partida(jogadores, modo_gelo, mediador):
    j1, j2 = jogadores[0], jogadores[1]
    embed = discord.Embed(
        title="⚔️ Partida Confirmada — 1x1",
        color=discord.Color.green()
    )
    embed.add_field(name=f"{EMOJI_CONTROLE} Modo de Jogo", value=f"{modo_gelo}", inline=False)
    embed.add_field(name=f"{EMOJI_DINHEIRO} Aposta", value="R$ 0,50", inline=False)
    embed.add_field(name=f"{EMOJI_BONECO} Jogadores", value=f"{j1.mention} vs {j2.mention}", inline=False)
    embed.add_field(name="🛡️ Mediador", value=f"{mediador.mention}", inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
    return embed

class ConfirmarPartidaView(discord.ui.View):
    def __init__(self, jogadores):
        super().__init__(timeout=None)
        self.jogadores = jogadores
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
            embed_final = discord.Embed(
                title="🚀 Ambos Confirmaram!",
                description="Todos os jogadores confirmaram! A partida está liberada. Boa sorte!",
                color=discord.Color.green()
            )
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(embed=embed_final)

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

        if len(fila_jogadores) >= TAMANHO_MAXIMO:
            await interaction.response.send_message("❌ A fila já está cheia!", ephemeral=True)
            return

        fila_jogadores.append(user)

        if len(fila_jogadores) == TAMANHO_MAXIMO:
            if not fila_mediadores:
                await interaction.response.send_message("❌ Não há mediadores na fila! Aguarde um mediador entrar.", ephemeral=True)
                fila_jogadores.pop() # Remove o último jogador que tentou entrar
                return

            # Pega o primeiro mediador, tira da frente e joga pro final da lista
            mediador = fila_mediadores.pop(0)
            fila_mediadores.append(mediador)

            # Atualiza automaticamente o painel de mediadores no canal para refletir a troca de posição em tempo real
            await atualizar_painel_mediadores()

            jogadores_partida = fila_jogadores.copy()
            fila_jogadores.clear()

            await interaction.response.edit_message(embed=criar_embed_fila(), view=self)
            await interaction.followup.send(f"✅ Fila lotada! Criando partida com o mediador {mediador.name}...", ephemeral=True)

            channel = interaction.channel
            j1, j2 = jogadores_partida[0], jogadores_partida[1]

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

            await topico.add_user(j1)
            await topico.add_user(j2)
            await topico.add_user(mediador)

            embed_partida = criar_embed_partida(jogadores_partida, modo_gelo, mediador)
            view_confirmacao = ConfirmarPartidaView(jogadores_partida)

            await topico.send(
                content=f"🔔 {j1.mention} {j2.mention} | Mediador: {mediador.mention}",
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
            
