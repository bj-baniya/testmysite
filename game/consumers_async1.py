# chat/consumers.py
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import psycopg2
from game.postgrehelper import PostgreHelp
import time
import asyncio

class AsyncChatConsumer(AsyncWebsocketConsumer):
    numberofuser = 3
    async def connect(self):
        
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        #self.openstate = True
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )


        await self.accept()
        '''
        self.send(text_data=json.dumps({
                    'message': count
         }))
        async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': 'member added'
                    }
                )
        '''
    async def disconnect(self, close_code):
        # Leave room group
       await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        
        text_data_json = json.loads(text_data)
        #message = text_data_json['message']
        state = text_data_json['state']
        if state =='connect':
            postgreHelp = PostgreHelp()
            count = await  postgreHelp.GetUserCount('roomname_' + self.room_name,self.numberofuser)
            context = 'connection'
            # response to a  new connection with the number of users and
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'client_broadcast',
                    'message': count,
                    'context':context,
                    'numberofuser':self.numberofuser
                }
            )
            print(self.numberofuser)
            # if the group is full then start the quiz
            if count== self.numberofuser: # and self.openstate == True:
                context = 'startgame'    
                await self.Question(context,'set')
                print(self.numberofuser)
                #asyncio.run(self.Timer(context))
                   
                #self.openstate = False
            '''
            if self.openstate == False:
                context = 'runninggame'
                self.Question(context,'get')
            '''
        elif state == 'answer':
            answer = text_data_json['answer']
            self.send(text_data=json.dumps({
                                'message': answer
            }))
   
    async def  Timer(self,context):
        self.countdown(10)
        self.Question(context,'set')

    # Receive message from room group
    async def client_broadcast(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': event['message'],
            'context': event['context'],
            'numberofuser': event['numberofuser']
        }))

    async def client_broadcast_question(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'context': event['context'],
            'question': event['question'],
            'options': event['options']
        }))
    
    async def Question(self, context, status):
        
        postgreHelp = PostgreHelp()
        #groupName ='asgi::group:chat_' + self.room_name + '_ques'
        groupName ='roomname_' + self.room_name
        que = None
        if status =='set':
            que = await postgreHelp.SetQuestion(groupName)
        else:
            que = await postgreHelp.GetQuestion(groupName)
        if  que is not None:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'client_broadcast_question',
                    'question': que[0],
                    'context':context,
                    'options':que[1]
                }
            )


    '''
    async def broadcast(self, msg):
        self.send(text_data=json.dumps({
                'message': event['message'],
            }))
    '''
    async def countdown(self ,t):
        while t:
            mins, secs = divmod(t, 60)      
            time.sleep(1)
            t -= 1