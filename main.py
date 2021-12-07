import discord, pickledb, asyncio
from discord.ext import commands, tasks
from rich.console import Console
from rich.theme import Theme
from rich import print
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
    def getAll(self):
        return self.db
inviteDict = invite()
userDict = invite()
async def updateInvites(guild):
    invites = await guild.invites()
    for invite in invites:
        inviteDict.set(invite.code, {"uses":invite.uses, "inviter":invite.inviter.id, "channel":invite.channel.id, })
        if userDict.get(str(invite.inviter.id)):
            continue
        userDict.set(str(invite.inviter.id), {"invitedBy":None, "invited":set(), "verified":0})
        

@bot.event
async def on_ready():
    console.print(f'Logged in as [green]{bot.user.name}[/] ({bot.user.id}) and in {len(bot.guilds)} {"servers" if len(bot.guilds) > 1 else "server"}.')
    console.log(f"Connected to Discord Gateway. Dpy version {discord.__version__}, servers - {', '.join([str(guild.name) for guild in bot.guilds])}.")
    await updateInvites(bot.guilds[0])
    print('------')


@bot.event
async def on_invite_create(invite):
    await updateInvites(invite.guild)

@bot.event
async def on_member_join(member):
    invites = await member.guild.invites()
    for invite in invites:
        if invite.uses > inviteDict.get(invite.code)["uses"]:
            console.log(f'[green]{member.name}[/] has joined the server with an invite that has been used {invite.uses - inviteDict.get(invite.code)["uses"]} times. And was invited by {invite.inviter.name}.')
            bruh = userDict.get(str(invite.inviter.id))
            bruh["invited"].update([member.id])
            userDict.set(str(invite.inviter.id), bruh)
            #console.log("Trying to set invites")
            userDict.set(str(member.id), {"invitedBy":invite.inviter.id, "invited":set()})
            console.log(f'[green]{member.name}[/] has been added to the list of users who invited {invite.inviter.name}. {inviteDict.get(str(invite.inviter.id))}')
            break
    await updateInvites(member.guild)

@bot.event
async def on_member_update(before, after):
    if before.roles != after.roles:
        if len(before.roles) < len(after.roles):
            if roleId in [id.id for id in after.roles]:
                console.log(f'[green]{after.name}[/] has been verified.')
                userDict.set(str(after.id), {"verified":1})
            console.log(f'[green]{after.name}[/] has gained a role.')
            return
        console.log(f'[green]{after.name}[/] has lost a role.')

@tasks.loop(seconds=10)
async def dump():
    print(inviteDict.getAll())
    print(userDict.getAll())
dump.start()

bot.run("token")
