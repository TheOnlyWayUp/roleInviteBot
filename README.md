# roleInviteBot

Invite tracker bot, that adds an invite and shows you the leaderboard when one of your invited users is verified. Made for [this thread](https://www.reddit.com/r/Discord_Bots/comments/ras8p6/paid_bot_that_does_an_invite_leaderboard_filtered/).

- You invite people to your server
- When they get a verified role, the inviter gets +1 to their verified Invites
- You can use the !leaderboard command, or use !leaderboard @role to get the leaderboard for the any role

Make sure to edit config.json -
```json
{
    "token": "your bot token",
    "log": "whether or not to show logs (true, false), False Recommended as it's slightly spammy and very resource intensive",
    "staffRoleId": "role id of the staff role, anyone with the role gets access to staff commands",
    "roleId": "the role that needs to be tracked (put main nft role id here)"
}
```
