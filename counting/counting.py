import random
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
import discord

class Counting(commands.Cog):
    """Cog for a counting game with leaderboards, custom reactions, per-guild configuration, and optional shame role."""

    lang = {
        "en": {
            "general": {
                "countingTwiceMsg1": "You tried to count twice in a row."
            }
        },
        "de": {
            "general": {
                "countingTwiceMsg1": "Du hast versucht zwei mal zu zählen."
            }
        }
    }

    default_guild = {
        "current_number": 0,
        "channel_id": None,
        "leaderboard": {},
        "shame_role": None,
        "last_counter_id": None,
        "fail_on_text": False,
        "ban_from_counting_after_fail": False,
        "participate_in_global_lb": False,
        "allow_consecutive_counting": False
    }

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=19516548596, force_registration=True)
        self.config.register_guild(**self.default_guild)

    @staticmethod
    def strToBool(convertme):
        # check if str is actually a string:
        if not isinstance(convertme, str):
            # check if it is a bool:
            if isinstance(convertme, bool):
                # if it is a bool, return it
                return convertme
            if isinstance(convertme, int):
                # if it is a int, return it
                if convertme > 0:
                    return True
                else:
                    return False
            else:
                # if it is neither, return False
                return False
        trueKeywords = ['true', '1', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']
        return convertme.lower() in trueKeywords
    
    @staticmethod
    def isNumber(str):
        try:
            float(str)
        except ValueError:
            return False
        return True

    async def failed(why, message, guildConfig, lang, banFromCountingAfterFail):
        # Why Array:
        # 1: Text in COunting Channel
        # 2: Consecutive Counting
        # 3: Wrong Number

        # wether or not the counter needs to be reset...
        reset = False

        # mark message as wrong
        await message.add_reaction("❌")

        display_name = message.author.display_name
        correct_number = guildConfig["current_number"] + 1

        roasts = {
            "en": [
                f"{display_name} could'nt even count to {correct_number}! Maybe try using your fingers next time?",
                f"Looks like {display_name} skipped a few math classes... Back to square one!",
                f"{display_name}, is that your final answer? Because it's definitely wrong!",
                f"{display_name}'s counting skills are as impressive as their ability to divide by zero.",
                f"{display_name}, are you sure you're not a calculator in disguise? Because your math is off!"
            ],
            "de": [
                f"{display_name}, Du bist der Grund, warum Taschenrechner erfunden wurden.",
            ]
        }
        
        title = ":bell: :bell: Shame!, Shame! :bell: :bell:"
        color = discord.Color.red()
        failmsg = "bleh"
        
        match why:
            case 1:
                failmsg = "Text is not allowed here."
            case 2:
                failmsg = "You cant count twice!"
            case 3:
                channel = message.channel
                # roast them!
                roast = random.choice(roasts[lang])
                await channel.send(embed=discord.Embed(description=roast, color=discord.Color.red()))
        
        # send message
        await message.channel.send(embed=discord.Embed(title=title, description=failmsg, color=color))
        
        # do logic to the user who failed! apply role etc.
        if guildConfig["shame_role"]:
            shame_role = message.guild.get_role(guildConfig["shame_role"])
            await message.author.add_roles(shame_role, reason="Wrong count or double counting")
        if banFromCountingAfterFail:
            await message.channel.set_permissions(shame_role, send_messages=False)
        return reset

    @commands.guild_only()
    @commands.command()
    async def countingset(self, ctx, setting = None, *parameters):
        """Aggregator Command for configuring all settings of the bot"""
        guild = ctx.guild
        guildcfg = self.config.guild(guild).all()
        
        match setting:
            case 'channel':
                title = "Setting: Channel"
                
                if len(parameters) > 0:
                    try:
                        channel = await commands.TextChannelConverter().convert(ctx, parameters[0])
                    except discord.ext.commands.errors.ChannelNotFound:
                        await ctx.send("Mentioned channel was not found.")
                        return
                else:
                    channel = ctx.channel
                    await ctx.send("No Channel defined, using the channel the command was sent from.")
                # TODO: check if channel exists
                # Set the Channel:
                await self.config.guild(guild).channel_id.set(channel.id)
                
                # Prepare message
                msg = "Counting Channel set to: " + str(channel.mention)
                color = discord.Color.green()
            case 'shamerole':
                title = "Setting: Shamerole"
                unset = False
                
                if len(parameters) > 0:
                    role = await commands.RoleConverter().convert(ctx, parameters[0])
                    await self.config.guild(guild).shame_role.set(role.id)
                else:
                    unset = True
                    await self.config.guild(guild).shame_role.set(None)
                    await ctx.send("No Role defined. Removing Shame Role.")
                
                
                # Prepare Message
                if unset:
                    msg = "Shamerole was removed."
                else:
                    msg = "Shamerole was set to " + (role.mention )
                color = discord.Color.green()
            case 'fail_on_text':
                title = "Setting Rule: Fail on Text"
                
                failOnText = False
                
                if len(parameters) > 0:
                    failOnText = self.strToBool(parameters[0])
                
                await self.config.guild(guild).fail_on_text.set(failOnText)
                
                msg = "Setting fail_on_text to: " + str(failOnText)
                color = discord.Color.green()
            case 'ban_from_counting_after_fail':
                title = "Setting Rule: Ban from counting after fail"
                
                banFromCountingAfterFail = False
                
                if len(parameters) > 0:
                    banFromCountingAfterFail = self.strToBool(parameters[0])
                
                await self.config.guild(guild).ban_from_counting_after_fail.set(banFromCountingAfterFail)
                                    
                msg = "Setting ban_from_counting_after_fail to: " + str(banFromCountingAfterFail)
                color = discord.Color.green()
            case 'allow_consecutive_counting':
                title = "Setting Rule: Ban from counting after fail"
                
                allowConsecutiveCounting = False
                
                if len(parameters) > 0:
                    allowConsecutiveCounting = self.strToBool(parameters[0])
                
                await self.config.guild(guild).allow_consecutive_counting.set(allowConsecutiveCounting)
                                    
                msg = "Setting allow_consecutive_counting to: " + str(allowConsecutiveCounting)
                color = discord.Color.green()
            case 'participate_in_global_lb':
                title = "Setting Rule: Ban from counting after fail"
                
                participateInGlobalLb = False
                
                if len(parameters) > 0:
                    participateInGlobalLb = self.strToBool(parameters[0])
                
                await self.config.guild(guild).participate_in_global_lb.set(participateInGlobalLb)
                                    
                msg = "Setting participate_in_global_lb to: " + str(participateInGlobalLb)
                color = discord.Color.green()
            case _:
                title = "No Setting or unknown Provided."
                msg = "Usage:\n```[p]countingset [setting] <parameters>```\n\nYou have the following Options (Current Values displayed after the name):\n"
                # add options and their values:
                channel = await self.config.guild(guild).channel_id()
                #channel = await commands.TextChannelConverter().convert(ctx, channelId)
                msg += "- channel (" + str(channel) + ")\n"
                role = await self.config.guild(guild).shame_role()
                #role = await commands.RoleConverter().convert(ctx, roleId)
                msg += "- shamerole (" + str(role) + ")\n"
                msg += "- fail_on_text (" + str(await self.config.guild(guild).fail_on_text()) + ")\n"
                msg += "- ban_from_counting_after_fail (" + str(await self.config.guild(guild).ban_from_counting_after_fail()) + ")\n"
                msg += "- allow_consecutive_counting (" + str(await self.config.guild(guild).allow_consecutive_counting()) + ")\n"
                msg += "- participate_in_global_lb (" + str(await self.config.guild(guild).participate_in_global_lb()) + ")"
                color = discord.Color.red()
                    
        await ctx.channel.send(embed=discord.Embed(title=title, description=msg, color=color))

    @commands.command()
    async def currentnumber(self, ctx):
        """Displays the current number in the counting game."""
        current_number = await self.config.guild(ctx.guild).current_number()
        await ctx.send(f"The current number is: {current_number}")

    @commands.command(aliases=["countingboard", "countingleaderboard"])
    async def countinglb(self, ctx):
        """Displays the leaderboard in an embed."""
        leaderboard = await self.config.guild(ctx.guild).leaderboard()
        if leaderboard:
            sorted_leaderboard = sorted(leaderboard.items(), key=lambda item: item[1], reverse=True)
            embed = discord.Embed(title="Counting Game Leaderboard", color=discord.Color.blue())
            for user_id, score in sorted_leaderboard[:10]:  # Show top 10
                user = self.bot.get_user(int(user_id))
                embed.add_field(name=user.name, value=score, inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("The leaderboard is empty.")
            
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handles messages in the counting game channel."""
        if message.author.bot:
            return

        guild_config = await self.config.guild(message.guild).all()
        
        if guild_config["channel_id"] == message.channel.id:
            try:
                # get settings:
                failOnText = self.strToBool(guild_config['fail_on_text'])
                banFromCountingAfterFail = self.strToBool(guild_config['ban_from_counting_after_fail'])
                allowConsecutiveCounting = self.strToBool(guild_config['allow_consecutive_counting'])
                #participateInGlobalLb = self.strToBool(guild_config['participate_in_global_lb'])
                
                # get current Stats
                last_number = int(guild_config['current_number'])
                correct_number = last_number + 1
                last_counter_id = guild_config['last_counter_id']
                
                # get vars for message:
                next_number = int(message.content)
                user_id = message.author.id
                
                # if fail on text is on, check it first!
                if failOnText:
                    if not self.isNumber(message.content):
                        reset = await self.failed(1, message, banFromCountingAfterFail)
                        if reset:
                            # reset counter
                            await self.config.guild(message.guild).current_number.set(1)
                            await self.config.guild(message.guild).last_counter_id.set(None)
                        return
                
                # if consecutive counting is forbidden, check this:
                if not allowConsecutiveCounting:
                    if user_id == last_counter_id:
                        reset = await self.failed(2, message, banFromCountingAfterFail)
                        if reset:
                            # reset counter
                            await self.config.guild(message.guild).current_number.set(1)
                            await self.config.guild(message.guild).last_counter_id.set(None)
                        return
                    
                # check if number is correct:
                if next_number != correct_number:
                    reset = await self.failed(3, message, banFromCountingAfterFail)
                    if reset:
                        # reset counter
                        await self.config.guild(message.guild).current_number.set(1)
                        await self.config.guild(message.guild).last_counter_id.set(None)
                    return
                    
                # update config to reflect new number:
                await self.config.guild(message.guild).current_number.set(next_number)
                # update config to reflect current user as last counter:
                await self.config.guild(message.guild).last_counter_id.set(user_id)
                # get current leaderboard from config:
                try:
                    leaderboard = guild_config["leaderboard"]
                except:
                    leaderboard = self.default_guild["leaderboard"]
                # get users leaderboard entry:
                try:
                    llbe = leaderboard.get(str(user_id))
                    # TODO: Global Leader Board
                except:
                    llbe = {
                        'count': 0,
                        'failcount': 0,
                        'pb': 0,
                        'warnings': {},
                        'fails': {}
                    }
                llbe['count'] = llbe['count'] + 1
                leaderboard[str(user_id)] = llbe
                # Write new Leaderboard to config:
                await self.config.guild(message.guild).leaderboard.set(leaderboard)
                
                # add a reaction to the messag indicating it was recorded.
                await message.add_reaction("✅")
            except ValueError:
                pass  # Ignore non-numeric messagesuser_id = str(message.author.id)