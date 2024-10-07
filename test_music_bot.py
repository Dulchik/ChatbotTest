import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
@commands.has_permissions(administrator=True)
async def unload(ctx, extension):
    try:
        await bot.unload_extension(f'cogs.{extension}')
        await ctx.send(f'Unloaded cog: {extension}')
    except Exception as e:
        await ctx.send(f"Error unloading cog: {extension}\n{e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def load(ctx, extension):
    try:
        await bot.load_extension(f'cogs.{extension}')
        await ctx.send(f'Loaded cog: {extension}')
    except Exception as e:
        await ctx.send(f"Error Loading cog: {extension}\n{e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, extension):
    try:
        await bot.unload_extension(f'cogs.{extension}')
        await bot.load_extension(f'cogs.{extension}')
        await ctx.send(f'Reloaded cog: {extension}')
    except Exception as e:
        await ctx.send(f"Error reloading cog: {extension}\n{e}")

async def load_cogs():
    # Assume the cogs are in the "cogs" directory
    for cog in os.listdir('./cogs'):
        if cog.endswith('.py') and cog != '__init__.py':
            await bot.load_extension(f'cogs.{cog[:-3]}')

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await load_cogs()  # Ensure this awaits properly

bot.run("MTI5MTQzMjQ2NjAyODAzNjE0MA.GmfB53.6yl3oNI-RKC0Pqh5DrjpElva-fD_q3GdoaYCso")