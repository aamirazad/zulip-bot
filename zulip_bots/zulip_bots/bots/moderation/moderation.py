#!/usr/bin/env python3

import zulip
import re
from typing import Dict, Any
import json
import os

NOTES_FILE = "./NOTES.json"

class ModBot(object):
    """
    A moderation bot to help manage larger communities
    """

    def usage(self):
        self.client = zulip.Client(config_file="./zuliprc")
        self.adminClient = zulip.Client(config_file="./personalzuliprc")
        self.help_msg = """
Available commands:
- `@HASD purge N` - Delete last N messages in the current stream
- `@HASD purge email@example.com N` - Delete last N messages from specified user
- `@HASD purge email@example.com` - Delete all messages from specified user in current channel
- `@HASD clean` Clean up all messages from the bot
- `@HASD mute email@example.com` - Removes the specified user's ability to post messages
- `@HASD unmute email@example.com` - Gives the specified user the ability to post messages
- `@HASD getnotes email@example.com` - Get mod notes of the specified user
- `@HASD addnote email@example.com <note>` - Adds a mod note to the specified user
"""
        return """A moderation bot to help manage larger communities"""

    def handle_message(self, message, bot_handler):
        self.delete_command_msg(message)
        self.process_command(message)

    def process_command(self, msg: Dict[str, Any]) -> None:
        """Process bot commands."""
        content = msg["content"].strip()
        stream_name = msg.get("display_recipient", "")

        author = self.client.get_user_by_id(msg["sender_id"])
        if int(author["user"]["role"]) > 300:
            self.send_response(msg, "Unauthorized")
            return

        # Parse the command
        try:
            if content in ("", "help"):
                self.send_help_message(msg)
                return

            # Handle "purge N" command
            purge_match = re.match(r"purge\s+(\d+)$", content)
            if purge_match:
                count = int(purge_match.group(1))
                self.purge_messages(stream_name, count, msg)
                return

            # Handle "purge email@example.com N" command
            user_purge_r_match = re.match(r"purge\s+([^\s]+)\s+(\d+)$", content)
            if user_purge_r_match:
                user_email = user_purge_r_match.group(1)
                count = int(user_purge_r_match.group(2))
                self.purge_user_messages(stream_name, user_email, count, msg)
                return

            # Handle "purge email@example.com" command (all messages from user)
            user_purge_all_match = re.match(r"purge\s+([^\s@]+@[^\s]+)$", content)
            if user_purge_all_match:
                user_email = user_purge_all_match.group(1)
                self.purge_user_messages(stream_name, user_email, 1000, msg)
                return

            # Handle "clean" command (delete all bot messages in stream)
            if content.strip() == "clean":
                self.purge_user_messages(stream_name, "hasd-bot@hasd.zulipchat.com", 1000, msg)
                return
            
            # Handle mute command
            user_mute_match = re.match(r"mute\s+([^\s@]+@[^\s]+)$", content)
            if user_mute_match:
                user_email = user_mute_match.group(1)
                self.mute_user(user_email, msg)
                return

            # Handle unmute command
            user_unmute_match = re.match(r"unmute\s+([^\s@]+@[^\s]+)$", content)
            if user_unmute_match:
                user_email = user_unmute_match.group(1)
                self.unmute_user(user_email, msg)
                return
            
            # Handle getnotes command
            user_getnote_match = re.match(r"getnotes\s+([^\s@]+@[^\s]+)$", content)
            if user_getnote_match:
                user_email = user_getnote_match.group(1)
                self.get_notes(user_email, author["user"]["user_id"], msg)
                return

            # Handle addnote
            user_addnote_match = re.match(r"addnote\s+([^\s@]+@[^\s]+)\s+(.+)$", content)
            if user_addnote_match:
                user_email = user_addnote_match.group(1)
                note = user_addnote_match.group(2)
                self.add_note(user_email, note, msg)
                return

            # If no valid command matched
            self.send_error_message(msg)

        except Exception as e:
            self.send_response(msg, f"Error processing command: {str(e)}")

    def purge_messages(self, stream_name: str, count: int, original_msg: Dict[str, Any]) -> None:
        """Delete the last N messages from a stream."""
        try:
            # Get messages
            response = self.client.get_messages(
                {
                    "anchor": "newest",
                    "num_before": (count),
                    "num_after": 0,
                    "narrow": [{"operator": "stream", "operand": stream_name}],
                }
            )

            if response["result"] != "success":
                self.send_response(original_msg, "Failed to fetch messages")
                return

            # Delete messages
            deleted_count = 0
            for message in response["messages"]:
                del_response = self.client.delete_message(message["id"])
                if del_response["result"] == "success":
                    deleted_count += 1

            self.send_response(original_msg, f"Successfully deleted {deleted_count} messages")

        except Exception as e:
            self.send_response(original_msg, f"Error while purging messages: {str(e)}")

    def purge_user_messages(
        self, stream_name: str, user_email: str, count: int, original_msg: Dict[str, Any]
    ) -> None:
        """Delete the last N messages from a specific user in a stream."""
        try:
            # Get messages
            response = self.client.get_messages(
                {
                    "anchor": "newest",
                    "num_before": count,
                    "num_after": 0,
                    "narrow": [
                        {"operator": "stream", "operand": stream_name},
                        {"operator": "sender", "operand": user_email},
                    ],
                }
            )

            if response["result"] != "success":
                self.send_response(original_msg, response)
                return

            # Delete messages
            deleted_count = 0
            for message in response["messages"]:
                del_response = self.client.delete_message(message["id"])
                if del_response["result"] == "success":
                    deleted_count += 1

            self.send_response(
                original_msg, f"Successfully deleted {deleted_count} messages from {user_email}"
            )

        except Exception as e:
            self.send_response(original_msg, f"Error while purging user messages: {str(e)}")

    def delete_command_msg(self, msg: Dict[str, Any]):
        self.client.delete_message(msg["id"])
    
    def mute_user(self, user_email: str, msg: Dict[str, Any]):
        user = self.getUserByEmail(user_email)
        userId = user["user"]["user_id"]

        request = {
            "delete": [userId]
        }
        res = self.adminClient.update_user_group_members(1066759, request)

        if res["result"] == "success":
            self.send_response(msg, f"Successfully muted user {user_email}")
        else:
            self.send_response(msg, res)
        
    def unmute_user(self, user_email: str, msg: Dict[str, Any]):
        userId = self.getUserId(user_email)

        request = {
            "add": [userId]
        }
        res = self.adminClient.update_user_group_members(1066759, request)

        if res["result"] == "success":
            self.send_response(msg, f"Successfully unmuted user {user_email}")
        else:
            self.send_response(msg, res)
    
    def add_note(self, user_email: str, note: str, msg: Dict[str, Any]):
        """Adds a note for a specific user."""
        notes = self.load_notes()
        user_id = str(self.getUserId(user_email))
        if user_id not in notes:
            notes[user_id] = []
        notes[user_id].append(note)
        self.save_notes(notes)
        self.send_response(msg, "Note added")

    def get_notes(self, user_email: str, author: int, msg: Dict[str, Any]):
        """Retrieves all notes for a specific user."""
        notes = self.load_notes()
        user_id = str(self.getUserId(user_email))
        if user_id in notes:
            user_notes = notes[user_id]
            if user_notes:
                pretty_string = f"Notes for {user_email}:\n"
                for i, note in enumerate(user_notes):
                    pretty_string += f"{i+1}. {note}\n"
                self.send_private_response(author, pretty_string.strip())
                self.send_response(msg, "Private message sent with the notes")

            else:
                self.send_private_response(author, f"No notes found for {user_email}.")
                return []
        else:
            self.send_private_response(author, f"No notes found for {user_email}.")
            return []
        
    def load_notes(self):
        """Loads notes from the JSON file."""
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    # Handle empty or malformed JSON file
                    return {}
        return {}

    def save_notes(self, notes):
        """Saves notes to the JSON file."""
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes, f, indent=4) # indent for pretty printing

    def getUserId(self, user_email: str):
        result = self.client.call_endpoint(
            url=f"/users/{user_email}",
            method="GET",
        )
        return result["user"]["user_id"]
        

    def send_response(self, original_msg: Dict[str, Any], content: str) -> None:
        """Send a response message."""
        request = {
            "type": original_msg["type"],
            "to": original_msg["display_recipient"],
            "subject": original_msg["subject"],
            "content": content,
        }
        self.client.send_message(request)

    def send_private_response(self, userId: int, content: str) -> None:
        """Send a private message."""
        request = {
            "type": "private",
            "to": [userId],
            "content": content,
        }
        self.client.send_message(request)

    def send_error_message(self, original_msg: Dict[str, Any]) -> None:
        """Send error message with usage instructions."""
        error_msg = "Invalid command format" + self.help_msg
        self.send_response(original_msg, error_msg)

    def send_help_message(self, original_msg: Dict[str, Any]) -> None:
        """Send usage instructions"""
        help_msg = self.help_msg
        self.send_response(original_msg, help_msg)


handler_class = ModBot
