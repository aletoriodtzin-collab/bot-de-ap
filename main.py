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

# Dicionário para armazenar estatísticas dos jogadores
estatisticas_jogadores = {}

# Dicionário para armazenar o valor da aposta de cada tópico/partida ativa
valores_apostas_partidas = {}

# Dicionários de controle para o sistema de pagamento nos tópicos
pagamentos_pendentes = {}
mediadores_partidas = {}
jogadores_partidas = {}

# Taxa padrão global em centavos (ex: 10 centavos = 0.10)
taxa_global_centavos = 0.10

mensagem_painel_med = None

# Contador global para numeração sequencial dos tópicos de fila (Fila-1, Fila-2...)
contador_filas_criadas = 0

# ------------------------------------------------------------------
# CONFIGURAÇÕES DO BOT
# ------------------------------------------------------------------
config_bot_dados = {
    "dono_id": "1461858587080130663",
    "cargo_comandos": [],
    "cargo_criar_fila": [],
    "cargo_criar_pix": [],
    "cargo_config": [],
    "cargo_entrar_med": [],
    "cargo_cadastrar_pix": [],
    "cargo_comando_p": []
}

def verificar_permissao_global(user: discord.Member) -> bool:
    """Verifica se o usuário é o dono do bot, administrador ou possui algum dos cargos configurados."""
    if str(user.id) == str(config_bot_dados.get("dono_id")):
        return True
    if user.guild_permissions.administrator:
        return True
    
    cargos_permitidos = []
    for chave in ["cargo_comandos", "cargo_config", "cargo_entrar_med", "cargo_criar_fila", "cargo_criar_pix", "cargo_cadastrar_pix", "cargo_comando_p"]:
        val = config_bot_dados.get(chave)
        if isinstance(val, list):
            cargos_permitidos.extend(val)
        elif val:
            cargos_permitidos.append(val)
            
    cargos_permitidos.extend(["mediador", "mediadores", "med"])
    
    for r in user.roles:
        for c in cargos_permitidos:
            if c and (str(r.id) == str(c) or r.name.lower() == str(c).lower()):
                return True
    return False

