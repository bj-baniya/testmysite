from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time
scheduler = BackgroundScheduler()
def start():
    scheduler.start()
def add_new_job(roomname,context):    
    scheduler.add_job(sendDeployments, 'interval',args=[roomname,context] ,seconds=10,id=roomname)
def sendDeployments(roomname,context):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        roomname,
        {'type': 'check_score', 'context': context}
    )
def stop(roomname):
    scheduler.remove_job(roomname)