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
EMOJI_BONECO   = "<:emoji_3:1535462271906746408>"
EMOJI_GELO     = "<:emoji_4:1535465191481810954>"

# Dicionário para salvar as chaves pix dos usuários
dados_pix = {}

# ------------------------------------------------------------------
# Modal para Cadastro de Pix
# ------------------------------------------------------------------
class PixModal(discord.ui.Modal, title="Cadastrar Chave Pix"):
    chave_pix = discord.ui.TextInput(
        label="Chave Pix",
        placeholder="Aceita chave aleatória, número de telefone e CPF...",
        style=discord.TextStyle.short,
        required=True
    )
    
    link_qrcode = discord.ui.TextInput(
        label="Link QR Code",
        placeholder="Cole o link do seu QR Code aqui...",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        dados_pix[interaction.user.id] = {
            "chave": self.chave_pix.value,
            "qrcode": self.link_qrcode.value
        }

        embed = discord.Embed(
            title="✅ Pix Cadastrado com Sucesso!",
            description="Sua chave Pix e QR Code foram salvos com sucesso.",
            color=discord.Color.green()
        )
        embed.add_field(name="🔑 Chave", value=self.chave_pix.value, inline=False)
        embed.add_field(name="🖼️ QR Code", value=f"[Clique aqui para ver]({self.link_qrcode.value})", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ------------------------------------------------------------------
# View do Botão de Cadastro de Pix (Cor Preta / Secondary)
# ------------------------------------------------------------------
class PixView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="clique aqui para cadastrar", style=discord.ButtonStyle.secondary, emoji="❖")
    async def cadastrar_pix(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PixModal())

# ------------------------------------------------------------------
# Função que gera a Embed da Fila no Chat (Painel Público)
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
# View dos Botões de Confirmação no Tópico Privado
# ------------------------------------------------------------------
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

        await interaction.response.defer()

        if len(self.confirmados) < len(self.jogadores):
            embed_confirmacao = discord.Embed(
                title="✅ Partida Confirmada",
                description=f"{user.mention} confirmou a aposta!\nO outro jogador precisa confirmar para continuar.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed_confirmacao)
        else:
            embed_final = discord.Embed(
                title="🚀 Ambos Confirmaram!",
                description="Todos os jogadores confirmaram! A partida está liberada. Boa sorte!",
                color=discord.Color.green()
            )
            for item in self.children:
                item.disabled = True
            
            await interaction.message.edit(view=self)
            await interaction.followup.send(embed=embed_final)

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, emoji="✖️")
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        if user not in self.jogadores:
            await interaction.response.send_message("❌ Você não faz parte desta partida!", ephemeral=True)
            return

        await interaction.response.defer()

        for item in self.children:
            item.disabled = True

        embed_cancelado = discord.Embed(
            title="❌ Partida Cancelada",
            description=f"{user.mention} cancelou a partida.",
            color=discord.Color.red()
        )
        await interaction.message.edit(view=self)
        await interaction.followup.send(embed=embed_cancelado)

# ------------------------------------------------------------------
# Botões interativos do painel principal (Fila)
# ------------------------------------------------------------------
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
            jogadores_partida = fila_jogadores.copy()
            fila_jogadores.clear()

            await interaction.response.edit_message(embed=criar_embed_fila(), view=self)
            await interaction.followup.send(f"✅ Fila lotada! Criando partida...", ephemeral=True)

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

            embed_partida = criar_embed_partida(jogadores_partida, modo_gelo)
            view_confirmacao = ConfirmarPartidaView(jogadores_partida)

            await topico.send(
                content=f"🔔 {j1.mention} {j2.mention}",
                embed=embed_partida,
                view=view_confirmacao
            )
        else:
            embed_atualizado = criar_embed_fila()
            await interaction.response.edit_message(embed=embed_atualizado, view=self)
            await interaction.followup.send(f"✅ {user.mention} entrou na fila ({modo_gelo})!", ephemeral=True)

# ------------------------------------------------------------------
# Eventos e Comandos
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

# Comando de texto !pix
@bot.command(name="pix")
async def comando_pix(ctx):
    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = discord.Embed(
        title="💳 Cadastro de Chave Pix",
        description="clique aqui para cadastrar seu Pix, pois se não cadastrar não terá como o cliente saber sua chave.",
        color=discord.Color.blue()
    )
    embed.set_image(url="https://cdn.discordapp.com/embed/avatars/0.png") # Altere para o link do seu Banner se desejar
    
    view = PixView()
    await ctx.send(embed=embed, view=view)

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ ERRO: A variável 'TOKEN' não existe no Railway!")
else:
    bot.run(TOKEN)
                
