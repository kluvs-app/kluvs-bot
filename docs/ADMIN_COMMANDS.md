# Admin Commands Guide

All admin commands are **prefix commands** (use `!` prefix, not `/`).

## Permission Model

- **Server commands**: Guild owner only
- **Club/Member/Session commands**: Guild owner OR club admin/owner

Guild owners have unrestricted access to all commands in their server. This allows bootstrapping: register server → create first club → add members → promote an admin.

## Server Commands

Commands for managing server registration and settings.

### `!server_register`

Registers the Discord server with the bot.

**Permission**: Guild owner only  
**Usage**: `!server_register`

**Example**:
```
!server_register
```

**Response**: Confirms server registration

### `!server_update <name>`

Updates the server's registered name.

**Permission**: Guild owner only  
**Usage**: `!server_update <new_name>`

**Example**:
```
!server_update "My Book Club Server"
```

**Response**: Confirms name update

### `!server_delete`

Deletes the server registration and ALL associated data (clubs, members, sessions).

**Permission**: Guild owner only  
**Usage**: `!server_delete`

**Confirmation**: Requires typing `y` to confirm; any other response cancels

**Example**:
```
!server_delete
⚠️ This will delete **all server data** including clubs, members, and sessions...
> y
✅ Server registration and all associated data have been removed.
```

## Club Commands

Commands for managing book clubs within the server.

### `!club_create <name>`

Creates a new book club in the current channel.

**Permission**: Guild owner OR club admin in this channel  
**Usage**: `!club_create <club_name>`

**Example**:
```
!club_create "Classic Literature"
```

**Response**: Confirms club creation in the channel

### `!club_update [--name <name>] [--channel <channel_id>]`

Updates club details. At least one flag required.

**Permission**: Guild owner OR club admin in this channel  
**Usage**: `!club_update --name "New Name"` or `!club_update --channel 123456789` or both

**Examples**:
```
!club_update --name "Sci-Fi Readers"
!club_update --channel 987654321
!club_update --name "Updated Club" --channel 987654321
```

**Response**: Confirms club update

### `!club_delete`

Deletes the book club in the current channel and all associated sessions.

**Permission**: Guild owner OR club admin in this channel  
**Usage**: `!club_delete`

**Confirmation**: Requires typing `y` to confirm

**Example**:
```
!club_delete
⚠️ This will delete **Test Club** and all its data...
> y
✅ **Test Club** has been deleted.
```

## Member Commands

Commands for managing club members.

### `!member_add @User`

Adds a Discord user to the current channel's book club.

**Permission**: Guild owner OR club admin in this channel  
**Usage**: `!member_add @Username`

**Example**:
```
!member_add @alice
```

**Response**: Confirms member addition and displays their name

### `!member_remove <member_id>`

Removes a member from the club.

**Permission**: Guild owner OR club admin in this channel  
**Usage**: `!member_remove <member_id>`

**Confirmation**: Requires typing `y` to confirm

**Example**:
```
!member_remove 42
⚠️ Remove member `42` from the club...
> y
✅ Member `42` has been removed.
```

### `!member_role <member_id> <role>`

Updates a member's role in the club.

**Permission**: Guild owner OR club admin in this channel  
**Usage**: `!member_role <member_id> <admin|member>`

**Roles**:
- `admin` - Can manage club/members/sessions
- `member` - Can view club content only

**Examples**:
```
!member_role 42 admin
!member_role 42 member
```

**Response**: Confirms role update

**Error**: Invalid role (must be `admin` or `member`)

## Session Commands

Commands for managing reading sessions.

### `!session_create <book_title> <author>`

Creates a new reading session for the club.

**Permission**: Guild owner OR club admin in this channel  
**Usage**: `!session_create "<title>" <author>`

**Example**:
```
!session_create "The Great Gatsby" F. Scott Fitzgerald
```

**Response**: Confirms session creation with book title

### `!session_update [--due-date YYYY-MM-DD] [--book "<title>|<author>"]`

Updates the active session. At least one flag required.

**Permission**: Guild owner OR club admin in this channel  
**Usage**: `!session_update --due-date YYYY-MM-DD` or `!session_update --book "<title>|<author>"` or both

**Examples**:
```
!session_update --due-date 2026-06-15
!session_update --book "Dune|Frank Herbert"
!session_update --due-date 2026-06-15 --book "Dune|Frank Herbert"
```

**Response**: Confirms session update

**Note**: Book format is `"<title>|<author>"` with pipe separator

### `!session_delete`

Deletes the active reading session for the club.

**Permission**: Guild owner OR club admin in this channel  
**Usage**: `!session_delete`

**Confirmation**: Requires typing `y` to confirm

**Example**:
```
!session_delete
⚠️ This will permanently delete the active reading session...
> y
✅ The active reading session has been deleted.
```

## Error Messages

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `❌ Only the server owner can use this command` | Non-owner trying server command | Ask guild owner to run |
| `❌ You need to be a club admin or owner to use this command` | Non-admin/owner trying club op | Ask club admin or guild owner to run |
| `❌ No book club found in this channel` | Channel has no linked club | Create club first with `!club_create` |
| `❌ No active session found in this channel` | No reading session in progress | Create session with `!session_create` |
| `❌ Role must be 'admin' or 'member'` | Invalid role in `!member_role` | Use `admin` or `member` only |
| `⏰ Confirmation timed out` | Didn't confirm `y/n` within 30 seconds | Re-run the command |

## Bootstrap Workflow

Fresh server setup:

```
1. Guild Owner: !server_register
   ✅ Server registered

2. Guild Owner: !club_create "My Book Club"
   ✅ Club created in #channel

3. Guild Owner: !member_add @alice
   ✅ Alice added

4. Guild Owner: !member_role <alice_id> admin
   ✅ Alice is now admin

5. Alice (club admin): !session_create "Dune" Frank Herbert
   ✅ Session created

6. Alice: !session_update --due-date 2026-06-15
   ✅ Due date set
```

## Notes

- All destructive commands (`_delete`) require `y/n` confirmation
- Confirmation timeout is **30 seconds**
- Guild owner can bypass club admin requirement for all club/member/session operations
- Each club is tied to a Discord channel
- Members are identified by Discord ID, not mention (for robustness)
