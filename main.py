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

# ------------------------------------------------------------------
# CONFIGURAÇÕES DO BOT (COMANDO /config_bot)
# ------------------------------------------------------------------
config_bot_dados = {
    "dono_id": "1461858587080130663",
    "cargo_comandos": None,
    "cargo_criar_fila": None,
    "cargo_criar_pix": None,
    "cargo_config": None,
    "cargo_criar_med": None
}

class ConfigBotModal(discord.ui.Modal, title="Configurações do Bot"):
    dono_id = discord.ui.TextInput(
        label="Quem pode mexer no bot? (ID)",
        placeholder="Ex: 1461858587080130663",
        style=discord.TextStyle.short,
        required=False
    )
    cargo_comandos = discord.ui.TextInput(
        label="Quem pode usar os comandos? (Cargo)",
        placeholder="Nome ou ID do cargo...",
        style=discord.TextStyle.short,
        required=False
    )
    cargo_criar_fila = discord.ui.TextInput(
        label="Quem pode criar fila? (Cargo)",
        placeholder="Nome ou ID do cargo...",
        style=discord.TextStyle.short,
        required=False
    )
    cargo_criar_pix = discord.ui.TextInput(
        label="Quem pode criar painel Pix? (Cargo)",
        placeholder="Nome ou ID do cargo...",
        style=discord.TextStyle.short,
        required=False
    )
    cargo_config = discord.ui.TextInput(
        label="Quem pode mexer nas configs? (Cargo)",
        placeholder="Nome ou ID do cargo...",
        style=discord.TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        if self.dono_id.value:
            config_bot_dados["dono_id"] = self.dono_id.value.strip()
        if self.cargo_comandos.value:
            config_bot_dados["cargo_comandos"] = self.cargo_comandos.value.strip()
        if self.cargo_criar_fila.value:
            config_bot_dados["cargo_criar_fila"] = self.cargo_criar_fila.value.strip()
        if self.cargo_criar_pix.value:
            config_bot_dados["cargo_criar_pix"] = self.cargo_criar_pix.value.strip()
        if self.cargo_config.value:
            config_bot_dados["cargo_config"] = self.cargo_config.value.strip()

        await interaction.response.send_message("✅ **Configurações do bot atualizadas com sucesso!**", ephemeral=True)

class ConfigBotModalExtra(discord.ui.Modal, title="Configurações (Parte 2)"):
    cargo_criar_med = discord.ui.TextInput(
        label="Criar fila de mediador? (Cargo)",
        placeholder="Nome ou ID do cargo...",
        style=discord.TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        if self.cargo_criar_med.value:
            config_bot_dados["cargo_criar_med"] = self.cargo_criar_med.value.strip()

        await interaction.response.send_message("✅ **Configurações adicionais salvas com sucesso!**", ephemeral=True)

class ConfigBotView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Editar Configurações (1/2)", style=discord.ButtonStyle.primary, emoji="⚙️")
    async def abrir_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfigBotModal())

    @discord.ui.button(label="Editar Configurações (2/2)", style=discord.ButtonStyle.secondary, emoji="🛡️")
    async def abrir_config_extra(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfigBotModalExtra())

@bot.tree.command(name="config_bot", description="Painel de configurações gerais e permissões do bot")
async def slash_config_bot(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚙️ Painel de Configurações do Bot",
        description="Gerencie abaixo quem tem permissão para executar ações e administrar o servidor.",
        color=discord.Color.blurple()
    )
    embed.add_field(name="👤 Dono do Bot (ID)", value=config_bot_dados["dono_id"] or "Não definido", inline=False)
    embed.add_field(name="⌨️ Cargo p/ Comandos", value=config_bot_dados["cargo_comandos"] or "Não definido", inline=True)
    embed.add_field(name="➔ Cargo p/ Criar Fila", value=config_bot_dados["cargo_criar_fila"] or "Não definido", inline=True)
    embed.add_field(name="💳 Cargo p/ Painel Pix", value=config_bot_dados["cargo_criar_pix"] or "Não definido", inline=True)
    embed.add_field(name="🔧 Cargo p/ Mexer Config", value=config_bot_dados["cargo_config"] or "Não definido", inline=True)
    embed.add_field(name="🛡️ Cargo p/ Fila Mediador", value=config_bot_dados["cargo_criar_med"] or "Não definido", inline=True)

    view = ConfigBotView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

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
def criar_embed_fila(modo_jogo="1v1 Mobile", valor_aposta="R$ 0,50"):
    embed = discord.Embed(
        title=f"➔ [{modo_jogo}] Fila de Aposta",
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

def criar_embed_partida(jogadores, modo_gelo, mediador, modo_jogo="1v1"):
    j1, j2 = jogadores[0], jogadores[1]
    embed = discord.Embed(
        title=f"⚔️ Partida Confirmada — {modo_jogo}",
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
    def __init__(self, modo_jogo="1v1"):
        super().__init__(timeout=None)
        self.modo_jogo = modo_jogo

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
            embed_atualizado = criar_embed_fila(modo_jogo=self.modo_jogo)
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

            await interaction.response.edit_message(embed=criar_embed_fila(modo_jogo=self.modo_jogo), view=self)
            await interaction.followup.send(f"✅ Fila lotada! Criando partida com o mediador {mediador.name}...", ephemeral=True)

            channel = interaction.channel
            j1, j2 = jogadores_partida[0], jogadores_partida[1]

            try:
                topico = await channel.create_thread(
                    name=f"🎮-{self.modo_jogo}-{j1.name}-vs-{j2.name}",
                    type=discord.ChannelType.public_thread,
                    auto_archive_duration=60
                )
            except Exception:
                topico = await channel.create_thread(
                    name=f"🎮-{self.modo_jogo}-{j1.name}-vs-{j2.name}",
                    auto_archive_duration=60
                )

            await topico.add_user(j1)
            await topico.add_user(j2)
            await topico.add_user(mediador)

            embed_partida = criar_embed_partida(jogadores_partida, modo_gelo, mediador, modo_jogo=self.modo_jogo)
            view_confirmacao = ConfirmarPartidaView(jogadores_partida, mediador)

            await topico.send(
                content=f"🔔 {j1.mention} {j2.mention} | Mediador: {mediador.mention}",
                embed=embed_partida,
                view=view_confirmacao
            )
        else:
            embed_atualizado = criar_embed_fila(modo_jogo=self.modo_jogo)
            await interaction.response.edit_message(embed=embed_atualizado, view=self)
            await interaction.followup.send(f"✅ {user.mention} entrou na fila ({modo_gelo})!", ephemeral=True)

# ------------------------------------------------------------------
# NOVO COMANDO: /criar_15_filas (Com seleção de canais por botões e valores com vírgula fixados)
# ------------------------------------------------------------------
class CanalSelect(discord.ui.ChannelSelect):
    def __init__(self, valores, modo):
        self.valores = valores
        self.modo = modo
        super().__init__(
            placeholder="Selecione até 5 canais...",
            min_values=1,
            max_values=5,
            channel_types=[discord.ChannelType.text]
        )

    async def callback(self, interaction: discord.Interaction):
        canais_selecionados = self.values
        await interaction.response.edit_message(content=f"⚙️ Gerando as 15 filas no modo **{self.modo}**, por favor aguarde...", view=None)

        valor_atual_idx = 0
        for canal in canais_selecionados:
            for _ in range(3):
                val = self.valores[valor_atual_idx % len(self.valores)]
                val_str = str(val).replace(".", ",")
                embed = criar_embed_fila(modo_jogo=self.modo, valor_aposta=f"R$ {val_str}")
                view = FilaView(modo_jogo=self.modo)
                await canal.send(embed=embed, view=view)
                valor_atual_idx += 1

        await interaction.followup.send("✅ As 15 filas foram criadas com sucesso nos canais selecionados!", ephemeral=True)

class ViewSelecaoCanais(discord.ui.View):
    def __init__(self, valores, modo):
        super().__init__(timeout=60)
        self.add_item(CanalSelect(valores, modo))

class SelectModoFila(discord.ui.Select):
    def __init__(self, valores):
        self.valores = valores
        options = [
            discord.SelectOption(label="4v4", value="4v4"),
            discord.SelectOption(label="3v3", value="3v3"),
            discord.SelectOption(label="2v2", value="2v2"),
            discord.SelectOption(label="1v1", value="1v1"),
        ]
        super().__init__(placeholder="Escolha o modo de jogo (1v1, 2v2, 3v3 ou 4v4)", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        modo = self.values[0]
        view_canais = ViewSelecaoCanais(self.valores, modo)
        await interaction.response.edit_message(content=f"📁 Modo selecionado: **{modo}**.\nAgora **clique no botão abaixo para selecionar os canais**:", view=view_canais)

class ViewSelecaoModoFila(discord.ui.View):
    def __init__(self, valores):
        super().__init__(timeout=60)
        self.add_item(SelectModoFila(valores))

class ModalCriarFilas(discord.ui.Modal, title="Configurar 15 Filas"):
    valores_input = discord.ui.TextInput(
        label="Valores (use apenas vírgula, ex: 0,50, 1,00)",
        placeholder="Ex: 0,50, 1,00, 2,00",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            input_cru = self.valores_input.value.replace(".", ",")
            valores = [v.strip() for v in input_cru.split(",")]

            view_modo = ViewSelecaoModoFila(valores)
            await interaction.response.send_message("🎮 Escolha abaixo se este canal é **1v1, 2v2, 3v3 ou 4v4**:", view=view_modo, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ocorreu an erro ao processar os valores: {e}", ephemeral=True)

@bot.tree.command(name="criar_15_filas", description="Gera 15 filas escolhendo os canais por botões e definindo o modo")
async def slash_criar_15_filas(interaction: discord.Interaction):
    await interaction.response.send_modal(ModalCriarFilas())

# ------------------------------------------------------------------
# NOVO PAINEL DE CONTROLE DA SALA DO MEDIADOR (!sala_criada)
# ------------------------------------------------------------------
class VencedorSelect(discord.ui.Select):
    def __init__(self, membros):
        options = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in membros]
        super().__init__(placeholder="Selecione o jogador vencedor...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        vencedor_id = int(self.values[0])
        vencedor = interaction.guild.get_member(vencedor_id) or await interaction.guild.fetch_member(vencedor_id)
        await interaction.response.send_message(f"🏆 **Vencedor Definido:** {vencedor.mention}!", ephemeral=False)

class ViewVencedor(discord.ui.View):
    def __init__(self, membros):
        super().__init__(timeout=60)
        self.add_item(VencedorSelect(membros))

class WoSelect(discord.ui.Select):
    def __init__(self, membros):
        options = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in membros]
        super().__init__(placeholder="Selecione o ganhador por W.O...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        ganhador_id = int(self.values[0])
        ganhador = interaction.guild.get_member(ganhador_id) or await interaction.guild.fetch_member(ganhador_id)
        await interaction.response.send_message(f"⚠️ **Vitória por W.O Definida:** {ganhador.mention} levou a melhor!", ephemeral=False)

class ViewWo(discord.ui.View):
    def __init__(self, membros):
        super().__init__(timeout=60)
        self.add_item(WoSelect(membros))

class PainelMediadorView(discord.ui.View):
    def __init__(self, membros_partida):
        super().__init__(timeout=None)
        self.membros_partida = membros_partida

    @discord.ui.button(label="Vencedor", style=discord.ButtonStyle.success, emoji="🏆")
    async def botao_vencedor(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.membros_partida:
            await interaction.response.send_message("❌ Nenhum membro elegível encontrado neste tópico.", ephemeral=True)
            return
        view = ViewVencedor(self.membros_partida)
        await interaction.response.send_message("👇 Escolha abaixo o jogador **Vencedor**:", view=view, ephemeral=True)

    @discord.ui.button(label="Ganhador por W.o", style=discord.ButtonStyle.primary, emoji="⚠️")
    async def botao_wo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.membros_partida:
            await interaction.response.send_message("❌ Nenhum membro elegível encontrado neste tópico.", ephemeral=True)
            return
        view = ViewWo(self.membros_partida)
        await interaction.response.send_message("👇 Escolha abaixo quem ganhou por **W.O**:", view=view, ephemeral=True)

    @discord.ui.button(label="Reinicia aposta", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def botao_reiniciar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔄 **A aposta foi reiniciada!**", ephemeral=False)

    @discord.ui.button(label="Finalizar aposta", style=discord.ButtonStyle.danger, emoji="🔒")
    async def botao_finalizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 **Aposta finalizada. Fechando o tópico em instantes...**", ephemeral=False)
        if isinstance(interaction.channel, discord.Thread):
            import asyncio
            await asyncio.sleep(2)
            try:
                await interaction.channel.edit(archived=True, locked=True)
            except Exception:
                pass

@bot.command(name="sala_criada")
async def sala_criada(ctx):
    try:
        await ctx.message.delete()
    except Exception:
        pass

    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("❌ Este comando só pode ser utilizado dentro do tópico da partida!", delete_after=5)
        return

    # Coleta apenas membros humanos que estão no tópico (excluindo bots)
    membros_partida = [m for m in ctx.channel.members if not m.bot]

    embed = discord.Embed(
        title="⚙️ Painel de Controle do Mediador",
        description="Utilize os botões abaixo para gerenciar a partida:",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Painel exclusivo para controle do Mediador.")

    view = PainelMediadorView(membros_partida)
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
         
