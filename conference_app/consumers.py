import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import datetime
from . import mongo_config
# import redis

# r = redis.Redis(host='localhost', port=6379, decode_responses=True)

class chatConsumer(WebsocketConsumer):
    def connect(self):
        session_data = self.scope['session']

        self.room_group_name = session_data['group']
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

        data_to_send = {
            'type': 'connected',
            'message': 'Connected to chat',
        }
        self.send(text_data=json.dumps(data_to_send))
        print(f"Connected to group: {self.room_group_name}")


    def receive(self, text_data = None, bytes_data = None):
        session_data = self.scope['session']
        text_data_json = json.loads(text_data)

        data_to_send = {
            'type': 'chat_message',
            'name': session_data['nickname'],
            'message': text_data_json['message'],
            'time':  datetime.datetime.now().strftime("%d %b, %Y %I:%M %p"),
        }

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            data_to_send
        )
        print(f"group: {self.room_group_name}, Received data: {data_to_send}")
        

    def chat_message(self, event):
        data = {
            'type': 'chat_message',
            'name': event['name'],
            'message': event['message'],
            'time':  event['time'],
        }
        self.send(text_data=json.dumps(data))


    def disconnect(self, code):
        self.send(text_data=json.dumps({
            'type': 'disconnected',
            'message': 'Disconnected from chat',
        }))
        self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"Disconnected from group: {self.room_group_name}")

        print(f"Disconnected with code: {code}")


class cheakUsernameConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def receive(self, text_data = None, bytes_data = None):
        text_data_json = json.loads(text_data)
        username = text_data_json['username']

        data_to_send = {
            'type': 'username_check',
            'is_available': False,
        }
        usersCollection = mongo_config.get_users_collection()

        is_availabe = usersCollection.find_one({"username": username})

        if is_availabe:
            data_to_send['is_available'] = False
        else:
            data_to_send['is_available'] = True

        self.send(text_data=json.dumps(data_to_send))