# chat/consumers.py
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
import psycopg2
from game.postgrehelper import PostgreHelp
import time
import asyncio
from . import scheduler
  
class ChatConsumer(WebsocketConsumer):
    numberofuser = 3
    groups = ["broadcast"]
    def connect(self):
        self.user = self.scope["user"]
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        #self.openstate = True 
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
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
    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        #message = text_data_json['message']
        state = text_data_json['state']
        if state =='connect':
            postgreHelp = PostgreHelp()
            username = text_data_json['username']
            count =  postgreHelp.GetUserCount(self.room_name,self.numberofuser,username)
            context = 'connection'
            if count <= self.numberofuser: 
                # response to a  new connection with the number 
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'client_broadcast',
                        'message': count,
                        'context':context,
                        'numberofuser':self.numberofuser
                    }
                )
            
            # if the group is full then start the quiz
                if count== self.numberofuser: # and self.openstate == True:
                    context = 'startgame'    
                    scheduler.add_new_job(self.room_group_name,context)
            #give user now allowed    
            else:
                self.send(text_data=json.dumps({
                    context: 'rooomfull'
                }))
                async_to_sync(self.channel_layer.group_discard)(
                    self.room_group_name,
                    self.channel_name
                )

            ''' 
            if self.openstate == False:
                context = 'runninggame'
                self.Question(context,'get')
            '''
        elif state == 'answer':
            answer = text_data_json['answer']
            username = text_data_json['userName']
            postgreHelp = PostgreHelp()
            postgreHelp.AnswerUpdate(self.room_name, username, answer)
   
    def  Timer(self,context):
        self.countdown(10)
        self.Question(context,'set')

    # Receive message from room group
    def client_broadcast(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': event['message'],
            'context': event['context'],
            'numberofuser': event['numberofuser']
        }))

    def client_broadcast_question(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'context': event['context'],
            'question': event['question'],
            'options': event['options']
        }))
    
    def Question(self, context, status):
        
        postgreHelp = PostgreHelp()
        #groupName ='asgi::group:chat_' + self.room_name + '_ques'
        groupName = self.room_name
        que = None
        if status =='set':
            que = postgreHelp.SetQuestion(groupName)
        else:
            que = postgreHelp.GetQuestion(groupName)
        if  que is not None:
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'client_broadcast_question',
                    'question': que[0],
                    'context':context,
                    'options':que[1]
                }
            )

    def check_score(self,event):
        # Receive message from room group
        context = event['context']
        print(context)
        print(self.room_group_name)
        self.Question(context,'set')

        postgreHelp = PostgreHelp()
        answers, correct_answer = postgreHelp.GetGroupAnswer(self.room_name)
        if correct_answer is not None and len(correct_answer) > 0:
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'client_broadcast_result',
                    'answer': correct_answer,
                    'stat':answers
                }
            )