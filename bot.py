import discord
from discord.ext import commands, tasks
import urllib.request
import asyncio
from bs4 import BeautifulSoup
import re
import os

TOKEN = os.environ["DISCORD_TOKEN"]
CATEGORY_ID = int(os.environ["CATEGORY_ID"])
INTERVAL_MINUTES = int(os.environ.get("INTERVAL_MINUTES", "30"))

URL = "https://metaforge.app/wardogs/market"
_last_price: str | None = None

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def fetch_gold_price() -> str | None:
    def _sync_fetch() -> str | None:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            req = urllib.request.Request(URL, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", "ignore")
        except Exception as e:
            print(f"Blad pobierania: {e}")
            return None

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)

        match = re.search(r"Current\s+([\d,]+)", text)
        if match:
            return "$" + match.group(1)

        return None

    return await asyncio.to_thread(_sync_fetch)


async def update_category_name(force: bool = False) -> str:
    global _last_price

    category = bot.get_channel(CATEGORY_ID)
    if category is None or not isinstance(category, discord.CategoryChannel):
        return "Nie znaleziono kategorii o podanym ID."

    price = await fetch_gold_price()
    if price is None:
        return "Nie udalo sie pobrac ceny zlota."

    if not force and price == _last_price:
        return f"Cena bez zmian: {price}"

    _last_price = price
    new_name = f"💰 GOLD || {price} ||"

    if len(new_name) > 100:
        new_name = new_name[:100]

    try:
        await category.edit(name=new_name)
        return f"Zmieniono nazwe kategorii na: {new_name}"
    except discord.Forbidden:
        return "Brak uprawnien (Zarzadzanie kanalami)."
    except discord.HTTPException as e:
        return f"Blad Discord API: {e}"


@bot.command(name="updateprice")
async def update_price_cmd(ctx: commands.Context):
    await ctx.send("Pobieram aktualna cene zlota...")
    result = await update_category_name(force=True)
    await ctx.send(result)


@bot.command(name="price")
async def show_price_cmd(ctx: commands.Context):
    price = await fetch_gold_price()
    if price:
        await ctx.send(f"Dzisiejsza cena zlota: {price}")
    else:
        await ctx.send("Nie udalo sie pobrac ceny.")


@tasks.loop(minutes=INTERVAL_MINUTES)
async def auto_update():
    print("Automatyczna aktualizacja ceny...")
    result = await update_category_name()
    print(result)


@auto_update.before_loop
async def before_auto_update():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")
    print(f"Kategoria ID: {CATEGORY_ID}")
    print(f"Auto-aktualizacja co {INTERVAL_MINUTES} min")
    if not auto_update.is_running():
        auto_update.start()


bot.run(TOKEN)
