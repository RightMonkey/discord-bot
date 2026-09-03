import disnake
from disnake.ext import commands, tasks
from disnake.ui import View, button
from disnake import ButtonStyle, Interaction
import random
import datetime
from loguru import logger
import json
import config
import asyncio


def load_user_data():
    try:
        with open(user_data_file, 'r') as f:
            data = json.load(f)
            
            for guild_id, user_data in data.items():
                for user_id, user_info in user_data.items():
                    if 'last_bonus' in user_info and user_info['last_bonus']:
                        user_info['last_bonus'] = datetime.datetime.fromisoformat(user_info['last_bonus'])
            logger.info("Данные пользователей успешно загружены")
            return data
    except FileNotFoundError:
        logger.warning("Файл с данными пользователей не найден. Будет создан новый файл.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {e}")
        return {}


def save_user_data(data):
    for guild_id, user_data in data.items():
        for user_id, user_info in user_data.items():
            if 'last_bonus' in user_info:
                if isinstance(user_info['last_bonus'], datetime.datetime):
                    user_info['last_bonus'] = user_info['last_bonus'].isoformat()

    with open(user_data_file, 'w') as f:
        json.dump(data, f, indent=4)
    logger.info("Данные пользователей сохранены")


async def async_load_user_data():
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, load_user_data)

async def async_save_user_data(data):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, save_user_data, data)

user_data_file = 'data/user_data.json'
user_data = load_user_data()

