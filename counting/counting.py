import random
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
import discord

class Counting(commands.Cog):
    """Cog for a counting game with leaderboards, custom reactions, per-guild configuration, and optional shame role."""

    default_guild = {
        "current_number": 0,
        "channel_id": None,
        "leaderboard": {},
        "correct_emote": "✅",
        "wrong_emote": "❌",
        "shame_role": None,
        "last_counter_id": None,
        "fail_on_text": False,
        "ban_from_counting_after_fail": False,
        "participate_in_global_lb": False
    }

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=19516548596, force_registration=True)
        self.config.register_guild(**self.default_guild)

    @commands.command()
    async def countingset(self, ctx, setting, *parameters):
        """Aggregator Command for configuring all settings of the bot"""
        guild = ctx.guild
        
        ctx.send("setting " + str(setting) + " with params " + str(parameters))

    @commands.command()
    async def countingsetchannel(self, ctx, channel: discord.TextChannel = None):
        """Sets the channel for the counting game. If no channel is provided, a new one is created."""
        guild = ctx.guild

        if channel is None:
            channel = await guild.create_text_channel(name="counting-game")
            await ctx.send(f"Counting game channel created: {channel.mention}. Please set the shame role (optional) using `countingsetshamerole`.")
        else:
            await ctx.send(f"Counting game channel set to {channel.mention}. Please set the shame role (optional) using `countingsetshamerole`.")

        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await self.config.guild(ctx.guild).current_number.set(1)
        await self.config.guild(ctx.guild).leaderboard.set({})
        await self.config.guild(ctx.guild).last_counter_id.set(None)

    @commands.command()
    async def countingsetshamerole(self, ctx, shame_role: discord.Role):
        """Sets the shame role for incorrect counting (optional)."""
        await self.config.guild(ctx.guild).shame_role.set(shame_role.id)
        await ctx.send(f"Shame role for counting set to {shame_role.mention}")

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
                # get proposed next number:
                next_number = int(message.content)
                # get id of last user to count:
                last_counter_id = await self.config.guild(message.guild).last_counter_id()
                # get id of counting user:
                user_id = message.author.id
                # get correct next number:
                correct_number = guild_config["current_number"] +1
                # check if number is correct and if user did not count twice:
                if next_number == correct_number and user_id != last_counter_id:
                    # update config to reflect new number:
                    await self.config.guild(message.guild).current_number.set(next_number)
                    # update config to reflect current user as last counter:
                    await self.config.guild(message.guild).last_counter_id.set(user_id)
                    # add a reaction to the messag indicating it was recorded.
                    await message.add_reaction(guild_config["correct_emote"])

                    # get current leaderboard from config:
                    leaderboard = guild_config["leaderboard"]
                    # update users leaderboard entry:
                    leaderboard[str(user_id)] = leaderboard.get(str(user_id), 0) + 1
                    # Write new Leaderboard to config:
                    await self.config.guild(message.guild).leaderboard.set(leaderboard)
                else:
                    await message.add_reaction(guild_config["wrong_emote"])

                    if guild_config["shame_role"]:
                        shame_role = message.guild.get_role(guild_config["shame_role"])
                        await message.author.add_roles(shame_role, reason="Wrong count or double counting")
                        await message.channel.set_permissions(shame_role, send_messages=False)

                        display_name = message.author.display_name
                        roasts = [
                            f"{display_name} couldn't even count to {guild_config['current_number'] + 1}! Maybe try using your fingers next time?",
                            f"Looks like {display_name} skipped a few math classes... Back to square one!",
                            f"{display_name}, is that your final answer? Because it's definitely wrong!",
                            f"{display_name}'s counting skills are as impressive as their ability to divide by zero.",
                            f"{display_name}, are you sure you're not a calculator in disguise? Because your math is off!",
                        ]
                        roast = random.choice(roasts)
                        await message.channel.send(embed=discord.Embed(description=roast, color=discord.Color.red()))

                    await self.config.guild(message.guild).current_number.set(1)
                    await self.config.guild(message.guild).last_counter_id.set(None)

            except ValueError:
                pass  # Ignore non-numeric messagesuser_id = str(message.author.id)