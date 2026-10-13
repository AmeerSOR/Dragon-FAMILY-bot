
import os
import json
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
COUNTER_FILE = "counter.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def next_invoice():
    try:
        with open(COUNTER_FILE, "r") as f:
            number = json.load(f).get("number", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        number = 0

    number += 1
    with open(COUNTER_FILE, "w") as f:
        json.dump({"number": number}, f)
    return number


class InvoiceModal(discord.ui.Modal, title="فاتورة جديدة"):
    product = discord.ui.TextInput(
        label="اسم المنتج",
        placeholder="اكتب اسم المنتج",
        max_length=100
    )
    quantity = discord.ui.TextInput(
        label="الكمية",
        placeholder="مثال: 2",
        max_length=6
    )
    price = discord.ui.TextInput(
        label="سعر الوحدة",
        placeholder="مثال: 5000",
        max_length=12
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qty = int(str(self.quantity.value))
            price = float(str(self.price.value))
            if qty < 1 or price < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "الكمية لازم تكون عدد موجب والسعر صفر أو أكثر.",
                ephemeral=True
            )
            return

        total = qty * price
        number = next_invoice()
        embed = discord.Embed(
            title=f"🧾 فاتورة رقم {number:04d}",
            color=0xF28C28
        )
        embed.add_field(name="المنتج", value=self.product.value)
        embed.add_field(name="الكمية", value=str(qty))
        embed.add_field(name="سعر الوحدة", value=f"{price:,.2f}")
        embed.add_field(name="الإجمالي", value=f"{total:,.2f}")
        embed.add_field(
            name="البائع",
            value=interaction.user.mention,
            inline=False
        )

        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel is None:
            await interaction.response.send_message(
                "إعدادات روم الفواتير غير مكتملة.",
                ephemeral=True
            )
            return

        await channel.send(embed=embed)
        await interaction.response.send_message(
            f"تم إنشاء الفاتورة رقم {number:04d}.",
            ephemeral=True
        )


class InvoiceView(discord.ui.View):
    @discord.ui.button(
        label="إنشاء فاتورة",
        style=discord.ButtonStyle.primary,
        emoji="🧾"
    )
    async def create_invoice(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(InvoiceModal())


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot ready: {bot.user}")


@bot.tree.command(
    name="setup_invoice",
    description="نشر زر إنشاء الفاتورة"
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_invoice(interaction: discord.Interaction):
    await interaction.response.send_message(
        "اضغط الزر لإنشاء فاتورة جديدة.",
        view=InvoiceView()
    )


if not TOKEN:
    raise RuntimeError("Set the DISCORD_TOKEN environment variable.")

bot.run(TOKEN)
