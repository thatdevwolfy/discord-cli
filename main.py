import os
import threading
import requests
import time
import json
# Made by thatdevwolfy!
bot_token = 'user token'
base_url = 'https://discord.com/api/'

class DiscordClient:
    def __init__(self):
        self.running = False
        self.selected_server = None
        self.selected_channel = None
        self.messages = []
        self.statuses = [
            "Running DiscordCLI V1 - https://github.com/thatdevwolfy/discord-cli",
            "DiscordCLI By lrdwlfy",
            "Using Discord In Linux"
        ]
        self.current_status_index = 0

    def start(self):
        if self.check_token_validity(bot_token):
            self.running = True
            user = self.get_user_info(bot_token)
            print(f"Logged in as {user['username']} ({user['id']})")
            print("")
            self.set_bot_status(bot_token)
            threading.Thread(target=self.rotate_statuses, daemon=True).start()  # Start rotating statuses in background
            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.send_messages()
        else:
            print("Invalid token. Please provide a valid bot token.")

    def check_token_validity(self, token):
        try:
            response = requests.get(base_url + 'users/@me', headers={'Authorization': f'{token}'})
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_user_info(self, token):
        try:
            response = requests.get(base_url + 'users/@me', headers={'Authorization': f'{token}'})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(e)
            return {}

    def set_bot_status(self, token):
        try:
            payload = {
                "custom_status": {
                    "text": self.statuses[self.current_status_index]
                }
            }
            headers = {
                "Authorization": f"{token}",
                "Content-Type": "application/json"
            }
            response = requests.patch(base_url + 'users/@me/settings', headers=headers, data=json.dumps(payload))
            response.raise_for_status()
