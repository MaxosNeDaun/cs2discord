import discord
from discord.ext import commands
from discord import app_commands
import os

# --- ТВОИ НАСТРОЙКИ ---
ADMIN_CHANNEL_ID = 1127290770571931739
PUBLIC_LIST_CHANNEL_ID = 1359230337602949391
# ----------------------

class AdminReview(discord.ui.View):
    def __init__(self, content, author_name):
        super().__init__(timeout=None)
        self.content = content
        self.author_name = author_name

    @discord.ui.button(label="Одобрить ✅", style=discord.ButtonStyle.success, custom_id="app_btn")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.client.get_channel(PUBLIC_LIST_CHANNEL_ID)
        
        if channel:
            new_entry = f"{self.content}\n(Автор: {self.author_name})"
            
            # Ищем последнее сообщение бота в этом канале
            last_msg = None
            async for message in channel.history(limit=10):
                if message.author == interaction.client.user:
                    last_msg = message
                    break
            
            if last_msg:
                # Если нашли сообщение бота — редактируем его, добавляя новую строку
                updated_content = last_msg.content + "\n" + new_entry
                # Проверка на лимит символов в Discord (2000)
                if len(updated_content) > 1900:
                    await channel.send(new_entry) # Если лимит превышен, создаем новое
                else:
                    await last_msg.edit(content=updated_content)
            else:
                # Если сообщений еще нет — отправляем первое
                await channel.send(new_entry)

            await interaction.response.edit_message(content=f"✅ Запись добавлена в общий список!", view=None, embed=None)
        else:
            await interaction.response.send_message("Ошибка: Канал не найден!", ephemeral=True)

    @discord.ui.button(label="Отклонить ❌", style=discord.ButtonStyle.danger, custom_id="rej_btn")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"❌ Отклонено модератором {interaction.user.mention}", view=None, embed=None)

class MyModal(discord.ui.Modal, title='Предложить запись'):
    answer = discord.ui.TextInput(
        label='Ваше сообщение (1-200 символов)',
        style=discord.TextStyle.paragraph,
        min_length=1,
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        admin_channel = interaction.client.get_channel(ADMIN_CHANNEL_ID)
        if not admin_channel:
            await interaction.response.send_message("Ошибка доступа к админ-каналу!", ephemeral=True)
            return

        embed = discord.Embed(title="📝 Новая заявка", color=discord.Color.orange())
        embed.add_field(name="Автор", value=interaction.user.mention)
        embed.add_field(name="Текст", value=self.answer.value, inline=False)
        
        await admin_channel.send(embed=embed, view=AdminReview(self.answer.value, interaction.user.display_name))
        await interaction.response.send_message('Отправлено на проверку!', ephemeral=True)

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

bot = Bot()

@bot.tree.command(name="setup", description="Создать кнопку")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    await interaction.response.send_message("Кнопка для предложений:", view=StartView())

bot.run(os.getenv('TOKEN'))
