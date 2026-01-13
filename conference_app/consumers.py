import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class chatConsumer(WebsocketConsumer):
    def connect(self):
        data = {
            'type': 'Connected',
            'message': 'Connected to chat'
        }
        
        self.room_group_name = 'a'
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()
        self.send(text_data=json.dumps(data))


    def receive(self, text_data = None, bytes_data = None):
        data = json.loads(text_data)
        # message = data['message']
        data = {
            'type': 'chat_message',
            'message': data['message']
        }
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            data
        )
        print(f"group: {self.room_group_name}, channel: {self.channel_name}, Received data: {text_data}")
    

    def chat_message(self, event):
        message = event['message']
        data = {
            'type': 'chat_message',
            'message': message
        }
        self.send(text_data=json.dumps(data))


    def disconnect(self, code):
        print(f"Disconnected with code: {code}")
