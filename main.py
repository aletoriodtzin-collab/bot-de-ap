import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.all()

class BotAP(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Comandos e painéis sincronizados com o Discord!")

bot = BotAP()

LIMITE_VAGAS = 12
fila_ap = []

class PainelAP(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Entrar na Fila 🎮", style=discord.ButtonStyle.green, custom_id="btn_entrar")
    async def entrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in fila_ap:
            await interaction.response.send_message("❌ Você já está na fila desta AP!", ephemeral=True)
            return

        if len(fila_ap) >= LIMITE_VAGAS:
            await interaction.response.send_message("⚠️ Fila lotada! Aguarde a próxima sala.", ephemeral=True)
            return

        fila_ap.append(interaction.user)
        await interaction.response.send_message(f"✅ {interaction.user.mention} entrou na lista!", ephemeral=True)
        await atualizar_painel(interaction)

    @discord.ui.button(label="Sair da Fila ❌", style=discord.ButtonStyle.red, custom_id="btn_sair")
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in fila_ap:
            await interaction.response.send_message("❌ Você não está na fila!", ephemeral=True)
            return

        fila_ap.remove(interaction.user)
        await interaction.response.send_message("🚪 Você saiu da fila da AP.", ephemeral=True)
        await atualizar_painel(interaction)

async def atualizar_painel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔥 ORGANIZAÇÃO DE AP - SALA ABERTA 🔥",
        description=f"Clique no botão abaixo para garantir sua vaga!\n\n**Vagas:** `{len(fila_ap)}/{LIMITE_VAGAS}`",
        color=discord.Color.gold()
    )

    if fila_ap:
        lista_membros = "\n".join([f"`{i+1}.` {user.mention}" for i, user in enumerate(fila_ap)])
        embed.add_field(name="📋 Jogadores/Lines Na Fila:", value=lista_membros, inline=False)
    else:
        embed.add_field(name="📋 Jogadores/Lines Na Fila:", value="*Ninguém na fila ainda. Seja o primeiro!*", inline=False)

    await interaction.message.edit(embed=embed, view=PainelAP())

@bot.tree.command(name="painel_ap", description="Abre o painel de inscrição da AP")
@app_commands.checks.has_permissions(administrator=True)
async def criar_painel(interaction: discord.Interaction):
    global fila_ap
    fila_ap = []

    embed = discord.Embed(
        title="🔥 ORGANIZAÇÃO DE AP - SALA ABERTA 🔥",
        description=f"Clique no botão abaixo para garantir sua vaga!\n\n**Vagas:** `0/{LIMITE_VAGAS}`",
        color=discord.Color.gold()
    )
    embed.add_field(name="📋 Jogadores/Lines Na Fila:", value="*Ninguém na fila ainda. Seja o primeiro!*", inline=False)

    await interaction.response.send_message(embed=embed, view=PainelAP())

@bot.tree.command(name="resetar_fila", description="Limpa todos os jogadores da fila atual")
@app_commands.checks.has_permissions(administrator=True)
async def resetar(interaction: discord.Interaction):
    global fila_ap
    fila_ap = []
    await interaction.response.send_message("🧹 Fila resetada com sucesso!", ephemeral=True)

# Ligar o Bot (Substitua abaixo pelo seu Token do Discord Portal)
bot.run("f5244c878494111ea81468c378c7ec108ba63b86f97d576a6730bf78cdb119bb")
                   
