import disnake
from disnake.ext import commands
import json
import os
import asyncio
import datetime
import config
import aiofiles
from config import DEVELOPER_ID

class Moderations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_levels = {}
        self.roles = {}
        
    async def cog_load(self):
        await self.load_levels()
        await self.load_roles()
    
    async def load_levels(self):
        try:
            async with aiofiles.open('data/user_levels.json', 'r', encoding='utf-8') as f:
                content = await f.read()
                self.user_levels = json.loads(content)
        except Exception:
            self.user_levels = {}

    def save_levels(self):
        with open(os.path.join(os.getcwd(), "data/user_levels.json"), "w", encoding="utf-8") as f:
            json.dump(self.user_levels, f, indent=4)
    
    async def load_roles(self):
        if os.path.exists("data/roles.json"):
            with open("data/roles.json", "r") as f:
                self.roles = json.load(f)
    
    async def save_roles(self):
        with open("data/roles.json", "w") as f:
            json.dump(self.roles, f, indent=4)


    @commands.command(name="setlvl")
    async def setlvl(self, ctx, member: disnake.Member, level: int):
        if ctx.author.id == DEVELOPER_ID:
            if 0 <= level <= 3:
                server_id = str(ctx.guild.id)
                user_id = str(member.id)
                
                if server_id not in self.user_levels:
                    self.user_levels[server_id] = {}

                self.user_levels[server_id][user_id] = level
                await ctx.send(f"Уровень доступа {member.mention} изменен на {level} на сервере {ctx.guild.name}")

                self.save_levels()
            else:
                await ctx.send("Неверный уровень доступа.")
        else:
            await ctx.send("У вас нет прав на выполнение этой команды.")


    @commands.command(name="removelvl")
    async def remove_lvl(self, ctx, member: disnake.Member):
        if ctx.author.id == 660378493393174530:
            server_id = str(ctx.guild.id)
            user_id = str(member.id)

            if user_id in self.user_levels[server_id]:
                del self.user_levels[server_id][user_id]

                if not self.user_levels[server_id]:
                    del self.user_levels[server_id]
                    await ctx.send(f"Уровень доступа пользователя {member.mention} удалён, и сервер {ctx.guild.name} также был убран из базы данных.")
                else:
                    await ctx.send(f"Уровень доступа пользователя {member.mention} удалён.")
                
                self.save_levels()
        
            else:
                await ctx.send(f"Участник {member.mention} не найден в базе данных.")


    @commands.slash_command(name="kick", description="Кикнуть пользователя")
    async def kick(self, ctx, member: disnake.Member, reason: str = None):
        server_id = str(ctx.guild.id)
        user_level = self.user_levels.get(server_id, {}).get(str(ctx.author.id), 0)
        member_level = self.user_levels.get(server_id, {}).get(str(member.id), 0)

        if member.id == ctx.author.id:
            embed = disnake.Embed(
                title="Ошибка!",
                description="Вы не можете выгнать себя.",
                color=disnake.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f"{config.BOT_VERSION}")
            return await ctx.send(embed=embed)
        
        if member_level > user_level:
            embed = disnake.Embed(
                title="Ошибка!",
                description="Вы не можете выгнать пользователя с более высоким уровнем доступа.",
                color=disnake.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f"{config.BOT_VERSION}")
            return await ctx.send(embed=embed)

        if user_level >= 1:
            if ctx.guild.me.guild_permissions.kick_members:
                await member.kick(reason=reason)
                
                emb = (f"**Был кикнут:** {member.mention}\n"
                       f"{'**Причина:** ' + reason if reason else '**Причина: Не указана**'}"
                       f"**Выдал наказание:** {ctx.author.display_name}")
                
                embed = disnake.Embed(
                    title="Информация о кике:",
                    description=emb,
                    color=disnake.Color.red(),
                    timestamp=datetime.datetime.now()
                    )
                embed.set_author(
                    name=config.BOT_NAME,
                    icon_url="https://i.imgur.com/kqi6GqA.png"
                )
                embed.set_thumbnail(url=member.display_avatar)
                
                embed.set_footer(text=f"{config.BOT_VERSION}")
                await ctx.send(embed=embed)
            else:
                embed = disnake.Embed(
                    title="Ошибка!",
                    description="У бота недостаточно прав для кика пользователей на сервере!",
                    color=disnake.Color.red(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"{config.BOT_VERSION}")
                await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(
                title="Ошибка!",
                description="У вас недостаточно прав на выполнение этой команды.",
                color=disnake.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f"{config.BOT_VERSION}")
            await ctx.send(embed=embed)


    @commands.command(name="role")
    @commands.is_owner()
    async def role(self, ctx, type_role: str, role_id: int):
        type_role = type_role.lower()
        server_id = str(ctx.guild.id)

        if server_id not in self.roles:
            self.roles[server_id] = {"muted_role_id": None, "vmuted_role_id": None}

        if type_role == "mute_role":
            self.roles[server_id]["muted_role_id"] = role_id
            await self.save_roles()

            embed = disnake.Embed(
                title="Успешно!",
                description=f"Роль 'Muted' была установлена на ID: {role_id} для сервера {ctx.guild.name}",
                color=disnake.Color.green()
            )
            embed.set_footer(text=f"{config.BOT_VERSION}")
        elif type_role == "vmute_role":
            self.roles[server_id]["vmuted_role_id"] = role_id
            await self.save_roles()

            embed = disnake.Embed(
                title="Успешно!",
                description=f"Роль 'V-Muted' была установлена на ID: {role_id} для сервера {ctx.guild.name}",
                color=disnake.Color.green()
            )
            embed.set_footer(text=f"{config.BOT_VERSION}")
        else:
            embed = disnake.Embed(
                title="Ошибка!",
                description=f"Типа {type_role} не существует.",
                color=disnake.Color.red()
            )

            embed.set_footer(text=f"{config.BOT_VERSION}")
        await ctx.send(embed=embed)

    @commands.slash_command(name="mute", description="Заглушить пользователя на указанный период времени")
    async def mute(self, ctx, member: disnake.Member, duration: str = commands.Param(gt=0, description="Введите продолжительность мута в формате: 10m (m/h/d"), reason: str = None, voice_only: bool = commands.Param(default=False, description="Если True — мут только в войс канале")):
        server_id = str(ctx.guild.id)
        user_level = self.user_levels.get(server_id, {}).get(str(ctx.author.id), 0)
        member_level = self.user_levels.get(server_id, {}).get(str(member.id), 0)

        duration_in_seconds = 0

        if member.id == ctx.author.id:
            embed = disnake.Embed(
                title="Ошибка!",
                description="Вы не можете замутить себя.",
                color=disnake.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f"{config.BOT_VERSION}")
            await ctx.send(embed=embed)

        if member_level > user_level:
            embed = disnake.Embed(
                title="Ошибка!",
                description="Вы не можете замутить пользователя с более высоким уровнем доступа.",
                color=disnake.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f"{config.BOT_VERSION}")
            await ctx.send(embed=embed)

        if user_level >= 1:
            if ctx.guild.me.guild_permissions.manage_roles:
                if duration[-1] in ['m', 'h', 'd']:
                    try:
                        time_val = int(duration[:-1])
                        if duration[-1] == 'm':
                            duration_in_seconds = time_val * 60
                        elif duration[-1] == 'h':
                            duration_in_seconds = time_val * 3600
                        elif duration[-1] == 'd':
                            duration_in_seconds = time_val * 86400

                        role_data = self.roles.get(server_id, {})
                        role_id = None
                        role_type = ""
                        if voice_only:
                            role_id = role_data.get("vmuted_role_id")
                            role_type = "voice-mute"
                        else:
                            role_id = role_data.get("muted_role_id")
                            role_type = "mute"

                        if role_id is None:
                            await ctx.send(f"Роль для {role_type} не настроена. Пожалуйста, свяжитесь с администратором.")
                            return

                        muted_role = ctx.guild.get_role(role_id)

                        if muted_role:
                            await member.add_roles(muted_role)
                            emb = (f"**Был замучен:** {member.mention}\n"
                                   f"**Срок мута:** {duration}\n"
                                   f"**Тип мута:** {role_type}\n"
                                   f"{'**Причина:** ' + reason if reason else '**Причина: Не указана**'}\n"
                                   f"**Выдал наказание:** {ctx.author.mention}")
                            embed=disnake.Embed(
                                title="Информация о муте:",
                                description=emb,
                                color=disnake.Color.red(),
                                timestamp=datetime.datetime.now()
                            )
                            embed.set_author(
                                name=config.BOT_NAME,
                                icon_url="https://i.imgur.com/kqi6GqA.png"
                            )
                            embed.set_thumbnail(url=member.display_avatar)
                            embed.set_footer(text=f"{config.BOT_VERSION}")
                            await ctx.send(embed=embed)
                            await asyncio.sleep(duration_in_seconds)
                            await member.remove_roles(muted_role)
                        else:
                            embed=disnake.Embed(
                                title="Ошибка!",
                                description="Роль 'Muted' не найдена или не настроена. Обратитесь к разработчику для решения данной проблемы",
                                color=disnake.Color.red(),
                                timestamp=datetime.datetime.now()
                            )
                            embed.set_footer(text=f"{config.BOT_VERSION}")
                            await ctx.send(embed=embed)
                    
                    except ValueError:
                        embed=disnake.Embed(
                            title="Ошибка!",
                            description="Ошибка формата времени!",
                            color=disnake.Color.red(),
                            timestamp=datetime.datetime.now()
                        )
                        embed.set_footer(text=f"{config.BOT_VERSION}")
                        await ctx.send(embed=embed)
                else:
                    embed=disnake.Embed(
                        title="Ошибка!",
                        description="Неверный формат времени. Используйте 'm', 'h' или 'd' для указания минут, часов или дней.",
                        color=disnake.Color.red(),
                        timestamp=datetime.datetime.now()
                    )
                    embed.set_footer(text=f"{config.BOT_VERSION}")
                    await ctx.send(embed=embed)
            else:
                embed=disnake.Embed(
                    title="Ошибка!",
                    description=f"У бота недостатачно прав для управления ролями на сервере!",
                    color=disnake.Color.red(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"{config.BOT_VERSION}")
                await ctx.send(embed=embed)
        else:
            embed=disnake.Embed(
                title="Ошибка!",
                description=f"У Вас недостатачно прав для использования этой команды",
                color=disnake.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f"{config.BOT_VERSION}")
            await ctx.send(embed=embed)

    @commands.slash_command(name="unmute", description="Убрать заглушку с пользователя")
    async def unmute(self, ctx, member: disnake.Member):
        server_id = str(ctx.guild.id)
        muted_role_id = self.roles.get(server_id, {}).get("muted_role_id")

        if muted_role_id is None:
            return await ctx.response.send_message("Роль 'Muted' не настроена. Пожалуйста, свяжитесь с администратором.")

        muted_role = ctx.guild.get_role(muted_role_id)
        user_level = self.user_levels.get(server_id, {}).get(str(ctx.author.id), 0)

        if muted_role:
            if ctx.guild.me.guild_permissions.manage_roles:
                if user_level >= 1:
                    if ctx.author.guild_permissions.manage_roles:
                        if muted_role in member.roles:
                            await member.remove_roles(muted_role)
                            embed = disnake.Embed(
                                title="Успешно!",
                                description=f"Пользователь {member.mention} был размучен!\nИнициатор: {ctx.author.mention}",
                                color=disnake.Color.green(),
                                timestamp=datetime.datetime.now()
                            )
                            embed.set_footer(text=f"{config.BOT_VERSION}")
                            await ctx.send(embed=embed)
                        else:
                            embed = disnake.Embed(
                                title="Ошибка!",
                                description=f"У пользователя {member.mention} **отсутствует** мут!",
                                color=disnake.Color.red(),
                                timestamp=datetime.datetime.now()
                            )
                            embed.set_footer(text=f"{config.BOT_VERSION}")
                            await ctx.send(embed=embed)
                    else:
                        embed = disnake.Embed(
                            title="Ошибка!",
                            description="У Вас нет прав на управление ролями на сервере.",
                            color=disnake.Color.red(),
                            timestamp=datetime.datetime.now()
                        )
                        embed.set_footer(text=f"{config.BOT_VERSION}")
                        await ctx.send(embed=embed)
                else:
                    embed = disnake.Embed(
                        title="Ошибка!",
                        description="У Вас недостаточно прав для использования этой команды.",
                        color=disnake.Color.red(),
                        timestamp=datetime.datetime.now()
                    )
                    embed.set_footer(text=f"{config.BOT_VERSION}")
                    await ctx.send(embed=embed)
            else:
                embed = disnake.Embed(
                    title="Ошибка!",
                    description="У бота недостаточно прав для управления ролями на сервере!",
                    color=disnake.Color.red(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"{config.BOT_VERSION}")
                await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(
                title="Ошибка!",
                description="Роль 'Muted' не найдена или не настроена. Обратитесь к разработчику для решения данной проблемы.",
                color=disnake.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f"{config.BOT_VERSION}")
            await ctx.send(embed=embed)

    @commands.slash_command(name="ban", description="Забанить пользователя на определённое количество дней")
    async def ban(self, ctx, member: disnake.Member, days: int, reason: str = None):
        server_id = str(ctx.guild.id)
        user_level = self.user_levels.get(server_id, {}).get(str(ctx.author.id), 0)
        member_level = self.user_levels.get(server_id, {}).get(str(member.id), 0)

        if member.id == ctx.author.id:
            embed = disnake.Embed(
                title="Ошибка!",
                description="Ты не можешь забанить самого себя.",
                color=disnake.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f"{config.BOT_VERSION}")
            return await ctx.send(embed=embed)
        
        if member_level > user_level:
            embed = disnake.Embed(
                title="Ошибка!",
                description="Ты не можешь забанить пользователя с более высоким уровнем доступа.",
                color=disnake.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f"{config.BOT_VERSION}")
            return await ctx.send(embed=embed)

        if user_level >= 2:
            if ctx.guild.me.guild_permissions.ban_members:
                await member.ban(reason=reason)
                sms = (f"**Был забанен:** {member.mention}\n"
                       f"**Срок бана:** {days} дней\n"
                       f"{'**Причина:** ' + reason if reason else '**Причина: Не указана**'}\n"
                       f"**Выдал наказание:** {ctx.author.mention}"
                       )
                embed = disnake.Embed(
                    title="Информация о бане:",
                    description=sms,
                    color=disnake.Color.red(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_author(
                    name=config.BOT_NAME,
                    icon_url="https://i.imgur.com/kqi6GqA.png"
                    )
                embed.set_thumbnail(url=member.display_avatar)
                embed.set_footer(text=f"{config.BOT_VERSION}")
                await ctx.send(embed=embed)
            
                if days > 0:
                    await asyncio.sleep(days * 86400)
                    await ctx.guild.unban(member)
            else:
                embed = disnake.Embed(
                    title="Ошибка!",
                    description="У бота недостаточно прав для бана пользователей на сервере!",
                    color=disnake.Color.red(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"{config.BOT_VERSION}")
                await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(
                title="Ошибка!",
                description="У вас недостаточно прав на выполнение этой команды.",
                color=disnake.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f"{config.BOT_VERSION}")
            await ctx.send(embed=embed)

    @commands.slash_command(name="unban", description="Разбанить пользователя")
    async def unban(self, ctx, user_id: str):
        server_id = str(ctx.guild.id)
        user_level = self.user_levels.get(server_id, {}).get(str(ctx.author.id), 0)

        if user_level >= 2:
            if ctx.guild.me.guild_permissions.ban_members:
                try:
                    await ctx.guild.unban(disnake.Object(id=user_id))
                    embed = disnake.Embed(
                        title="Успешно!",
                        description=f"Пользователь <@{user_id}> был разбанен!\n**Снял блокировку:** {ctx.author.mention}",
                        color=disnake.Color.green(),
                        timestamp=datetime.datetime.now()
                    )
                except disnake.NotFound:
                    embed = disnake.Embed(
                        title="Ошибка!",
                        description="Пользователь с указанным ID не найден или не забанен.",
                        color=disnake.Color.red(),
                        timestamp=datetime.datetime.now()
                    )
                except disnake.Forbidden:
                    embed = disnake.Embed(
                        title="Ошибка!",
                        description="У бота недостаточно прав для снятия блокировок пользователей на сервере!",
                        color=disnake.Color.red(),
                        timestamp=datetime.datetime.now()
                    )
            else:
                embed = disnake.Embed(
                    title="Ошибка!",
                    description="У бота недостаточно прав для снятия блокировок пользователей на сервере!",
                    color=disnake.Color.red(),
                    timestamp=datetime.datetime.now()
                )
        else:
            embed = disnake.Embed(
                title="Ошибка!",
                description="У вас недостаточно прав на выполнение этой команды.",
                color=disnake.Color.red(),
                timestamp=datetime.datetime.now()
            )
        embed.set_footer(text=f"{config.BOT_VERSION}")
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Moderations(bot))