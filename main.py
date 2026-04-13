import discord
from discord.ext import commands
from discord import app_commands  # ВОТ ЭТОЙ СТРОКИ НЕ ХВАТАЛО
import os

# --- НАСТРОЙКИ (Замени на свои цифры) ---
ADMIN_CHANNEL_ID = 1127290770571931739  # Канал для модераторов
PUBLIC_LIST_CHANNEL_ID = 1359230337602949391  # Канал для одобренных постов
# ---------------------------------------

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
            # Если бот не видит канал, он напишет это в чат
            await interaction.response.send_message(f"Ошибка: Канал модерации (ID: {ADMIN_CHANNEL_ID}) не найден или у бота нет прав!", ephemeral=True)
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
        intents.members = True # На всякий случай для имен пользователей
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(StartView())
        await self.tree.sync()
        print(f"Бот запущен под именем {self.user}")

bot = Bot()

@bot.tree.command(name="setup", description="Создать кнопку для отправки заявок")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    await interaction.response.send_message("Нажмите кнопку ниже, чтобы предложить свою запись:", view=StartView())

bot.run(os.getenv('TOKEN'))
