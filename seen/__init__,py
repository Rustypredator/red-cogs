from .seen import Seen

__red_end_user_data_statement__ = (
    "Stores Discord IDs and timestamps for activity tracking."
)

async def setup(bot):
    cog = Seen(bot)
    await cog.initialize()
    bot.add_cog(cog)