import disnake
from disnake.ext import commands
import random
import config

class Etc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="info", description="Узнать команды бота")
    async def infa(self, ctx):
        random_color = disnake.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        embed=disnake.Embed(
            title="**Список команд:**",
            color=random_color
        )
        embed.add_field(name="Экономика", value=f"\n\n!binus - Бонусные {config.NAME_CURRENCY}\n!bal - Узнать свой баланс\n/dice *пользователь* *ставка*\n/top - Топ баланса", inline=False)
        embed.add_field(name="Прочее", value="\n\n/profile - Посмотреть свой профиль", inline=False)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Etc(bot))