#!/usr/bin/env python3

import zulip
import re
from typing import Dict, Any


class ModBot(object):
    """
    A docstring documenting this bot.
    """

    def usage(self):
        self.client = zulip.Client(config_file="./zuliprc")
        self.help_msg = """
Available commands:
- `@HASD purge N` - Delete last N messages in the current stream
- `@HASD purge email@example.com N` - Delete last N messages from specified user
"""
        return """Your description of the bot"""

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
                self.send_help_messsage(msg)
                return

            # Handle "purge N" command
            purge_match = re.match(r"purge\s+(\d+)", content)
            if purge_match:
                count = int(purge_match.group(1))
                self.purge_messages(stream_name, count, msg)
                return

            # Handle "purge email@example.com N" command
            user_purge_match = re.match(r"purge\s+([^\s]+)\s+(\d+)", content)
            if user_purge_match:
                user_email = user_purge_match.group(1)
                count = int(user_purge_match.group(2))
                self.purge_user_messages(stream_name, user_email, count, msg)
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

    def send_response(self, original_msg: Dict[str, Any], content: str) -> None:
        """Send a response message."""
        request = {
            "type": original_msg["type"],
            "to": original_msg["display_recipient"],
            "subject": original_msg["subject"],
            "content": content,
        }
        self.client.send_message(request)

    def send_error_message(self, original_msg: Dict[str, Any]) -> None:
        """Send error message with usage instructions."""
        error_msg = "Invalid command format" + self.help_msg
        self.send_response(original_msg, error_msg)

    def send_help_messsage(self, original_msg: Dict[str, Any]) -> None:
        """Send usage instructions"""
        help_msg = self.help_msg
        self.send_response(original_msg, help_msg)


handler_class = ModBot
