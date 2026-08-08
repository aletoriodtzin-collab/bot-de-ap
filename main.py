import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Armazena os dados da fila
fila_jogadores = []
fila_mediadores = []
TAMANHO_MAXIMO = 2 

# Dicionário para armazenar o Pix de cada mediador cadastrado
pix_mediadores = {}

mensagem_painel_med = None

EMOJI_CONTROLE = "<:emoji_1:1535450507160846506>"
EMOJI_DINHEIRO = "<:emoji_2:1535453860947034193>"
EMOJI_BONECO   = "<:emoji_3:1535462271906746408>"
EMOJI_GELO     = "<:emoji_4:1535465191481810954>"

# ------------------------------------------------------------------
# FORMULÁRIO (MODAL) DE CADASTRO DO PIX DO MEDIADOR
# ------------------------------------------------------------------
class FormularioPixModal(discord.ui.Modal, title="Cadastrar Pix"):
    chave_pix = discord.ui.TextInput(
        label="Chave Pix ou Copia e Cola",
        placeholder="Cole a chave Pix ou o código Copia e Cola aqui...",
        style=discord.TextStyle.paragraph,
        required=True
    )

    nome_conta = discord.ui.TextInput(
        label="Nome no app do banco",
        placeholder="Ex: Luan Bruno",
        style=discord.TextStyle.short,
        required=True
    )

    link_qr = discord.ui.TextInput(
        label="Link do QR Code (opcional)",
        placeholder="Cole o link da imagem do seu QR Code...",
        style=discord.TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        chave = self.chave_pix.value
        nome = self.nome_conta.value
        qr = self.link_qr.value if self.link_qr.value else ""

        user_id_int = interaction.user.id
        user_id_str = str(interaction.user.id)

        dados = {
            "nome": nome,
            "chave": chave,
            "qr": qr
        }

        pix_mediadores[user_id_int] = dados
        pix_mediadores[user_id_str] = dados

        await interaction.response.send_message(
            f"✅ **Seu Pix foi cadastrado/atualizado com sucesso!**\n"
            f"📌 **Nome:** {nome}",
            ephemeral=True
        )

class PixView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cadastrar Meu Pix", style=discord.ButtonStyle.success, emoji="💳")
    async def abrir_formulario(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FormularioPixModal())

@bot.tree.command(name="pix", description="Cadastre o seu Pix para receber os pagamentos das partidas")
async def slash_pix(interaction: discord.Interaction):
    embed = discord.Embed(
        title="💳 Cadastro de Pix do Mediador",
        description="Clique no botão abaixo para cadastrar o seu Pix. É para este Pix que os jogadores farão o pagamento das partidas que você mediar!",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")

    view = PixView()
    # Alterado para público (ephemeral=False) conforme solicitado
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

# ------------------------------------------------------------------
# SISTEMA DE SUPORTE / MODERAÇÃO (TÓPICO PÚBLICO)
# ------------------------------------------------------------------
class TicketModView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Chamar Moderação", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def chamar_moderacao(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        channel = interaction.channel

        try:
            topico = await channel.create_thread(
                name=f"🛡️-suporte-{user.name}",
                type=discord.ChannelType.public_thread,
                auto_archive_duration=60
            )
        except Exception:
            topico = await channel.create_thread(
                name=f"🛡️-suporte-{user.name}",
                auto_archive_duration=60
            )

        await topico.add_user(user)

        embed_ticket = discord.Embed(
            title="🛡️ Atendimento com a Moderação",
            description=f"Olá {user.mention}! Um moderador irá te atender em breve.\nDescreva o seu problema ou envie as provas necessárias aqui.",
            color=discord.Color.blue()
        )

        await topico.send(content=f"🔔 {user.mention}", embed=embed_ticket)
        await interaction.response.send_message(f"✅ Seu ticket de atendimento foi criado com sucesso: {topico.mention}", ephemeral=True)

# ------------------------------------------------------------------
# PAINEL DA FILA DE MEDIADORES (/med)
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

@bot.tree.command(name="med", description="Abre o painel da fila de mediadores")
async def slash_med(interaction: discord.Interaction):
    global mensagem_painel_med
    await interaction.response.send_message(embed=criar_embed_mediadores(), view=MedView())
    mensagem_painel_med = await interaction.original_response()

# ------------------------------------------------------------------
# ESTRUTURA DA FILA DE PARTIDA
# ------------------------------------------------------------------
def criar_embed_fila(modo_jogo="1x1 Mobile", valor_aposta="R$ 0,50"):
    embed = discord.Embed(
        title=f"➔ {modo_jogo} — Fila de Partida",
        color=discord.Color.green()
    )
    embed.add_field(name=f"{EMOJI_CONTROLE} Modo", value=modo_jogo, inline=False)
    embed.add_field(name=f"{EMOJI_DINHEIRO} Valor", value=valor_aposta, inline=False)

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
    def __init__(self, jogadores, mediador):
        super().__init__(timeout=None)
        self.jogadores = jogadores
        self.mediador = mediador
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
            await interaction.response.send_message(f"✅ {user.mention} confirmou! Aguardando o outro jogador...", ephemeral=True)
        else:
            await interaction.response.send_message(f"✅ {user.mention} confirmou! Carregando dados do Pix...", ephemeral=True)

            dados_pix = pix_mediadores.get(self.mediador.id) or pix_mediadores.get(str(self.mediador.id))

            embed_pix = discord.Embed(
                title="💳 Realize o Pagamento",
                color=discord.Color.gold()
            )

            if not dados_pix:
                embed_pix.description = f"⚠️ {self.mediador.mention}, você ainda não cadastrou o seu Pix!\nUse o comando `/pix` para cadastrar antes de mediar."
                embed_pix.color = discord.Color.red()
            else:
                embed_pix.description = "Ambos os jogadores confirmaram! Copie a chave abaixo para realizar o pagamento:"
                embed_pix.add_field(name="👤 Nome no Banco", value=dados_pix["nome"], inline=False)
                embed_pix.add_field(name="🔑 Pix Copia e Cola / Chave", value=f"```\n{dados_pix['chave']}\n```", inline=False)
                
                qr_link = dados_pix.get("qr")
                if qr_link and qr_link.startswith("http"):
                    embed_pix.set_image(url=qr_link)
                    
                embed_pix.set_footer(text=f"Mediador responsável: {self.mediador.name}. Envie o comprovante aqui.")

            if isinstance(interaction.channel, discord.Thread):
                await interaction.channel.send(content=f"🔔 {self.jogadores[0].mention} {self.jogadores[1].mention}", embed=embed_pix)
            else:
                await interaction.followup.send(content=f"🔔 {self.jogadores[0].mention} {self.jogadores[1].mention}", embed=embed_pix)

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, emoji="✖️")
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user not in self.jogadores and user != self.mediador:
            await interaction.response.send_message("❌ Você não tem permissão para cancelar esta partida!", ephemeral=True)
            return

        embed_cancelado = discord.Embed(
            title="❌ Partida Cancelada",
            description=f"{user.mention} cancelou a partida. O tópico será apagado.",
            color=discord.Color.red()
        )
        
        await interaction.response.send_message(embed=embed_cancelado)

        if isinstance(interaction.channel, discord.Thread):
            try:
                import asyncio
                await asyncio.sleep(2)
                await interaction.channel.delete()
            except Exception as e:
                print(f"Erro ao deletar o tópico: {e}")

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
                fila_jogadores.pop() 
                return

            mediador = fila_mediadores.pop(0)
            fila_mediadores.append(mediador)
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
                    type=discord.ChannelType.public_thread,
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
            view_confirmacao = ConfirmarPartidaView(jogadores_partida, mediador)

            await topico.send(
                content=f"🔔 {j1.mention} {j2.mention} | Mediador: {mediador.mention}",
                embed=embed_partida,
                view=view_confirmacao
            )
        else:
            embed_atualizado = criar_embed_fila()
            await interaction.response.edit_message(embed=embed_atualizado, view=self)
            await interaction.followup.send(f"✅ {user.mention} entrou na fila ({modo_gelo})!", ephemeral=True)

@bot.tree.command(name="fila", description="Abre o painel da fila de partidas 1x1")
async def slash_fila(interaction: discord.Interaction):
    embed = criar_embed_fila()
    view = FilaView()
    await interaction.response.send_message(embed=embed, view=view)

# ------------------------------------------------------------------
# NOVO COMANDO: /criar_15_filas (Corrigido com View/Select separado)
# ------------------------------------------------------------------
class SelectModoFila(discord.ui.Select):
    def __init__(self, canais_ids, valores):
        self.canais_ids = canais_ids
        self.valores = valores
        options = [
            discord.SelectOption(label="4v4", value="4v4"),
            discord.SelectOption(label="3v3", value="3v3"),
            discord.SelectOption(label="2v2", value="2v2"),
            discord.SelectOption(label="1v1", value="1v1"),
        ]
        super().__init__(placeholder="Escolha o modo de jogo para as filas", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        modo = self.values[0]
        await interaction.response.edit_message(content=f"⚙️ Gerando as 15 filas no modo **{modo}**, por favor aguarde...", view=None)

        valor_atual_idx = 0
        for canal_id in self.canais_ids:
            canal = interaction.guild.get_channel(int(canal_id))
            if canal:
                for _ in range(3):
                    val = self.valores[valor_atual_idx % len(self.valores)]
                    embed = criar_embed_fila(modo_jogo=modo, valor_aposta=f"R$ {val}")
                    view = FilaView()
                    await canal.send(embed=embed, view=view)
                    valor_atual_idx += 1

        await interaction.followup.send("✅ As 15 filas foram criadas com sucesso nos canais!", ephemeral=True)

class ViewSelecaoModo(discord.ui.View):
    def __init__(self, canais_ids, valores):
        super().__init__(timeout=60)
        self.add_item(SelectModoFila(canais_ids, valores))

class ModalCriarFilas(discord.ui.Modal, title="Configurar 15 Filas"):
    canais_input = discord.ui.TextInput(
        label="IDs dos até 5 canais (separados por vírgula)",
        placeholder="Ex: 123456789, 987654321...",
        style=discord.TextStyle.paragraph,
        required=True
    )

    valores_input = discord.ui.TextInput(
        label="Valores (separados por vírgula)",
        placeholder="Ex: 0.50, 1.00, 2.00",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            canais_ids = [c.strip() for c in self.canais_input.value.split(",")]
            valores = [v.strip() for v in self.valores_input.value.split(",")]

            if len(canais_ids) > 5:
                await interaction.response.send_message("❌ Você pode selecionar no máximo 5 canais!", ephemeral=True)
                return

            # Envia uma mensagem com o menu Select para escolher o modo (solução correta do Discord)
            view = ViewSelecaoModo(canais_ids, valores)
            await interaction.response.send_message("🎮 Agora escolha abaixo o **modo de jogo** para gerar as filas:", view=view, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ocorreu um erro ao processar os dados: {e}", ephemeral=True)

@bot.tree.command(name="criar_15_filas", description="Gera 15 filas distribuídas em até 5 canais")
async def slash_criar_15_filas(interaction: discord.Interaction):
    await interaction.response.send_modal(ModalCriarFilas())

# ------------------------------------------------------------------
# PAINEL DE CONTROLE DA SALA DO MEDIADOR (!sala_criada)
# ------------------------------------------------------------------
class PainelMediadorModal(discord.ui.Modal, title="Painel de Controle da Partida"):
    escolha_vencedor_input = discord.ui.TextInput(
        label="Escolha o vencedor",
        placeholder="Nome ou menção do jogador vencedor...",
        style=discord.TextStyle.short,
        required=False
    )

    motivo_wo = discord.ui.TextInput(
        label="Vitória por W.O (Motivo / Vencedor)",
        placeholder="Descreva o W.O se necessário...",
        style=discord.TextStyle.short,
        required=False
    )

    dar_win_input = discord.ui.TextInput(
        label="Dar Win",
        placeholder="Nome do jogador para computar a Win...",
        style=discord.TextStyle.short,
        required=False
    )

    reembolsar_input = discord.ui.TextInput(
        label="Reembolsar",
        placeholder="Motivo do reembolso...",
        style=discord.TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        resposta = "⚙️ **Ações do Painel Registradas:**\n"
        
        if self.escolha_vencedor_input.value:
            resposta += f"🏆 **Vencedor Escolhido:** {self.escolha_vencedor_input.value}\n"
        if self.motivo_wo.value:
            resposta += f"⚠️ **W.O:** {self.motivo_wo.value}\n"
        if self.dar_win_input.value:
            resposta += f"✅ **Win Computada:** {self.dar_win_input.value}\n"
        if self.reembolsar_input.value:
            resposta += f"💸 **Reembolso:** {self.reembolsar_input.value}\n"

        if resposta == "⚙️ **Ações do Painel Registradas:**\n":
            resposta = "⚠️ Nenhuma alteração foi preenchida no modal."

        await interaction.response.send_message(resposta, ephemeral=True)

class PainelMediadorView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Painel", style=discord.ButtonStyle.primary, emoji="⚙️")
    async def abrir_painel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PainelMediadorModal())

@bot.command(name="sala_criada")
async def sala_criada(ctx):
    try:
        await ctx.message.delete()
    except Exception:
        pass

    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("❌ Este comando só pode ser utilizado dentro do tópico da partida!", delete_after=5)
        return

    embed = discord.Embed(
        title="⚙️ Painel de Controle da Partida",
        description="Clique no botão abaixo para abrir o formulário e gerenciar o desfecho da partida:",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Painel exclusivo para controle do Mediador.")

    view = PainelMediadorView()
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"✅ Slash commands sincronizados com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao sincronizar comandos: {e}")
    print(f"✅ Bot online com sucesso como: {bot.user}")

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ ERRO: A variável 'TOKEN' não existe no Railway!")
else:
    bot.run(TOKEN)