class DiceConfirmView(View):
    def __init__(self, bettor, opponent, stake, guild_id, user_data, bot, timeout=120):
        super().__init__(timeout=timeout)
        self.bettor = bettor
        self.opponent = opponent
        self.stake = stake
        self.guild_id = guild_id
        self.user_data = user_data
        self.result_sent = False
        self.message = None
        self.bot = bot

    async def on_timeout(self):
        if not self.result_sent and self.message:
            for child in self.children:
                child.disabled = True
            try:
                await self.message.edit(content="⏳ Время предложения истекло, отправьте новое предложение.", view=self)
            except Exception as e:
                print(f"Ошибка при on_timeout: {e}")
            self.stop()


    @button(label="Согласиться", style=ButtonStyle.green)
    async def confirm(self, button: button, inter: Interaction):

        if inter.author.id != self.opponent.id:
            await inter.response.send_message("Только оппонент может подтвердить ставку.", ephemeral=True)
            return
        
        cog = self.bot.get_cog("For_Users")
        if cog is None:
            await inter.response.send_message("Ошибка: ког Users не найден.", ephemeral=True)
            return

        lock1 = cog.get_user_lock(self.bettor.id)
        lock2 = cog.get_user_lock(self.opponent.id)

        first_lock, second_lock = (lock1, lock2) if self.bettor.id < self.opponent.id else (lock2, lock1)

        async with first_lock:
            async with second_lock:

                balance_1player = self.user_data[self.guild_id][str(self.bettor.id)]["balance"]
                balance_2player = self.user_data[self.guild_id][str(self.opponent.id)]["balance"]

                if balance_1player < self.stake or balance_2player < self.stake:
                    await inter.response.edit_message(content="❌ У кого-то из игроков недостаточно средств для ставки.", view=None)
                    self.result_sent = True
                    self.stop()
                    return

                self.user_data[self.guild_id][str(self.bettor.id)]["balance"] -= self.stake
                self.user_data[self.guild_id][str(self.opponent.id)]["balance"] -= self.stake

                roll1 = random.randint(1, 6)
                roll2 = random.randint(1, 6)

                if roll1 > roll2:
                    winner = str(self.bettor.id)
                    winner_mention = self.bettor.mention
                    winner_id = self.bettor.id
                    loser_mention = self.opponent.mention
                    loser_id = self.opponent.id
                elif roll2 > roll1:
                    winner = str(self.opponent.id)
                    winner_mention = self.opponent.mention
                    winner_id = self.opponent.id
                    loser_mention = self.bettor.mention
                    loser_id = self.bettor.id
                else:
                    winner = None

                random_color = disnake.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

                if winner:
                    self.user_data[self.guild_id][winner]["balance"] += self.stake * 2

                    embed = disnake.Embed(
                        title="🎲 Кости!",
                        description=(
                            f"🏆 В результате броска победителем становится {winner_mention} и ему начисляется {self.stake * 2} {config.NAME_CURRENCY}. Поздравляем!🎉"
                        ),
                        color=random_color,
                        timestamp=datetime.datetime.now()
                    )
                    logger.info(
                        f"Ставка: {self.stake} {config.NAME_CURRENCY}. "
                        f"Выиграл: {winner_mention}. "
                        f"Баланс {loser_mention}: {self.user_data[self.guild_id][str(loser_id)]['balance']} {config.NAME_CURRENCY}. "
                        f"Баланс {winner_mention}: {self.user_data[self.guild_id][str(winner_id)]['balance']} {config.NAME_CURRENCY}"
                    )
                else:
                    self.user_data[self.guild_id][str(self.bettor.id)]["balance"] += self.stake
                    self.user_data[self.guild_id][str(self.opponent.id)]["balance"] += self.stake
                    logger.info(f"В связи с ничьёй участникам были возвращены замороженные деньги: {self.bettor.mention} : {self.user_data[self.guild_id][self.bettor.id]["balance"]}, {self.opponent.mention} : {self.user_data[self.guild_id][self.opponent.id]["balance"]}")

                    embed = disnake.Embed(
                        title="🎲 Кости!",
                        description="В результате броска ничья! Все остались при своих.",
                        color=disnake.Color.light_gray(),
                        timestamp=datetime.datetime.now()
                    )

                embed.add_field(name="Счёт:", value=f"{self.bettor.mention} : {roll1}\n{self.opponent.mention} : {roll2}")
                embed.set_footer(text=f"{config.BOT_VERSION}")

                await async_save_user_data(self.user_data)

        await inter.response.edit_message(content=None, embed=embed, view=None)
        self.result_sent = True
        self.stop()

    @button(label="Отклонить", style=ButtonStyle.red)
    async def decline(self, button: button, inter: Interaction):
        if inter.author.id != self.opponent.id:
            await inter.response.send_message("Только оппонент может отклонить ставку.", ephemeral=True)
            return

        await inter.response.edit_message(content=f"❌ Ставка пользователя {self.bettor.mention} отклонена оппонентом {self.opponent.mention}.", view=None)
        self.result_sent = True
        self.stop()

