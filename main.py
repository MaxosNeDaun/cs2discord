import discord
from discord.ext import commands
from discord import app_commands
import os

# --- ТВОИ НАСТРОЙКИ ---
ADMIN_CHANNEL_ID = 1127290770571931739
PUBLIC_LIST_CHANNEL_ID = 1359230337602949391
# ----------------------

def save_to_file(content, author):
    """Функция для записи в файл"""
    with open("database.txt", "a", encoding="utf-8") as f:
        f.write(f"Автор: {author} | Запись: {content}\n")

class AdminReview(discord.ui.View):
    def __init__(self, content, author_name):
        super().__init__(timeout=None)
        self.content = content
        self.author_name = author_name

    @discord.ui.button(label="Одобрить ✅", style=discord.ButtonStyle.success, custom_id="app_btn")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.client.get_channel(PUBLIC_LIST_CHANNEL_ID)
        if channel:
            # 1. Отправляем в канал
            await channel.send(f"**Новая запись в списке:**\n> {self.content}\n*(Автор: {self.author_name})*")
            
            # 2. СОХРАНЯЕМ В ФАЙЛ
            save_to_file(self.content, self.author_name)
            
            # 3. Обновляем сообщение у админов
            await interaction.response.edit_message(content=f"✅ Одобрено модератором {interaction.user.mention} и сохранено в базу.", view=None, embed=None)
        else:
            await interaction.response.send_message("Ошибка: Канал для списка не найден!", ephemeral=True)

    @discord.ui.button(label="Отклонить ❌", style=discord.ButtonStyle.danger, custom_id="rej_btn")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"❌ Отклонено модератором {interaction.user.mention}", view=None, embed=None)

class MyModal(discord.ui.Modal, title='Предложить запись'):
    answer = discord.ui.TextInput(
        label='Ваше сообщение (1-200 символов)',
        style=discord.TextStyle.paragraph,
        placeholder='Введите ваш текст здесь...',
        min_length=1,
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        admin_channel = interaction.client.get_channel(ADMIN_CHANNEL_ID)
        if not admin_channel:
            await interaction.response.send_message(f"Ошибка: Канал модерации не найден!", ephemeral=True)
            return

        embed = discord.Embed(title="📝 Новая заявка", color=discord.Color.orange())
        embed.add_field(name="Автор", value=interaction.user.mention)
        embed.add_field(name="Текст", value=self.answer.value, inline=False)
        
        await admin_channel.send(embed=embed, view=AdminReview(self.answer.value, interaction.user.display_name))
        await interaction.response.send_message('Ваше сообщение отправлено на проверку!', ephemeral=True)

class StartView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Предложить название", style=discord.ButtonStyle.primary, custom_id="main_start_btn")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MyModal())

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(StartView())
        await self.tree.sync()
        print(f"Бот запущен как {self.user}")

bot = Bot()

@bot.tree.command(name="setup", description="Создать кнопку для заявок")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    await interaction.response.send_message("Нажмите кнопку ниже, чтобы предложить новое название:", view=StartView())

# Команда для админов, чтобы скачать файл с записями
@bot.tree.command(name="download_list", description="Скачать файл со всеми одобренными записями")
@app_commands.checks.has_permissions(administrator=True)
async def download_list(interaction: discord.Interaction):
    if os.path.exists("database.txt"):
        await interaction.response.send_message("Вот список всех записей:", file=discord.File("database.txt"))
    else:
        await interaction.response.send_message("Список пока пуст.", ephemeral=True)

bot.run(os.getenv('TOKEN'))
