import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import datetime
from . import values
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

class chatConsumer(WebsocketConsumer):
    def connect(self):
        
        session_data = self.scope['session']
        self.room_group_name = session_data['group']
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        values.member_count[self.room_group_name] += 1
        r.hset("members_count", mapping = {
            self.room_group_name: 
        })
        data_to_send = {
            'type': 'connected',
            'message': 'Connected to chat',
        }
        self.send(text_data=json.dumps(data_to_send))
        print(f"Connected to group: {self.room_group_name}, Total members: {values.member_count[self.room_group_name]}")


    def receive(self, text_data = None, bytes_data = None):
        session_data = self.scope['session']
        text_data_json = json.loads(text_data)

        data_to_send = {
            'type': 'chat_message',
            'name': session_data['name'],
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
        values.member_count[self.room_group_name] -= 1
        print(f"Disconnected from group: {self.room_group_name}, Total members: {values.member_count.get(self.room_group_name, 0)}")
        
        if values.member_count[self.room_group_name] <= 0:
            del values.member_count[self.room_group_name]
            print(f"Deleted group: {self.room_group_name}")

        print(f"Disconnected with code: {code}")
