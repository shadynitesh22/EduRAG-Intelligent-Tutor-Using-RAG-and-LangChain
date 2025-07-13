from celery import shared_task

def dummy_send_webhook(*args, **kwargs):
    pass
 
@shared_task
def send_webhook_async(event_type, data):
    # TODO: Implement actual webhook sending logic
    dummy_send_webhook(event_type, data) 

def dummy_send_webhook(*args, **kwargs):
    pass
 
@shared_task
def send_webhook_async(event_type, data):
    # TODO: Implement actual webhook sending logic
    dummy_send_webhook(event_type, data) 