class For_Users(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_data = {}
        self.user_locks = {}
        self.user_cooldowns = {}
        self.cleanup_cooldowns.start()
        self.data_lock = asyncio.Lock()

    def get_user_lock(self, user_id: int) -> asyncio.Lock:
        if user_id not in self.user_locks:
            self.user_locks[user_id] = asyncio.Lock()
        return self.user_locks[user_id]


    async def on_timeout(self):
        if not self.result_sent and self.message is not None:
            for child in self.children:
                child.disabled = True
            try:
                await self.message.edit(content="❌ Время подтверждения ставки истекло, предложение отменено.", view=self)
                self.result_sent = True
                self.stop()
            except Exception:
                pass
        
    async def give_bonus(self, guild_id, user_id):
        user_id = str(user_id)
        guild_id = str(guild_id)

        user_data = await async_load_user_data()

        if guild_id not in user_data:
            user_data[guild_id] = {}

        if user_id not in user_data[guild_id]:
            user_data[guild_id][user_id] = {'balance': 0, 'last_bonus': None}

        last_bonus = user_data[guild_id][user_id]['last_bonus']

        if isinstance(last_bonus, str):
            last_bonus = datetime.datetime.fromisoformat(last_bonus)

        if last_bonus is None or (datetime.datetime.now() - last_bonus).total_seconds() >= 86400:
            bonus_amount = random.randint(1, 20)
            user_data[guild_id][user_id]['balance'] += bonus_amount
            user_data[guild_id][user_id]['last_bonus'] = datetime.datetime.now()
            await async_save_user_data(user_data)

            logger.info(f"Пользователь с ID {user_id} получил бонус в размере {bonus_amount}")
            return True

        return False

    @tasks.loop(minutes=10)
    async def cleanup_cooldowns(self):
        now = datetime.datetime.utcnow()
        to_delete = [user_id for user_id, dt in self.user_cooldowns.items() if (now - dt).total_seconds() > 60]
        for user_id in to_delete:
            del self.user_cooldowns[user_id]


    @commands.command(name='bonus')
    async def bonus(self, ctx):
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        self.user_data = await async_load_user_data()

        if guild_id not in self.user_data:
            self.user_data[guild_id] = {}

        if user_id not in self.user_data[guild_id]:
            self.user_data[guild_id][user_id] = {'balance': 0, 'last_bonus': None}
            await async_save_user_data(self.user_data)

        got_bonus = await self.give_bonus(guild_id, user_id)

        if got_bonus:
            self.user_data = await async_load_user_data()
            balance = self.user_data[guild_id][user_id]["balance"]
            embed = disnake.Embed(
                title="🎉 Ты получил бонус!",
                description=f"Ты получил бонус и теперь у тебя {balance} {config.NAME_CURRENCY}!",
                color=disnake.Color.green(),
                timestamp=disnake.utils.utcnow(),
            )
            await ctx.send(embed=embed)
        else:
            sms = f"{ctx.author.mention}, с момента получения последнего бонуса ещё не прошло 24 часа."
            embed = disnake.Embed(
                description=sms,
                color=disnake.Color.orange(),
                timestamp=disnake.utils.utcnow(),
            )
            await ctx.send(embed=embed)


    @commands.slash_command(name="top", description=f"Показать топ пользователей по {config.NAME_CURRENCY}")
    async def top(self, ctx):
        guild_id = str(ctx.guild.id)

        global user_data
        user_data = await async_load_user_data()

        if guild_id not in user_data or not user_data[guild_id]:
            await ctx.send("На этом сервере нет данных пользователей.")
            return

        top_users = sorted(user_data[guild_id].items(), key=lambda x: x[1]['balance'], reverse=True)[:10]
        top_list = f"🏆 **Топ пользователей по {config.NAME_CURRENCY}:**\n\n"
        
        for i, (user_id, data) in enumerate(top_users):
            try:
                user = await self.bot.fetch_user(int(user_id))
                top_list += f"{i + 1}. {user.name} - {data['balance']} {config.NAME_CURRENCY}\n"
            except disnake.NotFound:
                top_list += f"{i + 1}. Пользователь <{user_id}> - {data['balance']} {config.NAME_CURRENCY}\n"

        random_color = disnake.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        embed = disnake.Embed(description=top_list, color=random_color)
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)

    
    @commands.slash_command(description="Брось кости и попытай удачу против других пользователей!")
    async def dice(self, inter: disnake.AppCmdInter, opponent: disnake.Member, stake: int = commands.Param(gt=0, description="Ставка должна быть больше 0")):
        now = datetime.datetime.utcnow()
        last_use = self.user_cooldowns.get(inter.author.id)
        if last_use and (now - last_use).total_seconds() < 60:
            await inter.response.send_message("❌ Пожалуйста, подождите минуту перед следующим использованием этой команды.", ephemeral=True)
            return
        self.user_cooldowns[inter.author.id] = now

        guild_id = str(inter.guild.id)
        player1_id = str(inter.author.id)
        player2_id = str(opponent.id)

        async with self.data_lock:
            self.user_data = await async_load_user_data()

            if guild_id not in self.user_data:
                self.user_data[guild_id] = {}

            for id_ in (player1_id, player2_id):
                if id_ not in self.user_data[guild_id]:
                    self.user_data[guild_id][id_] = {"balance": 0, "last_bonus": None}


            balance_1player = self.user_data[guild_id][player1_id]["balance"]
            balance_2player = self.user_data[guild_id][player2_id]["balance"]

            if balance_1player < stake:
                await inter.response.send_message(f"❌ У Вас недостаточно средств для ставки в размере {stake} {config.NAME_CURRENCY}", ephemeral=True)
                return
            if balance_2player < stake:
                await inter.response.send_message(f"❌ У оппонента {opponent.mention} недостаточно средств для ставки в размере {stake} {config.NAME_CURRENCY}", ephemeral=True)
                return

        view = DiceConfirmView(inter.author, opponent, stake, guild_id, user_data, self.bot, timeout=60)
        await inter.response.send_message(
            f"{opponent.mention}, пользователь {inter.author.mention} предлагает сыграть в кости со ставкой {stake} {config.NAME_CURRENCY}. Подтвердите или отклоните ставку.",
            view=view,
            ephemeral=False
            )
        view.message = await inter.original_message()


    @commands.slash_command(name="profile", description="Посмотреть свой профиль")
    async def stats(self, ctx: disnake.ApplicationCommandInteraction):
        status_map = {
        disnake.Status.online: "В сети",
        disnake.Status.idle: "Неактивен",
        disnake.Status.dnd: "Не беспокоить",
        disnake.Status.offline: "Не в сети"
    }
        status = ctx.author.desktop_status

        await ctx.response.defer()
        
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        user_data = await async_load_user_data()

        if guild_id not in user_data:
            user_data[guild_id] = {}

        if user_id not in user_data[guild_id]:
            user_data[guild_id][user_id] = {'balance': 0, 'last_bonus': None}
            await async_save_user_data(self.user_data)
        else:
            user_data[guild_id][user_id] = user_data[guild_id][user_id]

        random_color = disnake.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        created_at = ctx.author.created_at.strftime("%Y-%m-%d %H:%M")
        joined_at = ctx.author.joined_at.strftime("%Y-%m-%d %H:%M")
        
        embed = disnake.Embed(
            title="🗒️ Профиль пользователя",
            color=random_color,
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed.add_field(name="👤 Имя:", value=ctx.author.display_name, inline=False)
        embed.add_field(name="🆔 ID:", value=ctx.author.id, inline=False)
        embed.add_field(name="📅 Аккаунт создан:", value=created_at, inline=False)
        embed.add_field(name="🔗 Присоединился к серверу:", value=joined_at, inline=False)
        embed.add_field(name="🎖️ Роль:", value=ctx.author.top_role, inline=False)
        embed.add_field(name="🌟 Статус:", value=status_map.get(status, "Неизвестно"), inline=False)
        embed.add_field(name="💰 Баланс:", value=f"{user_data[guild_id][user_id]['balance']} {config.NAME_CURRENCY}", inline=False)

        embed.set_footer(text=config.BOT_VERSION)
        
        await ctx.edit_original_response(embed=embed)


    @commands.command(name="bal")
    async def bal(self, ctx):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        user_data = await async_load_user_data()

        if guild_id not in user_data:
            user_data[guild_id] = {}

        if user_id not in user_data[guild_id]:
            user_data[guild_id][user_id] = {'balance': 0, 'last_bonus': None}
            await async_save_user_data(self.user_data)
        else:
            user_data[guild_id][user_id] = user_data[guild_id][user_id]

        embed=disnake.Embed(
            title="Информация:",
            description=f"Твой баланс: {user_data[guild_id][user_id]['balance']} {config.NAME_CURRENCY}"
        )

        embed.set_footer(text=config.BOT_VERSION)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(For_Users(bot))