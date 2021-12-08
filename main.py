import discord, asyncio, json, jishaku
import dataframe_image as dfi
import pandas as pd
from discord.ext import commands, tasks
from rich.theme import Theme
from rich import print
from sqlitedict import SqliteDict

theme = Theme({"info": "cyan", "warning": "yellow", "error": "red", "success": "green"})
with open("config.json") as f:
    config = json.load(f)
token = config["token"]
roleId = config["roleId"]
staffRoleId = config["staffRoleId"]
log = config["log"]
bot = commands.Bot(command_prefix=config["prefix"], intents=discord.Intents.all())
bot.load_extension("jishaku")
if log:
    from rich.console import Console

    console = Console(theme=theme)
    print("[green]logging is enabled[/]")
else:

    class console:
        def __init__(self, *args, **kwargs):
            pass

        def log(self, *args, **kwargs):
            pass

    console = console()
    print("[red]LOGGING IS DISABLED[/]")


class invite:
    """Database Class"""

    def __init__(self, cheese):
        """Initialize the database"""
        self.db = SqliteDict(cheese, autocommit=True)

    def set(self, key, value):
        """Set a key to a value"""
        try:
            self.db[key] = value
            return True
        except:
            return False

    def get(self, key):
        """Get a value from a key"""
        try:
            return self.db[key]
        except:
            return False

    def dump(self):
        """Returns the entire database's value."""
        return dict(self.db.items())

    def delete(self, key):
        """Deletes a key from the database"""
        try:
            self.db.pop(key, None)
            return True
        except:
            return False


inviteDict = invite("inviteDict.db")
userDict = invite("userDict.db")


async def updateInvites(guild):
    """Updates the database with new information about all invites."""
    invites = await guild.invites()
    for invite in invites:
        inviteDict.set(
            invite.code,
            {
                "uses": invite.uses,
                "inviter": invite.inviter.id,
                "channel": invite.channel.id,
            },
        )
        if userDict.get(str(invite.inviter.id)):
            continue
        userDict.set(
            str(invite.inviter.id),
            {
                "invitedBy": None,
                "invited": {"invited": set(), "verifiedInvites": set()},
            },
        )


@bot.event
async def on_ready():
    """Tells you when the bot has successfully connected to Discord."""
    print(
        f'Logged in as [green]{bot.user.name}[/] ({bot.user.id}) and in {len(bot.guilds)} {"servers" if len(bot.guilds) > 1 else "server"}.'
    )
    console.log(
        f"Connected to Discord Gateway. Dpy version {discord.__version__}, servers - {', '.join([str(guild.name) for guild in bot.guilds])}."
    )
    await updateInvites(bot.guilds[0])
    print("------")


@bot.event
async def on_invite_create(invite):
    """Updates the invites database when a user creates an invite."""
    await updateInvites(invite.guild)


@bot.event
async def on_member_join(member):
    """Updates invites when a member joins"""
    invites = await member.guild.invites()
    for invite in invites:
        if invite.uses > inviteDict.get(invite.code)["uses"]:
            console.log(
                f'[green]{member.name}[/] has joined the server with an invite that has been used {invite.uses - inviteDict.get(invite.code)["uses"]} times. And was invited by {invite.inviter.name}.'
            )
            userDict.set(
                str(member.id),
                {
                    "invitedBy": invite.inviter.id,
                    "invited": {"invited": set(), "verifiedInvites": set()},
                },
            )
            bruh = userDict.get(str(invite.inviter.id))
            bruh["invited"]["invited"].update([member.id])
            userDict.set(str(invite.inviter.id), bruh)
            console.log(bruh)
            console.log(
                f"[green]{member.name}[/] has been added to the list of users who invited {invite.inviter.name}. {userDict.get(str(invite.inviter.id))}"
            )
            break
    await updateInvites(member.guild)


@bot.event
async def on_member_remove(member):
    """Removes a database/verified entry when a user is kicked, or leaves the server."""
    try:
        bruh = userDict.get(str(member.id))
        inviter = userDict.get(str(bruh["invitedBy"]))
        inviter["invited"]["invited"].discard(member.id)
        inviter["invited"]["verifiedInvites"].discard(member.id)
        userDict.set(str(bruh["invitedBy"]), inviter)
        userDict.delete(str(member.id))
    except TypeError:
        pass


@bot.event
async def on_member_update(before, after):
    """Checks if a member's roles have been updated and updates the database accordingly."""
    arid = [r.id for r in after.roles]
    brid = [r.id for r in before.roles]
    if before.roles != after.roles:
        if roleId in arid:
            if roleId in brid:
                # If the role we're interested is unchanged.
                return
            # If the role was added
            invitedBy = userDict.get(str(before.id))["invitedBy"]
            toModify = userDict.get(str(invitedBy))
            toModify["invited"]["verifiedInvites"].update([after.id])
            console.log(
                f'[green]{after.name}[/] has been verified - {userDict.get(str(after.id))["invitedBy"]}.'
            )
            userDict.set(str(invitedBy), toModify)
            return
        if roleId in brid:
            if roleId in arid:
                # If the role we're interested is unchanged.
                return
            # If the role was removed
            invitedBy = userDict.get(str(before.id))["invitedBy"]
            toModify = userDict.get(str(invitedBy))
            toModify["invited"]["verifiedInvites"].discard(before.id)
            userDict.set(str(invitedBy), toModify)
            console.log(
                f'[green]{before.name}[/] has been unverified - {userDict.get(str(before.id))["invitedBy"]}.'
            )
            return


