#!/usr/bin/env python3

import zulip
import re
from typing import Dict, Any
import json
import os

NOTES_FILE = "notes.json"

class ModerationBot(object):
    """
    A moderation bot to help manage larger communities.
    """

    # Pre-compile regexes for efficiency
    RESOLVE_COMMAND = re.compile(r"resolve$")
    UNRESOLVE_COMMAND = re.compile(r"unresolve$")
    PURGE_COMMAND = re.compile(r"purge\s+(\d+)$")
    PURGE_USER_COMMAND = re.compile(r"purge\s+([^\s]+)\s+(\d+)$")
    PURGE_USER_ALL_COMMAND = re.compile(r"purge\s+([^\s@]+@[^\s]+)$")
    MUTE_COMMAND = re.compile(r"mute\s+([^\s@]+@[^\s]+)$")
    UNMUTE_COMMAND = re.compile(r"unmute\s+([^\s@]+@[^\s]+)$")
    GET_NOTES_COMMAND = re.compile(r"getnotes\s+([^\s@]+@[^\s]+)$")
    ADD_NOTE_COMMAND = re.compile(r"addnote\s+([^\s@]+@[^\s]+)\s+(.+)$")

    def usage(self) -> str:
        """
        Returns the bot's usage string.
        """
        self.zulip_client = zulip.Client(config_file="./zuliprc")
        self.admin_zulip_client = zulip.Client(config_file="./personalzuliprc")
        return "A moderation bot to help manage larger communities."

    def handle_message(self, message: Dict[str, Any], bot_handler: Any) -> None:
        """
        Handles incoming messages, deletes the command message, and processes the command.
        """
        self.zulip_client.delete_message(message["id"])
        self.process_command(message)

    def process_command(self, message: Dict[str, Any]) -> None:
        """
        Parses and processes bot commands from a message.
        """
        content = message["content"].strip()
        stream_name = message.get("display_recipient", "")
        topic_name = message.get("subject", "")

        try:
            # Handle help and empty commands
            if content in ("", "help"):
                self.send_help_message(message)
                return

            # User commands (available to all users)
            if self.RESOLVE_COMMAND.match(content):
                self.resolve_topic(message)
                return

            if self.UNRESOLVE_COMMAND.match(content):
                self.unresolve_topic(message)
                return

            # Moderation commands (restricted to moderators)
            if not self.is_moderator(message):
                self.send_response(message, "Unauthorized to use moderation commands.")
                return

            # Purge commands
            purge_match = self.PURGE_COMMAND.match(content)
            if purge_match:
                count = int(purge_match.group(1))
                self.purge_messages(stream_name, topic_name, count, message)
                return

            purge_user_match = self.PURGE_USER_COMMAND.match(content)
            if purge_user_match:
                user_email = purge_user_match.group(1)
                count = int(purge_user_match.group(2))
                self.purge_user_messages(stream_name, topic_name, user_email, count, message)
                return

            purge_user_all_match = self.PURGE_USER_ALL_COMMAND.match(content)
            if purge_user_all_match:
                user_email = purge_user_all_match.group(1)
                self.purge_user_messages(stream_name, topic_name, user_email, 1000, message)
                return

            if content.strip() == "clean":
                self.purge_user_messages(stream_name, topic_name, "hasd-bot@hasd.zulipchat.com", 1000, message)
                return

            # Mute/unmute commands
            mute_match = self.MUTE_COMMAND.match(content)
            if mute_match:
                user_email = mute_match.group(1)
                self.mute_user(user_email, message)
                return

            unmute_match = self.UNMUTE_COMMAND.match(content)
            if unmute_match:
                user_email = unmute_match.group(1)
                self.unmute_user(user_email, message)
                return

            # Note commands
            get_notes_match = self.GET_NOTES_COMMAND.match(content)
            if get_notes_match:
                user_email = get_notes_match.group(1)
                author_id = message["sender_id"]
                self.get_notes(user_email, author_id, message)
                return

            add_note_match = self.ADD_NOTE_COMMAND.match(content)
            if add_note_match:
                user_email = add_note_match.group(1)
                note = add_note_match.group(2)
                self.add_note(user_email, note, message)
                return

            # If no valid command is matched, send an error message.
            self.send_error_message(message)

        except Exception as e:
            self.send_response(message, f"Error processing command: {str(e)}")

    def purge_messages(self, stream_name: str, topic_name: str, count: int, original_message: Dict[str, Any]) -> None:
        """Delete the last N messages from a topic."""
        try:
            # Get the most recent messages from the topic
            response = self.zulip_client.get_messages(
                {
                    "anchor": "newest",
                    "num_before": count,
                    "num_after": 0,
                    "narrow": [{"operator": "stream", "operand": stream_name}, {"operator": "topic", "operand": topic_name}],
                }
            )

            if response["result"] != "success":
                self.send_response(original_message, "Failed to fetch messages for purging.")
                return

            # Delete the fetched messages
            deleted_count = 0
            for message in response["messages"]:
                delete_response = self.zulip_client.delete_message(message["id"])
                if delete_response["result"] == "success":
                    deleted_count += 1

            if deleted_count > 0:
                self.send_response(original_message, f"Successfully deleted {deleted_count} messages.")

        except Exception as e:
            self.send_response(original_message, f"Error while purging messages: {str(e)}")

    def purge_user_messages(
        self, stream_name: str, topic_name: str, user_email: str, count: int, original_message: Dict[str, Any]
    ) -> None:
        """Delete the last N messages from a specific user in a topic."""
        try:
            # Get user-specific messages
            response = self.zulip_client.get_messages(
                {
                    "anchor": "newest",
                    "num_before": count,
                    "num_after": 0,
                    "narrow": [
                        {"operator": "stream", "operand": stream_name},
                        {"operator": "topic", "operand": topic_name},
                        {"operator": "sender", "operand": user_email},
                    ],
                }
            )

            if response["result"] != "success":
                self.send_response(original_message, "Failed to fetch user messages for purging.")
                return

            # Delete the fetched messages
            deleted_count = 0
            for message in response["messages"]:
                delete_response = self.zulip_client.delete_message(message["id"])
                if delete_response["result"] == "success":
                    deleted_count += 1

            self.send_response(
                original_message, f"Successfully deleted {deleted_count} messages from {user_email}."
            )

        except Exception as e:
            self.send_response(original_message, f"Error while purging user messages: {str(e)}")

    def mute_user(self, user_email: str, message: Dict[str, Any]):
        """Mutes a user by removing them from the 'everyone' group and updating their name."""
        user_id = self.get_user_id(user_email)
        if not user_id:
            self.send_response(message, f"Could not find user with email: {user_email}")
            return

        # Remove user from the 'everyone' group to mute them.
        # NOTE: The group ID (1066759) is specific to this Zulip instance.
        request = {"delete": [user_id]}
        response = self.admin_zulip_client.update_user_group_members(1066759, request)

        user_details = self.zulip_client.get_user_by_id(user_id)
        self.zulip_client.update_user_by_id(user_id, full_name=f"{user_details['user']['full_name']} (Muted)")

        if response["result"] == "success":
            self.send_response(message, f"Successfully muted user {user_email}.")
            self.send_private_message(user_id, "You have been muted. You can read discussions but cannot post. Contact a moderator to appeal.")
        else:
            self.send_response(message, f"Failed to mute user: {response.get('msg', 'Unknown error')}")

    def unmute_user(self, user_email: str, message: Dict[str, Any]):
        """Unmutes a user by adding them back to the 'everyone' group and updating their name."""
        user_id = self.get_user_id(user_email)
        if not user_id:
            self.send_response(message, f"Could not find user with email: {user_email}")
            return

        # Add user back to the 'everyone' group to unmute.
        # NOTE: The group ID (1066759) is specific to this Zulip instance.
        request = {"add": [user_id]}
        response = self.admin_zulip_client.update_user_group_members(1066759, request)

        user_details = self.zulip_client.get_user_by_id(user_id)
        new_name = user_details["user"]["full_name"].replace(" (Muted)", "").strip()
        self.zulip_client.update_user_by_id(user_id, full_name=new_name)

        if response["result"] == "success":
            self.send_response(message, f"Successfully unmuted user {user_email}.")
            self.send_private_message(user_id, "You have been unmuted. Please follow the [Community Guidelines](https://hasd.zulipchat.com/#narrow/channel/509975-fbla-bulletin/topic/resources/near/526484245).")
        else:
            self.send_response(message, f"Failed to unmute user: {response.get('msg', 'Unknown error')}")

    def add_note(self, user_email: str, note: str, message: Dict[str, Any]):
        """Adds a moderation note for a specific user."""
        notes = self.load_notes()
        user_id = str(self.get_user_id(user_email))
        if user_id:
            if user_id not in notes:
                notes[user_id] = []
            notes[user_id].append(note)
            self.save_notes(notes)
            self.send_response(message, "Note added successfully.")
        else:
            self.send_response(message, f"Could not find user with email: {user_email}")

    def get_notes(self, user_email: str, author_id: int, message: Dict[str, Any]):
        """Retrieves all notes for a specific user and sends them privately to the requester."""
        notes = self.load_notes()
        user_id = str(self.get_user_id(user_email))
        if user_id and user_id in notes and notes[user_id]:
            user_notes = notes[user_id]
            notes_string = f"Notes for {user_email}:\n" + "\n".join(f"{i+1}. {note}" for i, note in enumerate(user_notes))
            self.send_private_message(author_id, notes_string)
            self.send_response(message, "Notes sent privately.")
        else:
            self.send_private_message(author_id, f"No notes found for {user_email}.")

    def load_notes(self) -> Dict[str, Any]:
        """Loads notes from the JSON file."""
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    # Return an empty dictionary if the file is empty or malformed
                    return {}
        return {}

    def save_notes(self, notes: Dict[str, Any]) -> None:
        """Saves notes to the JSON file."""
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes, f, indent=4)

    def resolve_topic(self, message: Dict[str, Any]) -> None:
        """Marks a topic as resolved by adding a checkmark prefix."""
        # Send a temporary message to get a message ID for topic update
        temp_message = self.send_response(message, "Resolving...")
        request = {
            "message_id": temp_message["id"],
            "topic": f"✔ {message['subject']}",
            "propagate_mode": "change_all"
        }
        self.zulip_client.update_message(request)
        self.zulip_client.delete_message(temp_message["id"])

    def unresolve_topic(self, message: Dict[str, Any]) -> None:
        """Marks a topic as unresolved by removing the checkmark prefix."""
        # Send a temporary message to get a message ID for topic update
        temp_message = self.send_response(message, "Unresolving...")
        request = {
            "message_id": temp_message["id"],
            "topic": message["subject"].lstrip("✔ "),
            "propagate_mode": "change_all"
        }
        self.zulip_client.update_message(request)
        self.zulip_client.delete_message(temp_message["id"])

    def get_user_id(self, user_email: str) -> int:
        """Retrieves a user's ID from their email address."""
        try:
            result = self.zulip_client.call_endpoint(
                url=f"/users/{user_email}",
                method="GET",
            )
            return result["user"]["user_id"]
        except Exception:
            return None

    def send_response(self, original_message: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Sends a response message to the same topic as the original message."""
        request = {
            "type": original_message["type"],
            "to": original_message["display_recipient"],
            "subject": original_message["subject"],
            "content": content,
        }
        return self.zulip_client.send_message(request)

    def send_private_message(self, user_id: int, content: str) -> None:
        """Sends a private message to a user."""
        request = {
            "type": "private",
            "to": [user_id],
            "content": content,
        }
        self.zulip_client.send_message(request)

    def send_error_message(self, message: Dict[str, Any]) -> None:
        """Sends an error message indicating an invalid command."""
        self.send_response(message, "Invalid command. See `help` for available commands.")

    def send_help_message(self, message: Dict[str, Any]) -> None:
        """Sends a help message with available commands based on user role."""
        help_text = """
**Available Commands:**

**User Commands:**
- `@HASD resolve`: Mark the current topic as resolved.
- `@HASD unresolve`: Mark the current topic as unresolved.
"""
        if self.is_moderator(message):
            help_text += """
**Moderation Commands:**
- `@HASD purge <N>`: Delete the last N messages in the current topic.
- `@HASD purge <email> <N>`: Delete the last N messages from a user in the current topic.
- `@HASD purge <email>`: Delete all messages from a user in the current topic.
- `@HASD clean`: Clean up all messages from this bot in the current topic.
- `@HASD mute <email>`: Mute a user.
- `@HASD unmute <email>`: Unmute a user.
- `@HASD getnotes <email>`: Get moderation notes for a user.
- `@HASD addnote <email> <note>`: Add a moderation note for a user.
"""
        self.send_response(message, help_text)

    def is_moderator(self, message: Dict[str, Any]) -> bool:
        """Checks if the message author is a moderator."""
        author_details = self.zulip_client.get_user_by_id(message["sender_id"])
        # Role > 300 are members and guests.
        return int(author_details["user"]["role"]) <= 300

handler_class = ModerationBot
