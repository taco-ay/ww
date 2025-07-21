import discord
from discord.ext import commands
from discord import ui, ButtonStyle, TextStyle
import sqlite3
import os
from datetime import datetime

# === Veritabanı bağlantısı ===
DB_PATH = "projects.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Tablonun var olup olmadığını kontrol et ve yoksa oluştur
cursor.execute("""
CREATE TABLE IF NOT EXISTS projects (
    p_id INTEGER PRIMARY KEY AUTOINCREMENT,
    u_id TEXT,
    name TEXT,
    description TEXT,
    image_path TEXT,
    created_at TEXT
)
""")
conn.commit()

# === Modal tanımı ===
class ProjectModal(ui.Modal, title="Yeni Proje Ekle"):
    project_name = ui.TextInput(label="Proje Adı")
    project_desc = ui.TextInput(label="Açıklama", style=TextStyle.paragraph)
    project_image = ui.TextInput(label="Fotoğraf URL (opsiyonel)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        name = self.project_name.value
        desc = self.project_desc.value
        img_url = self.project_image.value if self.project_image.value else None

        # Veritabanına kaydet
        cursor.execute("""
        INSERT INTO projects (u_id, name, description, image_path, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, desc, img_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

        # Kanala mesaj at
        msg = f"✅ **Yeni Proje Eklendi!**\n📌 **Adı:** {name}\n📝 **Açıklama:** {desc}\n👤 **Ekleyen:** <@{user_id}>"
        if img_url:
            await interaction.channel.send(msg)
            await interaction.channel.send(img_url)
        else:
            await interaction.channel.send(msg)

        await interaction.response.send_message("✅ Projen başarıyla kaydedildi!", ephemeral=True)

# === Buton tanımı ===
class ProjectButton(ui.Button):
    def __init__(self):
        super().__init__(label="Yeni Proje Ekle", style=ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ProjectModal())

# === View (Butonu taşıyan yapı) ===
class ProjectView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ProjectButton())

# === Bot ayarları ===
intents = discord.Intents.default()
intents.message_content = True # This line is crucial for command processing
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} olarak giriş yapıldı!")
    # Optionally, to ensure persistent views work after bot restarts,
    # you can add them to the bot if they are meant to be persistent.
    # If the button is only sent with the command, this might not be strictly necessary.
    # bot.add_view(ProjectView()) # Uncomment if you want the view to persist across restarts

# === Komut: proje ekleme butonunu göster ===
@bot.command()
async def proje(ctx):
    await ctx.send("Yeni bir proje eklemek için aşağıdaki butona tıklayın:", view=ProjectView())

# === Komut: projeleri listele ===
@bot.command()
async def projeler(ctx):
    cursor.execute("SELECT p_id, name, description, u_id, created_at FROM projects ORDER BY p_id DESC LIMIT 5")
    rows = cursor.fetchall()
    if not rows:
        await ctx.send("Henüz hiç proje eklenmemiş.")
        return

    msg = "**📂 Son Eklenen Projeler:**\n"
    for p_id, name, desc, u_id, created_at in rows:
        msg += f"➡ **{p_id}. {name}** - {desc} (Ekleyen <@{u_id}> | {created_at})\n"
    await ctx.send(msg)

bot.run("your bot id")