class ConfigBotModal(discord.ui.Modal, title="Configurações do Bot"):
    dono_id = discord.ui.TextInput(
        label="Quem pode mexer no bot? (ID)",
        placeholder="Ex: 1461858587080130663",
        style=discord.TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Você não tem permissão para alterar estas configurações!", ephemeral=True)
            return

        if self.dono_id.value:
            config_bot_dados["dono_id"] = self.dono_id.value.strip()

        await interaction.response.send_message("✅ **Configurações do bot atualizadas com sucesso!**", ephemeral=True)

# ------------------------------------------------------------------
# SELECTS DE CARGOS MÚLTIPLOS
# ------------------------------------------------------------------
class MultiRoleSelectComandos(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder="Selecione os cargos p/ usar comandos...", min_values=0, max_values=10)

    async def callback(self, interaction: discord.Interaction):
        config_bot_dados["cargo_comandos"] = [str(r.id) for r in self.values]
        await interaction.response.send_message(f"✅ Cargos atualizados: {len(self.values)} cargo(s) selecionado(s).", ephemeral=True)

class MultiRoleSelectCriarFila(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder="Selecione os cargos p/ criar fila...", min_values=0, max_values=10)

    async def callback(self, interaction: discord.Interaction):
        config_bot_dados["cargo_criar_fila"] = [str(r.id) for r in self.values]
        await interaction.response.send_message(f"✅ Cargos atualizados: {len(self.values)} cargo(s) selecionado(s).", ephemeral=True)

class MultiRoleSelectCriarPix(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder="Selecione os cargos p/ criar painel Pix...", min_values=0, max_values=10)

    async def callback(self, interaction: discord.Interaction):
        config_bot_dados["cargo_criar_pix"] = [str(r.id) for r in self.values]
        await interaction.response.send_message(f"✅ Cargos atualizados: {len(self.values)} cargo(s) selecionado(s).", ephemeral=True)

class MultiRoleSelectConfig(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder="Selecione os cargos p/ mexer nas configs...", min_values=0, max_values=10)

    async def callback(self, interaction: discord.Interaction):
        config_bot_dados["cargo_config"] = [str(r.id) for r in self.values]
        await interaction.response.send_message(f"✅ Cargos atualizados: {len(self.values)} cargo(s) selecionado(s).", ephemeral=True)

class MultiRoleSelectEntrarMed(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder="Selecione os cargos p/ entrar na fila med...", min_values=0, max_values=10)

    async def callback(self, interaction: discord.Interaction):
        config_bot_dados["cargo_entrar_med"] = [str(r.id) for r in self.values]
        await interaction.response.send_message(f"✅ Cargos atualizados: {len(self.values)} cargo(s) selecionado(s).", ephemeral=True)

class MultiRoleSelectCadastrarPix(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder="Selecione os cargos p/ cadastrar o Pix...", min_values=0, max_values=10)

    async def callback(self, interaction: discord.Interaction):
        config_bot_dados["cargo_cadastrar_pix"] = [str(r.id) for r in self.values]
        await interaction.response.send_message(f"✅ Cargos atualizados: {len(self.values)} cargo(s) selecionado(s).", ephemeral=True)

class MultiRoleSelectComandoP(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder="Selecione os cargos p/ acionar o comando .p...", min_values=0, max_values=10)

    async def callback(self, interaction: discord.Interaction):
        config_bot_dados["cargo_comando_p"] = [str(r.id) for r in self.values]
        await interaction.response.send_message(f"✅ Cargos atualizados: {len(self.values)} cargo(s) selecionado(s).", ephemeral=True)

class ConfigBotViewPart1(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(MultiRoleSelectComandos())
        self.add_item(MultiRoleSelectCriarFila())
        self.add_item(MultiRoleSelectCriarPix())
        self.add_item(MultiRoleSelectConfig())

class ConfigBotViewPart2(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(MultiRoleSelectEntrarMed())
        self.add_item(MultiRoleSelectCadastrarPix())
        self.add_item(MultiRoleSelectComandoP())

class ConfigBotView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Definir Dono (ID)", style=discord.ButtonStyle.primary, emoji="⚙️")
    async def abrir_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas o dono ou mediadores podem usar este botão!", ephemeral=True)
            return
        await interaction.response.send_modal(ConfigBotModal())

    @discord.ui.button(label="Cargos Parte 1", style=discord.ButtonStyle.secondary, emoji="🛡️")
    async def cargos_parte_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas o dono ou mediadores podem usar este botão!", ephemeral=True)
            return
        await interaction.response.send_message("📌 **Selecione abaixo os cargos para cada permissão (Parte 1):**", view=ConfigBotViewPart1(), ephemeral=True)

    @discord.ui.button(label="Cargos Parte 2", style=discord.ButtonStyle.secondary, emoji="🛡️")
    async def cargos_parte_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas o dono ou mediadores podem usar este botão!", ephemeral=True)
            return
        await interaction.response.send_message("📌 **Selecione abaixo os cargos para cada permissão (Parte 2):**", view=ConfigBotViewPart2(), ephemeral=True)

    @discord.ui.button(label="Resetar total de filas", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def resetar_filas(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas o dono ou mediadores podem resetar as filas!", ephemeral=True)
            return
        global contador_filas_criadas
        contador_filas_criadas = 0
        await interaction.response.send_message("🗑️ **O contador total de filas foi resetado para 0 com sucesso!**", ephemeral=True)

    @discord.ui.button(label="Gerar filas", style=discord.ButtonStyle.success, emoji="📁")
    async def gerar_filas_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas o dono ou mediadores podem gerar filas!", ephemeral=True)
            return
        await interaction.response.send_modal(ModalCriarFilasDummy())

@bot.tree.command(name="config_bot", description="Painel de configurações gerais e permissões do bot")
async def slash_config_bot(interaction: discord.Interaction):
    if not verificar_permissao_global(interaction.user):
        await interaction.response.send_message("❌ Você não tem permissão para acessar este painel de configuração!", ephemeral=True)
        return

    def formatar_cargos(guild, lista_ids):
        if not lista_ids:
            return "Não definido"
        nomes = []
        for cid in lista_ids:
            cargo = guild.get_role(int(cid)) if cid.isdigit() else None
            if cargo:
                nomes.append(cargo.mention)
            else:
                nomes.append(f"ID: {cid}")
        return ", ".join(nomes)

    guild = interaction.guild
    embed = discord.Embed(
        title="⚙️ Painel de Configurações do Bot",
        description="Gerencie abaixo quem tem permissão para executar ações, administrar o servidor e gerenciar filas.",
        color=discord.Color.blurple()
    )
    embed.add_field(name="👤 Dono do Bot (ID)", value=config_bot_dados["dono_id"] or "Não definido", inline=False)
    embed.add_field(name="⌨️ Cargo p/ Comandos", value=formatar_cargos(guild, config_bot_dados["cargo_comandos"]), inline=True)
    embed.add_field(name="➔ Cargo p/ Criar Fila", value=formatar_cargos(guild, config_bot_dados["cargo_criar_fila"]), inline=True)
    embed.add_field(name="💳 Cargo p/ Painel Pix", value=formatar_cargos(guild, config_bot_dados["cargo_criar_pix"]), inline=True)
    embed.add_field(name="🔧 Cargo p/ Mexer Config", value=formatar_cargos(guild, config_bot_dados["cargo_config"]), inline=True)
    embed.add_field(name="🛡️ Cargo p/ Entrar Fila Med", value=formatar_cargos(guild, config_bot_dados["cargo_entrar_med"]), inline=True)
    embed.add_field(name="💰 Cargo p/ Cadastrar Pix", value=formatar_cargos(guild, config_bot_dados["cargo_cadastrar_pix"]), inline=True)
    embed.add_field(name="📊 Cargo p/ Comando .p", value=formatar_cargos(guild, config_bot_dados["cargo_comando_p"]), inline=True)
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
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas o dono ou mediadores podem alterar a taxa!", ephemeral=True)
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
    if not verificar_permissao_global(interaction.user):
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
    if not verificar_permissao_global(ctx.author):
        await ctx.send("❌ Você não possui permissão para usar o comando `.p`!", delete_after=5)
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
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas mediadores podem cadastrar o Pix!", ephemeral=True)
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
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas mediadores podem cadastrar o Pix!", ephemeral=True)
            return
        await interaction.response.send_modal(FormularioPixModal())

@bot.tree.command(name="pix", description="Cadastre o seu Pix para receber os pagamentos das partidas")
async def slash_pix(interaction: discord.Interaction):
    if not verificar_permissao_global(interaction.user):
        await interaction.response.send_message("❌ Apenas mediadores podem usar este comando!", ephemeral=True)
        return

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
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas mediadores podem entrar na fila de mediação!", ephemeral=True)
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
    if not verificar_permissao_global(interaction.user):
        await interaction.response.send_message("❌ Apenas mediadores podem usar este comando!", ephemeral=True)
        return

    global mensagem_painel_med
    await interaction.response.send_message(embed=criar_embed_mediadores(), view=MedView(), ephemeral=False)
    mensagem_painel_med = await interaction.original_response()

# ------------------------------------------------------------------
# ESTRUTURA DA FILA DE PARTIDA
# ------------------------------------------------------------------
def criar_embed_fila(nome_fila="Fila de Aposta", modo_jogo="1v1 Mobile", valor_aposta="R$ 0,50"):
    embed = discord.Embed(
        title=f"➔ {modo_jogo} — {nome_fila}",
        color=discord.Color.green()
    )
    embed.add_field(name=f"{EMOJI_CONTROLE} Modo", value=modo_jogo, inline=False)
    embed.add_field(name=f"{EMOJI_DINHEIRO} Valor", value=valor_aposta, inline=False)

    if not fila_jogadores:
        texto_jogadores = "*Aguardando jogador...*"
    else:
        # Exibe seguindo estritamente o formato solicitado: • @user | escolha (quem chegou primeiro fica acima do segundo)
        linhas = [f"• {j.mention} | {gelo}" for j, gelo in fila_jogadores]
        texto_jogadores = "\n".join(linhas)

    embed.add_field(name=f"{EMOJI_BONECO} Jogadores", value=texto_jogadores, inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
    return embed

class ConfirmarRecebimentoView(discord.ui.View):
    def __init__(self, mediador):
        super().__init__(timeout=None)
        self.mediador = mediador

    @discord.ui.button(label="Não recebi", style=discord.ButtonStyle.danger, emoji="❌")
    async def nao_recebi(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.mediador.id and not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas o mediador pode usar este botão!", ephemeral=True)
            return
        await interaction.response.send_message(f"❌ **{self.mediador.mention} informou que NÃO recebeu o pagamento!** Verifiquem o envio.", ephemeral=False)

    @discord.ui.button(label="Confirma recebimento", style=discord.ButtonStyle.success, emoji="✅")
    async def confirma_recebimento(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.mediador.id and not verificar_permissao_global(interaction.user):
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
                    await interaction.channel.send(content=f"🔔 {self.jogadores[0].mention} {self.jogadores[1].mention}", embed=embed_pix)
                else:
                    await interaction.followup.send(content=f"🔔 {self.jogadores[0].mention} {self.jogadores[1].mention}", embed=embed_pix)

                if isinstance(interaction.channel, discord.Thread):
                    await interaction.channel.send(f"🔑 **Pix Copia e Cola / Chave:**\n```\n{dados_pix['chave']}\n```\n*Envie o comprovante e digite **'pago'** aqui no chat assim que realizar o pagamento!*")

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, emoji="✖️")
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user not in self.jogadores and not verificar_permissao_global(user):
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
    def __init__(self, nome_fila="Fila de Aposta", modo_jogo="1v1", valor_str="0,50", valor_num=0.50):
        super().__init__(timeout=None)
        self.nome_fila = nome_fila
        self.modo_jogo = modo_jogo
        self.valor_str = valor_str
        self.valor_num = valor_num

        if self.modo_jogo in ["2v2", "3v3", "4v4"]:
            self.gelo_infinito.emoji = EMOJI_CONTROLE
            self.gelo_infinito.label = "Arma Infinita"
        else:
            self.gelo_infinito.emoji = EMOJI_GELO
            self.gelo_infinito.label = "Gelo Infinito"

    @discord.ui.button(label="Gelo Normal", style=discord.ButtonStyle.success, emoji=EMOJI_GELO)
    async def gelo_normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        modo_texto = "gelo normal"
        await self.entrar_na_fila(interaction, modo_texto)

    @discord.ui.button(label="Gelo Infinito", style=discord.ButtonStyle.success, emoji=EMOJI_GELO)
    async def gelo_infinito(self, interaction: discord.Interaction, button: discord.ui.Button):
        modo_texto = "arma infinita" if self.modo_jogo in ["2v2", "3v3", "4v4"] else "gelo infinito"
        await self.entrar_na_fila(interaction, modo_texto)

    @discord.ui.button(label="Sair Fila", style=discord.ButtonStyle.danger, emoji="❌")
    async def sair_fila(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        encontrado = None
        for item in fila_jogadores:
            if item[0].id == user.id:
                encontrado = item
                break

        if encontrado:
            fila_jogadores.remove(encontrado)
            embed_atualizado = criar_embed_fila(nome_fila=self.nome_fila, modo_jogo=self.modo_jogo, valor_aposta=f"R$ {self.valor_str}")
            await interaction.response.edit_message(embed=embed_atualizado, view=self)
            await interaction.followup.send(f"🚪 {user.mention} saiu da fila.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Você não está na fila!", ephemeral=True)

    async def entrar_na_fila(self, interaction: discord.Interaction, modo_gelo: str):
        global contador_filas_criadas
        user = interaction.user

        # Remove se o usuário já estiver na fila para atualizar ou tratar
        for item in fila_jogadores:
            if item[0].id == user.id:
                await interaction.response.send_message("⚠️ Você já está na fila!", ephemeral=True)
                return

        if len(fila_jogadores) >= TAMANHO_MAXIMO:
            await interaction.response.send_message("❌ A fila já está cheia!", ephemeral=True)
            return

        # Adiciona o jogador respeitando a ordem de chegada (quem chegou primeiro fica acima do segundo)
        fila_jogadores.append((user, modo_gelo))

        # Se atingiu o limite máximo (2 jogadores), verificamos as escolhas
        if len(fila_jogadores) == TAMANHO_MAXIMO:
            j1_obj, mode1 = fila_jogadores[0]
            j2_obj, mode2 = fila_jogadores[1]

            # Se os modos escolhidos forem DIFERENTES, não cria o tópico, atualiza a embed e avisa
            if mode1 != mode2:
                embed_atualizado = criar_embed_fila(nome_fila=self.nome_fila, modo_jogo=self.modo_jogo, valor_aposta=f"R$ {self.valor_str}")
                await interaction.response.edit_message(embed=embed_atualizado, view=self)
                await interaction.followup.send(
                    f"❌ **Escolhas diferentes!** O tópico não será criado pois {j1_obj.mention} e {j2_obj.mention} escolheram modos diferentes.", 
                    ephemeral=True
                )
                return

            # Se chegou aqui, as escolhas são IDÊNTICAS! Prosseguimos com a criação do tópico.
            if not fila_mediadores:
                await interaction.response.send_message("❌ Não há mediadores na fila! Aguarde um mediador entrar.", ephemeral=True)
                fila_jogadores.pop() # Remove o último que entrou para liberar a vaga
                return

            mediador = fila_mediadores.pop(0)
            fila_mediadores.append(mediador)
            await atualizar_painel_mediadores()

            jogadores_partida = [j1_obj, j2_obj]
            fila_jogadores.clear()

            await interaction.response.edit_message(embed=criar_embed_fila(nome_fila=self.nome_fila, modo_jogo=self.modo_jogo, valor_aposta=f"R$ {self.valor_str}"), view=self)
            await interaction.followup.send(f"✅ Fila lotada com o mesmo modo! Criando partida com o mediador {mediador.mention}...", ephemeral=True)

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
            mediadores_partidas[topico.id] = mediador
            jogadores_partidas[topico.id] = [j1.id, j2.id]

            await topico.add_user(j1)
            await topico.add_user(j2)
            await topico.add_user(mediador)

            valor_com_taxa_num = self.valor_num + taxa_global_centavos
            valor_com_taxa_str = f"R$ {valor_com_taxa_num:.2f}".replace(".", ",")
            valor_base_str = f"R$ {self.valor_str}"

            embed_partida = discord.Embed(
                color=discord.Color.from_rgb(40, 160, 90)
            )
            embed_partida.title = "✅ Partida Confirmada"
            embed_partida.add_field(name="⚔️ Estilo de Jogo", value=f"{mode1.capitalize()} ({self.modo_jogo})", inline=False)
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
            embed_atualizado = criar_embed_fila(nome_fila=self.nome_fila, modo_jogo=self.modo_jogo, valor_aposta=f"R$ {self.valor_str}")
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
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas mediadores podem gerar filas!", ephemeral=True)
            return

        canal_selecionado = interaction.guild.get_channel(self.values[0].id)
        
        if not canal_selecionado:
            await interaction.response.send_message("❌ Não foi possível encontrar o canal selecionado no servidor.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"⚙️ Gerando **15 filas** em ordem decrescente no modo **{self.parent_view.modo}** com o nome **{self.parent_view.nome_fila}** no canal {canal_selecionado.mention}...", 
            ephemeral=True
        )

        try:
            await interaction.message.delete()
        except Exception:
            pass

        valor_atual_idx = 0
        try:
            for _ in range(15):
                val_num = self.parent_view.valores_nums[valor_atual_idx % len(self.parent_view.valores_nums)]
                val_str = f"{val_num:.2f}".replace(".", ",")
                
                # CORREÇÃO AQUI: Passando valor_aposta em vez de valor_str
                embed = criar_embed_fila(nome_fila=self.parent_view.nome_fila, modo_jogo=self.parent_view.modo, valor_aposta=f"R$ {val_str}")
                view = FilaView(nome_fila=self.parent_view.nome_fila, modo_jogo=self.parent_view.modo, valor_str=val_str, valor_num=val_num)
                
                await canal_selecionado.send(embed=embed, view=view)
                valor_atual_idx += 1

            await interaction.followup.send(f"✅ As **15 filas** em ordem decrescente foram criadas com sucesso no canal {canal_selecionado.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ocorreu um erro ao enviar as filas: {e}", ephemeral=True)

class ModalNomeEValores(discord.ui.Modal, title="Configurar Nome e Valores"):
    nome_fila_input = discord.ui.TextInput(
        label="Nome da Fila",
        placeholder="Ex: Fila Principal, X1 dos Crias...",
        style=discord.TextStyle.short,
        required=True
    )
    valores_input = discord.ui.TextInput(
        label="Valores (use vírgula, ex: 10,00, 5,00, 1,00)",
        placeholder="Ex: 10,00, 5,00, 1,00",
        style=discord.TextStyle.short,
        required=True
    )

    def __init__(self, modo):
        super().__init__()
        self.modo = modo

    async def on_submit(self, interaction: discord.Interaction):
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas mediadores podem configurar filas!", ephemeral=True)
            return

        try:
            nome_fila = self.nome_fila_input.value.strip()
            input_cru = self.valores_input.value.strip()
            
            valores_nums = []
            for v in input_cru.split(","):
                v_clean = v.strip().replace(",", ".")
                if v_clean:
                    try:
                        valores_nums.append(float(v_clean))
                    except ValueError:
                        pass

            if not valores_nums:
                valores_nums = [0.50]
            else:
                valores_nums.sort(reverse=True)

            class ViewSelecaoCanalUnico(discord.ui.View):
                def __init__(self, nome_fila, valores_nums, modo):
                    super().__init__(timeout=60)
                    self.nome_fila = nome_fila
                    self.valores_nums = valores_nums
                    self.modo = modo
                    self.add_item(CanalUnicoSelect(self))

            view_canal = ViewSelecaoCanalUnico(nome_fila, valores_nums, self.modo)
            if interaction.response.is_done():
                await interaction.followup.send("📁 Agora **selecione o canal único abaixo** para gerar as 15 filas:", view=view_canal, ephemeral=True)
            else:
                await interaction.response.send_message("📁 Agora **selecione o canal único abaixo** para gerar as 15 filas:", view=view_canal, ephemeral=True)
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Ocorreu um erro ao processar os dados: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Ocorreu um erro ao processar os dados: {e}", ephemeral=True)

class SelectModoFila(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="4v4", value="4v4"),
            discord.SelectOption(label="3v3", value="3v3"),
            discord.SelectOption(label="2v2", value="2v2"),
            discord.SelectOption(label="1v1", value="1v1"),
        ]
        super().__init__(placeholder="Escolha o modo de jogo (1v1, 2v2, 3v3 ou 4v4)", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas mediadores podem gerar filas!", ephemeral=True)
            return
        modo = self.values[0]
        await interaction.response.send_modal(ModalNomeEValores(modo))

class ViewSelecaoModoFila(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(SelectModoFila())

class ModalCriarFilasDummy(discord.ui.Modal, title="Gerar Filas"):
    async def on_submit(self, interaction: discord.Interaction):
        pass

@bot.tree.command(name="criar_15_filas", description="Gera 15 filas escolhendo primeiro o modo de jogo em um único canal")
async def slash_criar_15_filas(interaction: discord.Interaction):
    if not verificar_permissao_global(interaction.user):
        await interaction.response.send_message("❌ Apenas mediadores podem usar este comando!", ephemeral=True)
        return

    view_modo = ViewSelecaoModoFila()
    await interaction.response.send_message("🎮 **Passo 1:** Escolha abaixo o modo de jogo desejado:", view=view_modo, ephemeral=True)

# ------------------------------------------------------------------
# PAINEL DE CONTROLE DA SALA DO MEDIADOR
# ------------------------------------------------------------------
class VencedorSelect(discord.ui.Select):
    def __init__(self, membros):
        options = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in membros]
        super().__init__(placeholder="Selecione o jogador vencedor...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas mediadores podem definir o vencedor!", ephemeral=True)
            return

        vencedor_id = int(self.values[0])
        ganhador = interaction.guild.get_member(vencedor_id) or await interaction.guild.fetch_member(vencedor_id)
        
        if ganhador.id not in estatisticas_jogadores:
            estatisticas_jogadores[ganhador.id] = {"vitorias": 0, "derrotas": 0, "streak": 0, "streak_atual": 0, "coins": 0}
        
        estatisticas_jogadores[ganhador.id]["vitorias"] += 1
        estatisticas_jogadores[ganhador.id]["coins"] += 1
        estatisticas_jogadores[ganhador.id]["streak_atual"] += 1
        
        if estatisticas_jogadores[ganhador.id]["streak_atual"] > estatisticas_jogadores[ganhador.id]["streak"]:
            estatisticas_jogadores[ganhador.id]["streak"] = estatisticas_jogadores[ganhador.id]["streak_atual"]

        thread_id = interaction.channel.id
        ids_partida = jogadores_partidas.get(thread_id, [])
        for pid in ids_partida:
            if pid != ganhador.id:
                if pid not in estatisticas_jogadores:
                    estatisticas_jogadores[pid] = {"vitorias": 0, "derrotas": 0, "streak": 0, "streak_atual": 0, "coins": 0}
                estatisticas_jogadores[pid]["derrotas"] += 1
                estatisticas_jogadores[pid]["streak_atual"] = 0

        await interaction.response.send_message(
            f"🏆 **Vencedor Definido com Sucesso!**\n"
            f"👑 **Jogador:** {ganhador.mention}\n"
            f"📈 **Vitórias Consecutivas:** {estatisticas_jogadores[ganhador.id]['streak_atual']}\n"
            f"🏆 **Vitórias Totais:** {estatisticas_jogadores[ganhador.id]['vitorias']}\n"
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
        super().__init__(placeholder="Selecione quem ganhou por W.O...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas mediadores podem definir o W.O!", ephemeral=True)
            return

        vencedor_id = int(self.values[0])
        ganhador = interaction.guild.get_member(vencedor_id) or await interaction.guild.fetch_member(vencedor_id)
        
        if ganhador.id not in estatisticas_jogadores:
            estatisticas_jogadores[ganhador.id] = {"vitorias": 0, "derrotas": 0, "streak": 0, "streak_atual": 0, "coins": 0}
        
        estatisticas_jogadores[ganhador.id]["vitorias"] += 1
        estatisticas_jogadores[ganhador.id]["coins"] += 1
        estatisticas_jogadores[ganhador.id]["streak_atual"] += 1
        
        if estatisticas_jogadores[ganhador.id]["streak_atual"] > estatisticas_jogadores[ganhador.id]["streak"]:
            estatisticas_jogadores[ganhador.id]["streak"] = estatisticas_jogadores[ganhador.id]["streak_atual"]

        thread_id = interaction.channel.id
        ids_partida = jogadores_partidas.get(thread_id, [])
        for pid in ids_partida:
            if pid != ganhador.id:
                if pid not in estatisticas_jogadores:
                    estatisticas_jogadores[pid] = {"vitorias": 0, "derrotas": 0, "streak": 0, "streak_atual": 0, "coins": 0}
                estatisticas_jogadores[pid]["derrotas"] += 1
                estatisticas_jogadores[pid]["streak_atual"] = 0

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

class PainelMediadorSelect(discord.ui.Select):
    def __init__(self, membros_partida, thread_id, mediador_id):
        self.membros_partida = membros_partida
        self.thread_id = thread_id
        self.mediador_id = mediador_id
        
        options = [
            discord.SelectOption(label="Escolher o vencedor", value="vencedor", description="Define o jogador vencedor da partida", emoji="🏆"),
            discord.SelectOption(label="Dar vitória por w.o", value="wo", description="Define a vitória por W.O", emoji="⚠️"),
            discord.SelectOption(label="Reembolsar e finalizar", value="reembolso", description="Mostra o valor para reembolso", emoji="💸"),
            discord.SelectOption(label="Finalizar partida", value="finalizar", description="Finaliza e deleta o tópico", emoji="🔒")
        ]
        super().__init__(placeholder="Selecione uma opção de gerenciamento...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if not verificar_permissao_global(interaction.user):
            await interaction.response.send_message("❌ Apenas mediadores podem usar estas opções!", ephemeral=True)
            return

        escolha = self.values[0]

        if escolha == "vencedor":
            if not self.membros_partida:
                await interaction.response.send_message("❌ Nenhum jogador elegível encontrado neste tópico.", ephemeral=True)
                return
            view = ViewVencedor(self.membros_partida)
            await interaction.response.send_message("👇 Escolha abaixo o jogador **Vencedor**:", view=view, ephemeral=True)

        elif escolha == "wo":
            if not self.membros_partida:
                await interaction.response.send_message("❌ Nenhum jogador elegível encontrado neste tópico.", ephemeral=True)
                return
            view = ViewWo(self.membros_partida)
            await interaction.response.send_message("👇 Escolha abaixo quem ganhou por **W.O**:", view=view, ephemeral=True)

        elif escolha == "reembolso":
            valor_base = valores_apostas_partidas.get(self.thread_id, 0.50)
            valor_str = f"R$ {valor_base:.2f}".replace(".", ",")
            taxa_centavos_exibicao = int(round(taxa_global_centavos * 100))

            embed_reembolso = discord.Embed(
                title="💸 Reembolso Solicitado",
                description=(
                    f"O valor exato para o reembolso (descontando a taxa de {taxa_centavos_exibicao}c) é:\n\n"
                    f"🔑 **Valor do Reembolso:** `{valor_str}`"
                ),
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed_reembolso, ephemeral=True)

        elif escolha == "finalizar":
            await interaction.response.send_message("🔒 **A partida foi finalizada. Deletando o tópico em instantes...**", ephemeral=True)
            if isinstance(interaction.channel, discord.Thread):
                import asyncio
                await asyncio.sleep(2)
                try:
                    await interaction.channel.delete()
                except Exception:
                    pass

class PainelMediadorView(discord.ui.View):
    def __init__(self, membros_partida, thread_id, mediador_id):
        super().__init__(timeout=None)
        self.add_item(PainelMediadorSelect(membros_partida, thread_id, mediador_id))

@bot.tree.command(name="painel_sala", description="Abre o painel de controle da sala")
async def slash_painel_sala(interaction: discord.Interaction):
    if not verificar_permissao_global(interaction.user):
        await interaction.response.send_message("❌ Apenas mediadores podem usar este comando!", ephemeral=True)
        return

    if not isinstance(interaction.channel, discord.Thread):
        await interaction.response.send_message("❌ Este comando só pode ser utilizado dentro do tópico da partida!", ephemeral=True)
        return

    thread_id = interaction.channel.id
    
    ids_jogadores = jogadores_partidas.get(thread_id, [])
    membros_partida = []
    for j_id in ids_jogadores:
        membro = interaction.guild.get_member(j_id) or await interaction.guild.fetch_member(j_id)
        if membro:
            membros_partida.append(membro)

    embed = discord.Embed(
        title="⚙️ Painel de Controle do Mediador",
        description="Utilize o menu abaixo para gerenciar a partida:",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Painel exclusivo para controle do Mediador.")

    mediador_atribuido = mediadores_partidas.get(thread_id)
    mediador_id = mediador_atribuido.id if mediador_atribuido else interaction.user.id
    view = PainelMediadorView(membros_partida, thread_id, mediador_id)
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="finalizar_sala", description="Abre o painel de gerenciamento/finalização da sala atual")
async def slash_finalizar_sala(interaction: discord.Interaction):
    if not verificar_permissao_global(interaction.user):
        await interaction.response.send_message("❌ Apenas mediadores podem usar este comando!", ephemeral=True)
        return

    if not isinstance(interaction.channel, discord.Thread):
        await interaction.response.send_message("❌ Este comando só pode ser utilizado dentro do tópico da partida!", ephemeral=True)
        return

    thread_id = interaction.channel.id
    
    ids_jogadores = jogadores_partidas.get(thread_id, [])
    membros_partida = []
    for j_id in ids_jogadores:
        membro = interaction.guild.get_member(j_id) or await interaction.guild.fetch_member(j_id)
        if membro:
            membros_partida.append(membro)

    embed = discord.Embed(
        title="⚙️ Painel de Controle do Mediador",
        description="Utilize o menu abaixo para gerenciar a partida:",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Painel exclusivo para controle do Mediador.")

    mediador_atribuido = mediadores_partidas.get(thread_id)
    mediador_id = mediador_atribuido.id if mediador_atribuido else interaction.user.id
    view = PainelMediadorView(membros_partida, thread_id, mediador_id)
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

# ------------------------------------------------------------------
# EVENTO ON_MESSAGE: DETECTAR QUANDO OS JOGADORES DIZEM "PAGO"
# ------------------------------------------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if isinstance(message.channel, discord.Thread):
        thread_id = message.channel.id
        
        if thread_id in jogadores_partidas and thread_id in mediadores_partidas:
            conteudo = message.content.lower().strip()
            if "pago" in conteudo or "paguei" in conteudo:
                autor_id = message.author.id
                validos_ids = jogadores_partidas[thread_id]

                if autor_id in validos_ids:
                    if thread_id not in pagamentos_pendentes:
                        pagamentos_pendentes[thread_id] = set()
                    
                    pagamentos_pendentes[thread_id].add(autor_id)

                    if set(validos_ids).issubset(pagamentos_pendentes[thread_id]):
                        pagamentos_pendentes[thread_id].clear()
                        mediador = mediadores_partidas[thread_id]

                        view_recebimento = ConfirmarRecebimentoView(mediador)
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
