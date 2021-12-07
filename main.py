import discord, pickledb, asyncio
from discord import user
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
    def delete(self, key):
        try:
            self.db.pop(key, None)
            return True
        except:
            return False

inviteDict = invite()
userDict = invite()
async def updateInvites(guild):
    invites = await guild.invites()
    for invite in invites:
        inviteDict.set(invite.code, {"uses":invite.uses, "inviter":invite.inviter.id, "channel":invite.channel.id, })
        if userDict.get(str(invite.inviter.id)):
            continue
        userDict.set(str(invite.inviter.id), {"invitedBy":None, "invited":{"invited":set(), "verifiedInvites":set()}})
        

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
    bruh = userDict.get(str(member.id))
    inviter = userDict.get(str(bruh["invitedBy"]))
    inviter["invited"]["invited"].discard(member.id)
    inviter['invited']['verifiedInvites'].discard(member.id)
    userDict.set(str(bruh["invitedBy"]), inviter)
    userDict.delete(str(member.id))
# @bot.event
# async def on_member_update(before, after):
#     if before.roles != after.roles:
#         if len(before.roles) < len(after.roles):
#             if roleId in [id.id for id in after.roles]:
#                 console.log(f'[green]{after.name}[/] has been verified.')
#                 toModify = userDict.get(userDict.get(str(after.id))['invitedBy'])
#                 toModify["invited"]['verifiedInvites'].update([after.id])
#                 userDict.set(str(after.id), toModify)
#                 return
#             console.log("Status of L77 - ")
#             invitedBy = userDict.get(str(after.id))['invitedBy']
#             toModify = userDict.get(invitedBy)
#             toModify["invited"]['verifiedInvites'].remove([after.id])
#             userDict.set(str(after.id), toModify)
#             console.log(f'[green]{after.name}[/] has gained a role.')
#             return

#         console.log(f'[green]{after.name}[/] has lost a role.')

@tasks.loop(seconds=10)
async def dump():
    print(inviteDict.getAll())
    print(userDict.getAll())
dump.start()

bot.run("ODgzMDQ3MTk1Mjk1NzY0NTIx.YTEPyQ.-6N9aaoW1Qksn07BrLq0g6RNINo")
