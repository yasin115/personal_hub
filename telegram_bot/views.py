"""
Webhook view for Telegram bot (if you prefer webhook over long polling).
For most cases, use management command runbot instead.
"""
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import asyncio

# You can expand this to process updates without polling
@csrf_exempt
def telegram_webhook(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")
    
    try:
        update = json.loads(request.body)
        # TODO: Process update here or queue it
        # For simplicity, recommend using polling via runbot command
        print("Received Telegram update:", update.get('update_id'))
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