#            print("Bot status updated successfully.")
        except requests.exceptions.RequestException as e:
            print("Failed to update bot status:", e)

    def rotate_statuses(self):
        while self.running:
            self.current_status_index = (self.current_status_index + 1) % len(self.statuses)
            self.set_bot_status(bot_token)
            time.sleep(15)  # Rotate status every 30 seconds

    def stop(self):
        self.running = False
        print("Discord client stopped.")

    def receive_messages(self):
        while self.running:
            if self.selected_channel:
                try:
                    messages = self.fetch_channel_messages(self.selected_channel['id'])
                    if messages != self.messages:
                        self.messages = messages
                        self.print_messages()
                except requests.exceptions.RequestException as e:
                    print(e)
            time.sleep(3)

    def fetch_bot_servers(self):
        try:
            response = requests.get(base_url + 'users/@me/guilds', headers={'Authorization': bot_token})
            response.raise_for_status()
            servers = response.json()
            servers.sort(key=lambda x: x['name'])
            return servers
        except requests.exceptions.RequestException as e:
            print(e)
            return []

    def fetch_server_channels(self, server_id):
        try:
            response = requests.get(base_url + f'guilds/{server_id}/channels', headers={'Authorization': bot_token})
            response.raise_for_status()
            channels = response.json()
            categories = {}
            for channel in channels:
                if channel['type'] == 4:  
                    categories[channel['id']] = {'name': channel['name'], 'channels': []}
            for channel in channels:
                if channel['type'] == 0:  
                    category_id = channel.get('parent_id')
                    if category_id:
                        categories[category_id]['channels'].append(channel)
            return categories
        except requests.exceptions.RequestException as e:
            print(e)
            return {}

    def fetch_dm_channels(self):
        try:
            response = requests.get(base_url + 'users/@me/channels', headers={'Authorization': bot_token})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(e)
            return []

    def fetch_channel_messages(self, channel_id):
        try:
            response = requests.get(base_url + f'channels/{channel_id}/messages', headers={'Authorization': bot_token})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(e)
            return []

    def print_servers(self, servers):
        print("Available servers:")
        for index, server in enumerate(servers, 1):
            print(f"{index}. {server['name']}")
            if index % 25 == 0:
                input("Press Enter to view more servers...")
                os.system('cls' if os.name == 'nt' else 'clear')

    def print_categories(self, categories):
        print("Available categories:")
        for index, (category_id, category) in enumerate(categories.items(), 1):
            print(f"{index}. {category['name']}")
            if index % 25 == 0:
                input("Press Enter to view more categories...")
                os.system('cls' if os.name == 'nt' else 'clear')

    def print_channels(self, channels):
        print("Available channels:")
        for index, channel in enumerate(channels, 1):
            print(f"{index}. {channel['name']}")
            if index % 25 == 0:
                input("Press Enter to view more channels...")
                os.system('cls' if os.name == 'nt' else 'clear')

    def print_dm_channels(self, dm_channels):
        print("Available DM channels:")
        for index, channel in enumerate(dm_channels, 1):
            recipients = ", ".join([recipient['username'] for recipient in channel['recipients']])
            if len(channel['recipients']) > 1:
                print(f"{index}. Group Chat: {recipients}")
            else:
                print(f"{index}. {recipients}")
            if index % 25 == 0:
                input("Press Enter to view more DM channels...")
                os.system('cls' if os.name == 'nt' else 'clear')

    def print_messages(self):
        if self.messages:
            print("Recent messages:")
            for message in reversed(self.messages):
                print(f"{message['author']['username']}: {message['content']}")
        else:
            print("No messages in this channel.")

    def send_message(self, content):
        if self.selected_channel:
            try:
                response = requests.post(
                    base_url + f'channels/{self.selected_channel["id"]}/messages',
                    headers={'Authorization': bot_token},
                    json={'content': content}
                )
                response.raise_for_status()
                print("Message sent successfully.")
                self.messages = self.fetch_channel_messages(self.selected_channel['id'])
                self.print_messages()
            except requests.exceptions.RequestException as e:
                print(e)
        else:
            print("No channel selected. Please select a channel first.")

    def select_server(self):
        servers = self.fetch_bot_servers()
        if servers:
            self.print_servers(servers)
            choice = int(input("Enter the number of the server: "))
            if 1 <= choice <= len(servers):
                self.selected_server = servers[choice - 1]
            else:
                print("Invalid choice.")
        else:
            print("No servers found.")

    def select_category(self, categories):
        self.print_categories(categories)
        choice = int(input("Enter the number of the category: "))
        if 1 <= choice <= len(categories):
            category_id = list(categories.keys())[choice - 1]
            self.selected_channel = categories[category_id]['channels']
        else:
            print("Invalid choice.")

    def select_channel(self, channels):
        self.print_channels(channels)
        choice = int(input("Enter the number of the channel: "))
        if 1 <= choice <= len(channels):
            self.selected_channel = channels[choice - 1]
        else:
            print("Invalid choice.")

    def select_dm_channel(self, dm_channels):
        self.print_dm_channels(dm_channels)
        choice = int(input("Enter the number of the DM channel: "))
        if 1 <= choice <= len(dm_channels):
            self.selected_channel = dm_channels[choice - 1]
        else:
            print("Invalid choice.")

    def send_messages(self):
        while self.running:
            action = input("Enter 's' to select server, 'cat' to select category, 'c' to select channel, 'dm' to select DM channel, 'm' to send message, or 'exit' to stop: ")
            if action.lower() == 's':
                self.select_server()
            elif action.lower() == 'cat':
                if self.selected_server:
                    categories = self.fetch_server_channels(self.selected_server['id'])
                    self.select_category(categories)
                else:
                    print("No server selected. Please select a server first.")
            elif action.lower() == 'c':
                if self.selected_channel:
                    self.select_channel(self.selected_channel)
                else:
                    print("No category selected. Please select a category first.")
            elif action.lower() == 'dm':
                dm_channels = self.fetch_dm_channels()
                if dm_channels:
                    self.select_dm_channel(dm_channels)
                else:
                    print("No DM channels found.")
            elif action.lower() == 'm':
                message = input("Enter your message: ")
                self.send_message(message)
            elif action.lower() == 'exit':
                self.stop()

def main():
    client = DiscordClient()
    client.start()

if __name__ == "__main__":
    main()
