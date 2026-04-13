import discord
from discord.ext import commands
import os

# --- НАСТРОЙКИ (Вставь свои ID) ---
ADMIN_CHANNEL_ID = 123456789012345678  # Канал, куда приходят заявки
PUBLIC_LIST_CHANNEL_ID = 123456789012345678  # Канал, куда попадает одобренное
# ---------------------------------

class AdminReview(discord.ui.View):
    def __init__(self, content, author_name):
        super().__init__(timeout=None)
        self.content = content
        self.author_name = author_name

    @discord.ui.button(label="Одобрить ✅", style=discord.ButtonStyle.success, custom_id="app_btn")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.client.get_channel(PUBLIC_LIST_CHANNEL_ID)
        if channel:
            await channel.send(f"**Новая запись в списке:**\n> {self.content}\n*(Автор: {self.author_name})*")
            await interaction.response.edit_message(content=f"✅ Одобрено модератором {interaction.user.mention}", view=None, embed=None)
        else:
            await interaction.response.send_message("Ошибка: Канал для списка не найден!", ephemeral=True)

    @discord.ui.button(label="Отклонить ❌", style=discord.ButtonStyle.danger, custom_id="rej_btn")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"❌ Отклонено модератором {interaction.user.mention}", view=None, embed=None)

class MyModal(discord.ui.Modal, title='Предложить запись в список'):
    answer = discord.ui.TextInput(
        label='Ваше сообщение',
        style=discord.TextStyle.paragraph,
        placeholder='Напишите здесь то, что попадет в список...',
        min_length=5,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        admin_channel = interaction.client.get_channel(ADMIN_CHANNEL_ID)
        if not admin_channel:
            await interaction.response.send_message("Ошибка: Канал модерации не настроен!", ephemeral=True)
            return

        embed = discord.Embed(title="📝 Новая заявка", color=discord.Color.orange())
        embed.add_field(name="Автор", value=interaction.user.mention)
        embed.add_field(name="Текст", value=self.answer.value, inline=False)
        
        await admin_channel.send(embed=embed, view=AdminReview(self.answer.value, interaction.user.display_name))
        await interaction.response.send_message('Ваше сообщение отправлено на проверку модераторам!', ephemeral=True)

class StartView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Оставить запись", style=discord.ButtonStyle.primary, custom_id="main_start_btn")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MyModal())

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Регистрируем View, чтобы кнопки работали всегда, даже после перезагрузки
        self.add_view(StartView())
        await self.tree.sync()

bot = Bot()

@bot.tree.command(name="setup", description="Создать кнопку для отправки заявок")
@commands.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    await interaction.response.send_message("Нажмите кнопку ниже, чтобы предложить свою запись:", view=StartView())

bot.run(os.getenv('TOKEN'))