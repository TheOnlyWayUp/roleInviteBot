import discord, pickledb, asyncio
import dataframe_image as dfi
from discord.ext import commands, tasks
from rich.console import Console
from rich.theme import Theme
from rich import print
import pandas as pd
inviteDict = pickledb.load('inviteDb.db', False)
theme = Theme({"info":"cyan", "warning":"yellow", "error":"red", "success":"green"})
console = Console(theme=theme)
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
roleId = 884480740421672991
class invite():
    def __init__(self):
        self.db = {}
    def set(self, key, value):
        try:
            self.db[key] = value
            return True
        except:
            return False
    def get(self, key):
        try:
            return self.db[key]
        except:
            return False
    def dump(self):
        return self.db
    def delete(self, key):
        try:
            self.db.pop(key, None)
            return True
        except:
            return False

inviteDict = invite()
userDict = invite()
async def updateInvites(guild):
    """Updates the database with new information about all invites.
    """
    invites = await guild.invites()
    for invite in invites:
        inviteDict.set(invite.code, {"uses":invite.uses, "inviter":invite.inviter.id, "channel":invite.channel.id, })
        if userDict.get(str(invite.inviter.id)):
            continue
        userDict.set(str(invite.inviter.id), {"invitedBy":None, "invited":{"invited":set(), "verifiedInvites":set()}})
        

@bot.event
async def on_ready():
    """Tells you when the bot has successfully connected to Discord.
    """    
    console.print(f'Logged in as [green]{bot.user.name}[/] ({bot.user.id}) and in {len(bot.guilds)} {"servers" if len(bot.guilds) > 1 else "server"}.')
    console.log(f"Connected to Discord Gateway. Dpy version {discord.__version__}, servers - {', '.join([str(guild.name) for guild in bot.guilds])}.")
    await updateInvites(bot.guilds[0])
    print('------')


@bot.event
async def on_invite_create(invite):
    """Updates the invites database when a user creates an invite.
    """
    await updateInvites(invite.guild)

@bot.event
async def on_member_join(member):
    """Updates invites when a member joins
    """
    invites = await member.guild.invites()
    for invite in invites:
        if invite.uses > inviteDict.get(invite.code)["uses"]:
            console.log(f'[green]{member.name}[/] has joined the server with an invite that has been used {invite.uses - inviteDict.get(invite.code)["uses"]} times. And was invited by {invite.inviter.name}.')
            userDict.set(str(member.id), {"invitedBy":invite.inviter.id, "invited":{"invited":set(), "verifiedInvites":set()}})
            bruh = userDict.get(str(invite.inviter.id))
            bruh["invited"]['invited'].update([member.id])
            e = userDict.set(str(invite.inviter.id), bruh)
            print(e)
            console.log(bruh)
            #console.log("Trying to set invites")
            console.log(f'[green]{member.name}[/] has been added to the list of users who invited {invite.inviter.name}. {userDict.get(str(invite.inviter.id))}')
            break
    await updateInvites(member.guild)

@bot.event
async def on_member_remove(member):
    """Removes a database/verified entry when a user is kicked, or leaves the server.
    """
    bruh = userDict.get(str(member.id))
    inviter = userDict.get(str(bruh["invitedBy"]))
    inviter["invited"]["invited"].discard(member.id)
    inviter['invited']['verifiedInvites'].discard(member.id)
    userDict.set(str(bruh["invitedBy"]), inviter)
    userDict.delete(str(member.id))



@bot.event
async def on_member_update(before, after):
    """Checks if a member's roles have been updated and updates the database accordingly.
    """
    arid = [r.id for r in after.roles]
    brid = [r.id for r in before.roles]
    if before.roles != after.roles:
        if roleId in arid:
            if roleId in brid:
                #If the role we're interested is unchanged.
                return
            #If the role was added
            toModify = userDict.get(str(after.id))['invitedBy']
            toModify = userDict.get(str(toModify))
            toModify['invited']['verifiedInvites'].update([after.id])
            console.log(f'[green]{after.name}[/] has been verified - {userDict.get(str(after.id))["invitedBy"]}.')
            return
        if roleId in brid:
            if roleId in arid:
                #If the role we're interested is unchanged.
                return
            #If the role was removed
            toModify = userDict.get(str(before.id))['invitedBy']
            toModify = userDict.get(str(toModify))
            toModify['invited']['verifiedInvites'].discard(before.id)
            console.log(f'[green]{before.name}[/] has been unverified - {userDict.get(str(before.id))["invitedBy"]}.')
            return

@tasks.loop(seconds=10)
async def dump():
    """Dumps all data to the database, essentially committing it.
    """
    print("Dumping...")
    print(inviteDict.dump())
    print(userDict.dump())
    print('------')
dump.start()

@bot.command(help="Shows you the top 10 users with the highest verified invites.")
async def leaderboard(ctx):
    """Shows you the top 10 users with the highest verified invites.
    """
    users = userDict.dump()
    users = [(k, v["invited"]["verifiedInvites"]) for k, v in users.items()]
    users = sorted(users, key=lambda x: len(x[1]), reverse=True)
    users = users[:10]
    console.log(users)
    safe = {bot.get_user(int(k)).name:len(v) for k, v in users}
    df = {"name":list(safe.keys()), "invites":list(safe.values())}
    console.log(df)
    df = pd.DataFrame(df)
    dfi.export(df, 'leaderboard.png', table_conversion='matplotlib')
    file = discord.File('leaderboard.png', filename='leaderboard.png')
    nusers = [f'{i+1}. {bot.get_user(int(users[i][0])).name} - {len(users[i][1])} verified invite(s)' for i in range(len(users))]
    await ctx.send('\n'.join(nusers), file=file)

bot.run("token")
