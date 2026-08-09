import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Armazena os dados da fila
fila_jogadores = []
fila_mediadores = []
TAMANHO_MAXIMO = 2 

# Dicionário para armazenar o Pix de cada mediador cadastrado
pix_mediadores = {}

# Dicionário para armazenar estatísticas dos jogadores (Vitórias, Derrotas, Streak, Coins)
estatisticas_jogadores = {}

# Dicionário para armazenar o valor da aposta de cada tópico/partida ativa (ex: {thread_id: 10.50})
valores_apostas_partidas = {}

# Controle para saber quais jogadores já disseram "pago" em cada tópico: {thread_id: set([user_id1, user_id2])}
pagamentos_pendentes = {}

# Taxa padrão global em centavos (ex: 10 centavos = 0.10)
taxa_global_centavos = 0.10

mensagem_painel_med = None

# Contador global para numeração sequencial dos tópicos de fila (Fila-1, Fila-2...)
contador_filas_criadas = 0

# ------------------------------------------------------------------
# CONFIGURAÇÕES DO BOT (COMANDO /config_bot)
# ------------------------------------------------------------------
config_bot_dados = {
    "dono_id": "1461858587080130663",
    "cargo_comandos": None,
    "cargo_criar_fila": None,
    "cargo_criar_pix": None,
    "cargo_config": None,
    "cargo_entrar_med": None,
    "cargo_cadastrar_pix": None,
    "cargo_comando_p": None
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
    cargo_entrar_med = discord.ui.TextInput(
        label="Cargos p/ entrar na fila de mediador",
        placeholder="Nome ou ID do cargo...",
        style=discord.TextStyle.short,
        required=False
    )
    cargo_cadastrar_pix = discord.ui.TextInput(
        label="Cargos p/ cadastrar o Pix",
        placeholder="Nome ou ID do cargo...",
        style=discord.TextStyle.short,
        required=False
    )
    cargo_comando_p = discord.ui.TextInput(
        label="Cargos p/ acionar o comando .p",
        placeholder="Nome ou ID do cargo...",
        style=discord.TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        if self.cargo_entrar_med.value:
            config_bot_dados["cargo_entrar_med"] = self.cargo_entrar_med.value.strip()
        if self.cargo_cadastrar_pix.value:
            config_bot_dados["cargo_cadastrar_pix"] = self.cargo_cadastrar_pix.value.strip()
        if self.cargo_comando_p.value:
            config_bot_dados["cargo_comando_p"] = self.cargo_comando_p.value.strip()

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

    @discord.ui.button(label="Resetar total de filas", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def resetar_filas(self, interaction: discord.Interaction, button: discord.ui.Button):
        global contador_filas_criadas
        contador_filas_criadas = 0
        await interaction.response.send_message("🗑️ **O contador total de filas foi resetado para 0 com sucesso!**", ephemeral=True)

    @discord.ui.button(label="Gerar filas", style=discord.ButtonStyle.success, emoji="📁")
    async def gerar_filas_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalCriarFilas())

@bot.tree.command(name="config_bot", description="Painel de configurações gerais e permissões do bot")
async def slash_config_bot(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚙️ Painel de Configurações do Bot",
        description="Gerencie abaixo quem tem permissão para executar ações, administrar o servidor e gerenciar filas.",
        color=discord.Color.blurple()
    )
    embed.add_field(name="👤 Dono do Bot (ID)", value=config_bot_dados["dono_id"] or "Não definido", inline=False)
    embed.add_field(name="⌨️ Cargo p/ Comandos", value=config_bot_dados["cargo_comandos"] or "Não definido", inline=True)
    embed.add_field(name="➔ Cargo p/ Criar Fila", value=config_bot_dados["cargo_criar_fila"] or "Não definido", inline=True)
    embed.add_field(name="💳 Cargo p/ Painel Pix", value=config_bot_dados["cargo_criar_pix"] or "Não definido", inline=True)
    embed.add_field(name="🔧 Cargo p/ Mexer Config", value=config_bot_dados["cargo_config"] or "Não definido", inline=True)
    embed.add_field(name="🛡️ Cargo p/ Entrar Fila Med", value=config_bot_dados["cargo_entrar_med"] or "Não definido", inline=True)
    embed.add_field(name="💰 Cargo p/ Cadastrar Pix", value=config_bot_dados["cargo_cadastrar_pix"] or "Não definido", inline=True)
    embed.add_field(name="📊 Cargo p/ Comando .p", value=config_bot_dados["cargo_comando_p"] or "Não definido", inline=True)
    embed.add_field(name="📁 Filas Criadas Atualmente", value=str(contador_filas_criadas), inline=False)

    view = ConfigBotView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ------------------------------------------------------------------
# COMANDO SLASH: /configura_taxar
# ------------------------------------------------------------------
class ModalConfiguraTaxa(discord.ui.Modal, title="Configurar Taxa"):
    valor_taxa = discord.ui.TextInput(
        label="Valor da taxa (em centavos ou reais)",
        placeholder="Ex: 10 (para 10 centavos) ou 0,10",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        dono_id = config_bot_dados.get("dono_id", "1461858587080130663")
        if str(interaction.user.id) != str(dono_id):
            await interaction.response.send_message("❌ Apenas o dono do bot pode alterar a taxa!", ephemeral=True)
            return

        global taxa_global_centavos
        texto = self.valor_taxa.value.strip().replace(",", ".")
        try:
            num = float(texto)
            if num >= 1.0:
                taxa_global_centavos = num / 100.0
            else:
                taxa_global_centavos = num
                
            taxa_centavos_exibicao = int(round(taxa_global_centavos * 100))
            await interaction.response.send_message(
                f"✅ **Taxa atualizada com sucesso!**\n"
                f"A taxa configurada agora é de **{taxa_centavos_exibicao} centavos** (R$ {taxa_global_centavos:.2f}).",
                ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message("❌ Valor inválido! Digite apenas números (ex: 10 ou 0,10).", ephemeral=True)

@bot.tree.command(name="configura_taxar", description="Configura o valor da taxa aplicada aos reembolsos/apostas")
async def slash_configura_taxar(interaction: discord.Interaction):
    dono_id = config_bot_dados.get("dono_id", "1461858587080130663")
    if str(interaction.user.id) != str(dono_id):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando!", ephemeral=True)
        return
    await interaction.response.send_modal(ModalConfiguraTaxa())

EMOJI_CONTROLE = "<:emoji_1:1535450507160846506>"
EMOJI_DINHEIRO = "<:emoji_2:1535453860947034193>"
EMOJI_BONECO   = "<:emoji_3:1535462271906746408>"
EMOJI_GELO     = "<:emoji_4:1535465191481810954>"

# ------------------------------------------------------------------
# COMANDO DE PREFIXO: .p (ESTATÍSTICAS)
# ------------------------------------------------------------------
@bot.command(name="p")
async def comando_p(ctx, membro: discord.Member = None):
    cargo_comandos = config_bot_dados.get("cargo_comandos")
    if cargo_comandos and not any(str(c.id) == cargo_comandos or c.name.lower() == cargo_comandos.lower() for c in ctx.author.roles):
        if str(ctx.author.id) != config_bot_dados.get("dono_id"):
            await ctx.send("❌ Você não possui o cargo necessário para executar comandos do bot!", delete_after=5)
            return

    cargo_req = config_bot_dados.get("cargo_comando_p")
    if cargo_req and not any(str(c.id) == cargo_req or c.name.lower() == cargo_req.lower() for c in ctx.author.roles):
        if str(ctx.author.id) != config_bot_dados.get("dono_id"):
            await ctx.send(f"❌ Você não possui o cargo necessário (**{cargo_req}**) para usar o comando `.p`!", delete_after=5)
            return

    alvo = membro if membro else ctx.author
    stats = estatisticas_jogadores.get(alvo.id, {"vitorias": 0, "derrotas": 0, "streak": 0, "streak_atual": 0, "coins": 0})

    embed = discord.Embed(
        title=f"📊 Estatísticas de {alvo.display_name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="📈 Vitórias Consecutivas (Recorde)", value=str(stats["streak"]), inline=True)
    embed.add_field(name="🏆 Vitórias", value=str(stats["vitorias"]), inline=True)
    embed.add_field(name="❌ Perdas", value=str(stats["derrotas"]) if "derrotas" in stats else "0", inline=True)
    embed.add_field(name="------", value="\u200b", inline=False)
    embed.add_field(name="🪙 Coins", value=f"{stats['vitorias']} vitórias | {stats['coins']} Coins", inline=False)
    embed.set_thumbnail(url=alvo.display_avatar.url)

    await ctx.send(embed=embed)

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
        cargo_req = config_bot_dados.get("cargo_cadastrar_pix")
        if cargo_req and not any(str(c.id) == cargo_req or c.name.lower() == cargo_req.lower() for c in interaction.user.roles):
            await interaction.response.send_message(f"❌ Você não possui o cargo necessário (**{cargo_req}**) para cadastrar o Pix!", ephemeral=True)
            return

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
# PAINEL DA FILA DE MEDIADORES (/med)
# ------------------------------------------------------------------
def criar_embed_mediadores():
    embed = discord.Embed(
        title="🛡️ Fila de Mediadores",
        description="Você taxa que entrar na fila para começar a mediar, caso contrário nenhuma partida será iniciada!",
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
        cargo_req = config_bot_dados.get("cargo_entrar_med")
        if cargo_req and not any(str(c.id) == cargo_req or c.name.lower() == cargo_req.lower() for c in interaction.user.roles):
            await interaction.response.send_message(f"❌ Você não possui o cargo necessário (**{cargo_req}**) para entrar na fila de mediadores!", ephemeral=True)
            return

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
def criar_embed_fila(nome_fila="Fila de Aposta", modo_jogo="1v1 Mobile", valor_aposta="R$ 0,50"):
    embed = discord.Embed(
        title=f"➔ [{nome_fila}] {modo_jogo}",
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

class ConfirmarRecebimentoView(discord.ui.View):
    def __init__(self, mediador, jogadores):
        super().__init__(timeout=None)
        self.mediador = mediador
        self.jogadores = jogadores

    @discord.ui.button(label="Não recebi", style=discord.ButtonStyle.danger, emoji="❌")
    async def nao_recebi(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.mediador.id and str(interaction.user.id) != config_bot_dados.get("dono_id"):
            await interaction.response.send_message("❌ Apenas o mediador pode usar este botão!", ephemeral=True)
            return
        await interaction.response.send_message(f"❌ **{self.mediador.mention} informou que NÃO recebeu o pagamento!** Verifiquem o envio.", ephemeral=False)

    @discord.ui.button(label="Confirma recebimento", style=discord.ButtonStyle.success, emoji="✅")
    async def confirma_recebimento(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.mediador.id and str(interaction.user.id) != config_bot_dados.get("dono_id"):
            await interaction.response.send_message("❌ Apenas o mediador pode usar este botão!", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ **{self.mediador.mention} confirmou o recebimento dos pagamentos!** Boa sorte na partida!", ephemeral=False)

class ConfirmarPartidaView(discord.ui.View):
    def __init__(self, jogadores, mediador, valor_com_taxa_str, valor_base_str):
        super().__init__(timeout=None)
        self.jogadores = jogadores
        self.mediador = mediador
        self.valor_com_taxa_str = valor_com_taxa_str
        self.valor_base_str = valor_base_str
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
                color=discord.Color.from_rgb(40, 160, 90)
            )
            embed_pix.title = "✅ Partida Confirmada"
            embed_pix.add_field(name="⚔️ Estilo de Jogo", value="1x1", inline=False)
            embed_pix.add_field(name="Informações da Aposta", value=f"Valor da Sala: {self.valor_base_str}\nMediador: {self.mediador.mention}", inline=False)
            embed_pix.add_field(name="💰 Valor da Aposta", value=self.valor_com_taxa_str, inline=False)
            embed_pix.add_field(name="👤 Jogadores", value=f"{self.jogadores[0].mention}\n{self.jogadores[1].mention}", inline=False)

            if not dados_pix:
                embed_pix.description = f"⚠️ {self.mediador.mention}, você ainda não cadastrou o seu Pix! Use o comando `/pix`."
                if isinstance(interaction.channel, discord.Thread):
                    await interaction.channel.send(content=f"🔔 {self.jogadores[0].mention} {self.jogadores[1].mention}", embed=embed_pix)
                else:
                    await interaction.followup.send(content=f"🔔 {self.jogadores[0].mention} {self.jogadores[1].mention}", embed=embed_pix)
            else:
                qr_link = dados_pix.get("qr")
                if qr_link and qr_link.startswith("http"):
                    embed_pix.set_image(url=qr_link)

                if isinstance(interaction.channel, discord.Thread):
                    msg_pix = await interaction.channel.send(content=f"🔔 {self.jogadores[0].mention} {self.jogadores[1].mention}", embed=embed_pix)
                else:
                    msg_pix = await interaction.followup.send(content=f"🔔 {self.jogadores[0].mention} {self.jogadores[1].mention}", embed=embed_pix)

                # Enviar chave Copia e Cola logo abaixo do Embed do Pix
                if isinstance(interaction.channel, discord.Thread):
                    await interaction.channel.send(f"🔑 **Pix Copia e Cola / Chave:**\n```\n{dados_pix['chave']}\n```\n*Envie o comprovante e digite **'pago'** aqui no chat assim que realizar o pagamento!*")

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
    def __init__(self, nome_fila="Fila de Aposta", modo_jogo="1v1", valor_str="R$ 0,50", valor_num=0.50):
        super().__init__(timeout=None)
        self.nome_fila = nome_fila
        self.modo_jogo = modo_jogo
        self.valor_str = valor_str
        self.valor_num = valor_num

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
            embed_atualizado = criar_embed_fila(nome_fila=self.nome_fila, modo_jogo=self.modo_jogo, valor_aposta=self.valor_str)
            await interaction.response.edit_message(embed=embed_atualizado, view=self)
            await interaction.followup.send(f"🚪 {user.mention} saiu da fila.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Você não está na fila!", ephemeral=True)

    async def entrar_na_fila(self, interaction: discord.Interaction, modo_gelo: str):
        global contador_filas_criadas
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

            await interaction.response.edit_message(embed=criar_embed_fila(nome_fila=self.nome_fila, modo_jogo=self.modo_jogo, valor_aposta=self.valor_str), view=self)
            await interaction.followup.send(f"✅ Fila lotada! Criando partida com o mediador {mediador.name}...", ephemeral=True)

            channel = interaction.channel
            j1, j2 = jogadores_partida[0], jogadores_partida[1]

            contador_filas_criadas += 1
            nome_topico_fila = f"Fila-{contador_filas_criadas}"

            try:
                topico = await channel.create_thread(
                    name=nome_topico_fila,
                    type=discord.ChannelType.public_thread,
                    auto_archive_duration=60
                )
            except Exception:
                topico = await channel.create_thread(
                    name=nome_topico_fila,
                    auto_archive_duration=60
                )

            valores_apostas_partidas[topico.id] = self.valor_num

            await topico.add_user(j1)
            await topico.add_user(j2)
            await topico.add_user(mediador)

            valor_com_taxa_num = self.valor_num + taxa_global_centavos
            valor_com_taxa_str = f"R$ {valor_com_taxa_num:.2f}".replace(".", ",")
            valor_base_str = f"R$ {self.valor_num:.2f}".replace(".", ",")

            embed_partida = discord.Embed(
                color=discord.Color.from_rgb(40, 160, 90)
            )
            embed_partida.title = "✅ Partida Confirmada"
            embed_partida.add_field(name="⚔️ Estilo de Jogo", value=f"{modo_gelo} ({self.modo_jogo})", inline=False)
            embed_partida.add_field(name="Informações da Aposta", value=f"Valor da Sala: {valor_base_str}\nMediador: {mediador.mention}", inline=False)
            embed_partida.add_field(name="💰 Valor da Aposta", value=valor_com_taxa_str, inline=False)
            embed_partida.add_field(name="👤 Jogadores", value=f"{j1.mention}\n{j2.mention}", inline=False)

            view_confirmacao = ConfirmarPartidaView(jogadores_partida, mediador, valor_com_taxa_str, valor_base_str)

            await topico.send(
                content=f"🔔 {j1.mention} {j2.mention} | Mediador: {mediador.mention}",
                embed=embed_partida,
                view=view_confirmacao
            )
        else:
            embed_atualizado = criar_embed_fila(nome_fila=self.nome_fila, modo_jogo=self.modo_jogo, valor_aposta=self.valor_str)
            await interaction.response.edit_message(embed=embed_atualizado, view=self)
            await interaction.followup.send(f"✅ {user.mention} entrou na fila ({modo_gelo})!", ephemeral=True)

# ------------------------------------------------------------------
# GERENCIAMENTO DE CRIAÇÃO DE 15 FILAS EM 1 SÓ CANAL
# ------------------------------------------------------------------
class CanalUnicoSelect(discord.ui.ChannelSelect):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        super().__init__(
            placeholder="Selecione o canal onde serão criadas as 15 filas...",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text]
        )

    async def callback(self, interaction: discord.Interaction):
        canal_selecionado = interaction.guild.get_channel(self.values[0].id)
        
        if not canal_selecionado:
            await interaction.response.send_message("❌ Não foi possível encontrar o canal selecionado no servidor.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"⚙️ Gerando **15 filas** no modo **{self.parent_view.modo}** com o nome **{self.parent_view.nome_fila}** no canal {canal_selecionado.mention}...", 
            ephemeral=True
        )

        try:
            await interaction.message.delete()
        except Exception:
            pass

        valor_atual_idx = 0
        try:
            for _ in range(15):
                val_str = self.parent_view.valores_originais[valor_atual_idx % len(self.parent_view.valores_originais)]
                val_num = self.parent_view.valores_nums[valor_atual_idx % len(self.parent_view.valores_nums)]
                
                embed = criar_embed_fila(nome_fila=self.parent_view.nome_fila, modo_jogo=self.parent_view.modo, valor_aposta=f"R$ {val_str}")
                view = FilaView(nome_fila=self.parent_view.nome_fila, modo_jogo=self.parent_view.modo, valor_str=f"R$ {val_str}", valor_num=val_num)
                
                await canal_selecionado.send(embed=embed, view=view)
                valor_atual_idx += 1

            await interaction.followup.send(f"✅ As **15 filas** foram criadas com sucesso no canal {canal_selecionado.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ocorreu um erro ao enviar as filas: {e}", ephemeral=True)

class ViewSelecaoCanalUnico(discord.ui.View):
    def __init__(self, nome_fila, valores_originais, valores_nums, modo):
        super().__init__(timeout=60)
        self.nome_fila = nome_fila
        self.valores_originais = valores_originais
        self.valores_nums = valores_nums
        self.modo = modo
        self.add_item(CanalUnicoSelect(self))

class SelectModoFila(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label="4v4", value="4v4"),
            discord.SelectOption(label="3v3", value="3v3"),
            discord.SelectOption(label="2v2", value="2v2"),
            discord.SelectOption(label="1v1", value="1v1"),
        ]
        super().__init__(placeholder="Escolha o modo de jogo (1v1, 2v2, 3v3 ou 4v4)", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        modo = self.values[0]
        view_canal = ViewSelecaoCanalUnico(self.parent_view.nome_fila, self.parent_view.valores_originais, self.parent_view.valores_nums, modo)
        await interaction.response.edit_message(content=f"📁 Modo selecionado: **{modo}**.\nAgora **selecione o canal único abaixo** para gerar as 15 filas:", view=view_canal)

class ViewSelecaoModoFila(discord.ui.View):
    def __init__(self, nome_fila, valores_originais, valores_nums):
        super().__init__(timeout=60)
        self.nome_fila = nome_fila
        self.valores_originais = valores_originais
        self.valores_nums = valores_nums
        self.add_item(SelectModoFila(self))

class ModalCriarFilas(discord.ui.Modal, title="Configurar Filas"):
    nome_fila_input = discord.ui.TextInput(
        label="Nome da Fila",
        placeholder="Ex: Fila Principal, X1 dos Crias...",
        style=discord.TextStyle.short,
        required=True
    )
    valores_input = discord.ui.TextInput(
        label="Valores (use vírgula, ex: 0,50, 1,00, 2,00)",
        placeholder="Ex: 0,50, 1,00, 2,00",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            nome_fila = self.nome_fila_input.value.strip()
            input_cru = self.valores_input.value.strip()
            
            valores_originais = []
            valores_nums = []
            for v in input_cru.split(","):
                v_clean = v.strip()
                if v_clean:
                    valores_originais.append(v_clean)
                    try:
                        v_num = float(v_clean.replace(",", "."))
                        valores_nums.append(v_num)
                    except ValueError:
                        valores_nums.append(0.50)

            if not valores_originais:
                valores_originais = ["0,50"]
                valores_nums = [0.50]

            view_modo = ViewSelecaoModoFila(nome_fila, valores_originais, valores_nums)
            if interaction.response.is_done():
                await interaction.followup.send("🎮 Escolha abaixo o modo de jogo:", view=view_modo, ephemeral=True)
            else:
                await interaction.response.send_message("🎮 Escolha abaixo o modo de jogo:", view=view_modo, ephemeral=True)
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Ocorreu um erro ao processar os dados: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Ocorreu um erro ao processar os dados: {e}", ephemeral=True)

@bot.tree.command(name="criar_15_filas", description="Gera 15 filas em um único canal escolhido")
async def slash_criar_15_filas(interaction: discord.Interaction):
    await interaction.response.send_modal(ModalCriarFilas())

# ------------------------------------------------------------------
# PAINEL DE CONTROLE DA SALA DO MEDIADOR (!sala_criada)
# ------------------------------------------------------------------
class VencedorSelect(discord.ui.Select):
    def __init__(self, membros):
        options = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in membros]
        super().__init__(placeholder="Selecione o jogador vencedor...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        vencedor_id = int(self.values[0])
        vencedor = interaction.guild.get_member(vencedor_id) or await interaction.guild.fetch_member(vencedor_id)
        
        if vencedor.id not in estatisticas_jogadores:
            estatisticas_jogadores[vencedor.id] = {"vitorias": 0, "derrotas": 0, "streak": 0, "streak_atual": 0, "coins": 0}
        
        estatisticas_jogadores[vencedor.id]["vitorias"] += 1
        estatisticas_jogadores[vencedor.id]["coins"] += 1
        estatisticas_jogadores[vencedor.id]["streak_atual"] += 1
        
        if estatisticas_jogadores[vencedor.id]["streak_atual"] > estatisticas_jogadores[vencedor.id]["streak"]:
            estatisticas_jogadores[vencedor.id]["streak"] = estatisticas_jogadores[vencedor.id]["streak_atual"]

        if isinstance(interaction.channel, discord.Thread):
            for m in interaction.channel.members:
                if not m.bot and m.id != vencedor.id:
                    if m.id not in estatisticas_jogadores:
                        estatisticas_jogadores[m.id] = {"vitorias": 0, "derrotas": 0, "streak": 0, "streak_atual": 0, "coins": 0}
                    estatisticas_jogadores[m.id]["derrotas"] += 1
                    estatisticas_jogadores[m.id]["streak_atual"] = 0

        await interaction.response.send_message(
            f"🏆 **Vencedor Definido:** {vencedor.mention}\n"
            f"📈 **Vitórias Consecutivas:** {estatisticas_jogadores[vencedor.id]['streak_atual']}\n"
            f"🏆 **Vitórias Totais:** {estatisticas_jogadores[vencedor.id]['vitorias']}\n"
            f"🪙 **Coins:** +1", 
            ephemeral=False
        )

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
        
        if ganhador.id not in estatisticas_jogadores:
            estatisticas_jogadores[ganhador.id] = {"vitorias": 0, "derrotas": 0, "streak": 0, "streak_atual": 0, "coins": 0}
        
        estatisticas_jogadores[ganhador.id]["vitorias"] += 1
        estatisticas_jogadores[ganhador.id]["coins"] += 1
        estatisticas_jogadores[ganhador.id]["streak_atual"] += 1
        
        if estatisticas_jogadores[ganhador.id]["streak_atual"] > estatisticas_jogadores[ganhador.id]["streak"]:
            estatisticas_jogadores[ganhador.id]["streak"] = estatisticas_jogadores[ganhador.id]["streak_atual"]

        if isinstance(interaction.channel, discord.Thread):
            for m in interaction.channel.members:
                if not m.bot and m.id != ganhador.id:
                    if m.id not in estatisticas_jogadores:
                        estatisticas_jogadores[m.id] = {"vitorias": 0, "derrotas": 0, "streak": 0, "streak_atual": 0, "coins": 0}
                    estatisticas_jogadores[m.id]["derrotas"] += 1
                    estatisticas_jogadores[m.id]["streak_atual"] = 0

        await interaction.response.send_message(
            f"⚠️ **Vitória por W.O Definida:** {ganhador.mention}\n"
            f"📈 **Vitórias Consecutivas:** {estatisticas_jogadores[ganhador.id]['streak_atual']}\n"
            f"🏆 **Vitórias Totais:** {estatisticas_jogadores[ganhador.id]['vitorias']}\n"
            f"🪙 **Coins:** +1", 
            ephemeral=False
        )

class ViewWo(discord.ui.View):
    def __init__(self, membros):
        super().__init__(timeout=60)
        self.add_item(WoSelect(membros))

class PainelMediadorView(discord.ui.View):
    def __init__(self, membros_partida, thread_id):
        super().__init__(timeout=None)
        self.membros_partida = membros_partida
        self.thread_id = thread_id

    @discord.ui.button(label="Escolher vencedor", style=discord.ButtonStyle.success, emoji="🏆")
    async def botao_vencedor(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.membros_partida:
            await interaction.response.send_message("❌ Nenhum membro elegível encontrado neste tópico.", ephemeral=True)
            return
        view = ViewVencedor(self.membros_partida)
        await interaction.response.send_message("👇 Escolha abaixo o jogador **Vencedor**:", view=view, ephemeral=True)

    @discord.ui.button(label="Dar vitória por w.o", style=discord.ButtonStyle.primary, emoji="⚠️")
    async def botao_wo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.membros_partida:
            await interaction.response.send_message("❌ Nenhum membro elegível encontrado neste tópico.", ephemeral=True)
            return
        view = ViewWo(self.membros_partida)
        await interaction.response.send_message("👇 Escolha abaixo quem ganhou por **W.O**:", view=view, ephemeral=True)

    @discord.ui.button(label="Dar reembolso", style=discord.ButtonStyle.secondary, emoji="💸")
    async def botao_reembolso(self, interaction: discord.Interaction, button: discord.ui.Button):
        valor_base = valores_apostas_partidas.get(self.thread_id, 0.50)
        valor_reembolso = valor_base + taxa_global_centavos
        
        valor_str = f"R$ {valor_reembolso:.2f}".replace(".", ",")
        base_str = f"R$ {valor_base:.2f}".replace(".", ",")
        taxa_centavos_exibicao = int(round(taxa_global_centavos * 100))

        embed_reembolso = discord.Embed(
            title="💸 Reembolso Solicitado",
            description=(
                f"O valor base da aposta era de **{base_str}**.\n"
                f"Com a taxa atual de **{taxa_centavos_exibicao}c** (R$ {taxa_global_centavos:.2f}), o valor exato do reembolso é:\n\n"
                f"🔑 **Valor do Reembolso:** `{valor_str}`"
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed_reembolso, ephemeral=False)

    @discord.ui.button(label="Finalizar a partida", style=discord.ButtonStyle.danger, emoji="🔒")
    async def botao_finalizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 **A partida foi finalizada. Fechando o tópico em instantes...**", ephemeral=False)
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

    membros_partida = [m for m in ctx.channel.members if not m.bot]

    embed = discord.Embed(
        title="⚙️ Painel de Controle do Mediador",
        description="Utilize os botões abaixo para gerenciar a partida:",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Painel exclusivo para controle do Mediador.")

    view = PainelMediadorView(membros_partida, ctx.channel.id)
    await ctx.send(embed=embed, view=view)

# ------------------------------------------------------------------
# EVENTO ON_MESSAGE: DETECTAR QUANDO OS JOGADORES DIZEM "PAGO"
# ------------------------------------------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Processar comandos tradicionais primeiro (.p, etc)
    await bot.process_commands(message)

    # Verificar se a mensagem foi enviada dentro de um tópico (Thread)
    if isinstance(message.channel, discord.Thread):
        thread_id = message.channel.id
        
        # Verificar se a mensagem contém "pago" ou "paguei"
        conteudo = message.content.lower().strip()
        if "pago" in conteudo or "paguei" in conteudo:
            # Descobrir quem é o mediador e os jogadores verificando os membros do tópico
            membros_nao_bot = [m for m in message.channel.members if not m.bot]
            if len(membros_nao_bot) >= 3:
                # O mediador costuma ser o último adicionado ou vamos filtrar (assumindo que o criador/mediador está no tópico)
                # Vamos identificar os jogadores recolhendo do histórico inicial ou assumindo os 2 primeiros não-mediadores
                # Alternativa robusta: procurar nos membros do tópico quem não é o criador ou verificar por ID nas views criadas.
                # Aqui registramos o ID do usuário que disse "pago"
                if thread_id not in pagamentos_pendentes:
                    pagamentos_pendentes[thread_id] = set()
                
                pagamentos_pendentes[thread_id].add(message.author.id)

                # Precisamos encontrar o mediador do tópico (procurando nos membros que possuem cargo ou simplesmente pegando o último membro adicionado)
                # Como a ordem típica de adição foi: j1, j2, mediador -> o mediador é o último
                mediador = membros_nao_bot[-1]
                jogadores = membros_nao_bot[:2]

                # Verificar se os 2 jogadores já disseram pago
                jogadores_ids = {j.id for j in jogadores}
                if jogadores_ids.issubset(pagamentos_pendentes[thread_id]):
                    # Limpar para evitar spam contínuo
                    pagamentos_pendentes[thread_id].clear()

                    view_recebimento = ConfirmarRecebimentoView(mediador, jogadores)
                    await message.channel.send(
                        content=f"🔔 {mediador.mention}",
                        embed=discord.Embed(
                            title="💳 Confirmação de Pagamento",
                            description="Ambos os jogadores informaram que pagaram! **(Confirme o recebimento)** abaixo:",
                            color=discord.Color.gold()
                        ),
                        view=view_recebimento
                    )

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
