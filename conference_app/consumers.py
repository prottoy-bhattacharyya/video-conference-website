import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import datetime

class chatConsumer(WebsocketConsumer):
    def connect(self):
        data_to_send = {
            'type': 'connected',
            'message': 'Connected to chat',
        }
        session_data = self.scope['session']
        self.room_group_name = session_data['group']
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        self.send(text_data=json.dumps(data_to_send))


    def receive(self, text_data = None, bytes_data = None):
        # TODO: Handle file upload
        session_data = self.scope['session']
        text_data_json = json.loads(text_data)


        data_type = text_data_json.get('type')
        if data_type == 'chat_message':
            data_to_send = {
                'type': 'chat_message',
                'name': session_data['name'],
                'message': text_data_json['message'],
                'time':  datetime.datetime.now().strftime("%d %b, %Y %I:%M %p"),
            }
        
        else:
            data_to_send = {
                'type': 'rtc_signal',
                'name': session_data['name'],
                'data': text_data_json,
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

    def rtc_signal(self, event):
        if event['name'] == self.scope['session']['name']:
            return  # Don't send the signal back to the sender
        data = event['data']
        self.send(text_data=json.dumps(data))

    def disconnect(self, code):
        self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"Disconnected with code: {code}")
