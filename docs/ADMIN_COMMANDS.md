# Admin Commands Guide

All admin commands are **prefix commands** (use `!` prefix, not `/`).

## Permission Model

- **Server commands**: Guild owner only
- **Club/Member/Session commands**: Guild owner OR club admin/owner in the target club

Guild owners have unrestricted access to all commands in their server. This allows bootstrapping:
register server → create first club → add members → promote an admin.

## Using an Admin Channel

All club/member/session commands accept an optional `--channel <id>` flag so they can be
issued from a dedicated `#admin` channel without needing to navigate to the club channel.

```
# From #admin channel, targeting #book-club (id: 123456789)
!member_add @alice --channel 123456789
!session_create "Dune" Frank Herbert --channel 123456789
!club_delete --channel 123456789
```

Omitting `--channel` targets the current channel as usual.

---

## Server Commands

These are server-wide operations and do **not** support `--channel`.

### `!server_register`

Registers the Discord server with the bot.

**Permission**: Guild owner only  
**Usage**: `!server_register`

### `!server_update <name>`

Updates the server's registered name.

**Permission**: Guild owner only  
**Usage**: `!server_update <new_name>`

**Example**: `!server_update "My Book Club Server"`

### `!server_delete`

Deletes the server registration and ALL associated data (clubs, members, sessions).

**Permission**: Guild owner only  
**Usage**: `!server_delete`  
**Confirmation**: Requires `y`

---

## Club Commands

### `!club_create <name> [--channel <channel_id>]`

Creates a new book club. The caller is **automatically assigned as club owner**.

**Permission**: Guild owner OR club admin in the target channel  
**Usage**: `!club_create <name> [--channel <channel_id>]`

**Examples**:
```
!club_create "Classic Literature"
!club_create "Sci-Fi Club" --channel 123456789
```

### `!club_update [--name <name>] [--new-channel <channel_id>] [--channel <channel_id>]`

Updates club details. Use `--new-channel` to move the club to a different Discord channel.
Use `--channel` to target a specific club from another channel (e.g. `#admin`).

**Permission**: Guild owner OR club admin in the target channel  
**At least one of** `--name` or `--new-channel` required

**Examples**:
```
!club_update --name "Sci-Fi Readers"
!club_update --new-channel 987654321
!club_update --name "Updated" --new-channel 987654321 --channel 123456789
```

### `!club_delete [--channel <channel_id>]`

Deletes the book club and all its data.

**Permission**: Guild owner OR club admin in the target channel  
**Usage**: `!club_delete [--channel <channel_id>]`  
**Confirmation**: Requires `y`

**Example**: `!club_delete --channel 123456789`

---

## Member Commands

### `!member_add @User [--channel <channel_id>]`

Adds a Discord user to a club. If the user already has a member record (from another club),
they are linked to this club without creating a duplicate.

**Permission**: Guild owner OR club admin in the target channel  
**Usage**: `!member_add @Username [--channel <channel_id>]`

**Examples**:
```
!member_add @alice
!member_add @alice --channel 123456789
```

### `!member_remove <member_id> [--channel <channel_id>]`

Removes a member by their ID.

**Permission**: Guild owner OR club admin in the target channel  
**Usage**: `!member_remove <member_id> [--channel <channel_id>]`  
**Confirmation**: Requires `y`

**Example**: `!member_remove 42 --channel 123456789`

### `!member_role <member_id> <role> [--channel <channel_id>]`

Updates a member's role in the club.

**Permission**: Guild owner OR club admin in the target channel  
**Usage**: `!member_role <member_id> <admin|member> [--channel <channel_id>]`

**Roles**:
- `admin` — Can manage club/members/sessions
- `member` — Standard membership, read-only access to club commands

**Examples**:
```
!member_role 42 admin
!member_role 42 member --channel 123456789
```

---

## Session Commands

### `!session_create "<book_title>" <author> [--channel <channel_id>]`

Creates a new reading session for a club.

**Permission**: Guild owner OR club admin in the target channel  
**Usage**: `!session_create "<title>" <author> [--channel <channel_id>]`

**Examples**:
```
!session_create "The Great Gatsby" F. Scott Fitzgerald
!session_create "Dune" Frank Herbert --channel 123456789
```

### `!session_update [--due-date YYYY-MM-DD] [--book "<title>|<author>"] [--channel <channel_id>]`

Updates the active session. At least one of `--due-date` or `--book` required.

**Permission**: Guild owner OR club admin in the target channel  
**Note**: Book format uses a pipe separator: `"<title>|<author>"`

**Examples**:
```
!session_update --due-date 2026-06-15
!session_update --book "Dune|Frank Herbert"
!session_update --due-date 2026-06-15 --book "Dune|Frank Herbert" --channel 123456789
```

### `!session_delete [--channel <channel_id>]`

Deletes the active reading session.

**Permission**: Guild owner OR club admin in the target channel  
**Usage**: `!session_delete [--channel <channel_id>]`  
**Confirmation**: Requires `y`

**Example**: `!session_delete --channel 123456789`

---

## Error Reference

| Error | Cause | Solution |
|-------|-------|----------|
| `❌ Only the server owner can use this command` | Non-owner running a server command | Ask the guild owner |
| `❌ You need to be a club admin or owner` | Insufficient permissions | Ask a club admin or the guild owner |
| `❌ No book club found in that channel` | No club linked to the target channel | Create one with `!club_create` |
| `❌ No active session found in that channel` | No reading session in progress | Create one with `!session_create` |
| `❌ Role must be 'admin' or 'member'` | Invalid role in `!member_role` | Use `admin` or `member` |
| `⏰ Confirmation timed out` | No response within 30 seconds | Re-run the command |

---

## Bootstrap Workflow

Fresh server setup from an `#admin` channel (channel ID: `123456`):

```
1. !server_register
   ✅ Server registered

2. !club_create "My Book Club" --channel 123456
   ✅ Club created — caller assigned as owner

3. !member_add @alice --channel 123456
   ✅ Alice added

4. !member_role <alice_id> admin --channel 123456
   ✅ Alice is now admin

5. !session_create "Dune" Frank Herbert --channel 123456
   ✅ Session created

6. !session_update --due-date 2026-06-15 --channel 123456
   ✅ Due date set
```