@tasks.loop(seconds=60)
async def dump():
    """Dumps all data to the database, essentially committing it."""
    console.log("Dumping...")
    console.log(inviteDict.dump())
    console.log(userDict.dump())
    console.log("------")


dump.start()


@bot.command(help="Shows you the top 10 users with the highest verified invites.")
async def leaderboard(ctx, role: discord.Role = None):
    """Shows you the top 10 users with the highest verified invites."""
    if role is None:
        users = userDict.dump()
        users = [(k, v["invited"]["verifiedInvites"]) for k, v in users.items()]
        console.log(users)
        users = sorted(users, key=lambda x: len(x[1]), reverse=True)
        console.log(users)
        users = users[:10]
        safe = {bot.get_user(int(k)).name: len(v) for k, v in users}
        df = {"name": list(safe.keys()), "invites": list(safe.values())}
        df = pd.DataFrame(df)
        dfi.export(df, "leaderboard.png", table_conversion="matplotlib")
        file = discord.File("leaderboard.png", filename="leaderboard.png")
        nusers = [
            f"{i+1}. {bot.get_user(int(users[i][0])).name} - {len(users[i][1])} verified invite(s)"
            for i in range(len(users))
        ]
        await ctx.send("\n".join(nusers), file=file)
        return
    members = role.members
    users = [
        user["invitedBy"]
        for user in [
            userDict.get(str(m.id))
            for m in members
            if type(userDict.get(str(m.id))) is not bool
            and dict(userDict.get(str(m.id))).get("invitedBy") is not None
        ]
    ]
    users = {bot.get_user(int(l)): users.count(l) for l in set(users)}
    safe = {"name": list(users.keys()), "invites": list(users.values())}
    dfi.export(
        pd.DataFrame(safe),
        "leaderboard.png",
        table_conversion="matplotlib",
    )
    file = discord.File("leaderboard.png", filename="leaderboard.png")
    nusers = [
        f"{i+1}. {list(users.keys())[i].name} - {list(users.values())[i]} verified invite(s)"
        for i in range(len(users))
    ]
    await ctx.send("\n".join(nusers), file=file)


bot.remove_command("help")


@bot.command(help="This message")
async def help(ctx):
    """Help command"""
    helpEmbed = discord.Embed(
        title="Help", description="Prefix - !/mentions", color=0x00FF00
    )
    helpEmbed.add_field(
        name="!leaderboard [role]",
        value="Shows you the top 10 users with the highest verified invites.",
        inline=False,
    )
    helpEmbed.add_field(
        name="!stats/profile/me/invites [user, default - author]",
        value="Gives you the invite stats for the user.",
        inline=False,
    )
    helpEmbed.add_field(
        name="!about",
        value="The bot's settings, and other information about it.",
        inline=False,
    )
    helpEmbed.add_field(name="!help", value="This command.", inline=False)
    await ctx.send(embed=helpEmbed)


@bot.command(
    help="Gives you the invite stats for the user.", aliases=["stats", "profile", "me"]
)
async def invites(ctx, user: discord.Member = None):
    """Gives you the invite stats for the user."""
    if user is None:
        user = ctx.author
    try:
        userd = userDict.get(str(user.id))
    except TypeError:
        await ctx.send("That user isn't being tracked yet.")
        return
    inviter = "Unknown"
    try:
        inviter = bot.get_user(int(str(userd["invitedBy"]))).mention
    except ValueError:
        pass
    except TypeError:
        pass
    userEmbed = discord.Embed(
        title=bot.get_user(user.id).name,
        description=f"Invited by {inviter}.\nInvites - {len(dict(userd)['invited']['invited'])} ({', '.join([bot.get_user(username).name for username in userd['invited']['invited']])})\nVerified Invites - {len(dict(userd)['invited']['verifiedInvites'])} ({', '.join([bot.get_user(username).name for username in userd['invited']['verifiedInvites']])})",
        color=0x00FF00,
    )
    await ctx.send(embed=userEmbed)


@bot.command(help="About the bot")
async def about(ctx):
    """About the bot"""
    aboutEmbed = discord.Embed(
        title="About", description="Prefix - !/mentions", color=0x00FF00
    )
    aboutEmbed.add_field(
        name="Invite Tracker",
        value="A bot that tracks invites and checks if they're verified.",
        inline=False,
    )
    aboutEmbed.add_field(name="Author", value="TheOnlyWayUp#1231", inline=False)
    aboutEmbed.add_field(name="Version", value="0.0.1", inline=False)
    aboutEmbed.add_field(
        name="GitHub",
        value="https://github.com/TheOnlyWayUp/roleInviteBot",
        inline=False,
    )
    aboutEmbed.add_field(
        name="Staff Role", value=ctx.guild.get_role(staffRoleId).mention, inline=False
    )
    await ctx.send(embed=aboutEmbed)



bot.run(token)
