import requests
import json
from typing import Dict, Any, List
from django.conf import settings
import logging
import hashlib
import hmac

logger = logging.getLogger('rag_tutor')

class WebhookAdapter:
    def __init__(self):
        self.webhook_secret = settings.WEBHOOK_SECRET
        self.webhook_endpoints = [
            endpoint.strip() 
            for endpoint in settings.WEBHOOK_ENDPOINTS 
            if endpoint.strip()
        ]
    
    def send_webhook(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Send webhook to configured endpoints"""
        if not self.webhook_endpoints:
            logger.info("No webhook endpoints configured")
            return True
        
        payload = {
            'event_type': event_type,
            'data': data,
            'timestamp': self._get_timestamp()
        }
        
        success = True
        for endpoint in self.webhook_endpoints:
            try:
                self._send_to_endpoint(endpoint, payload)
            except Exception as e:
                logger.error(f"Failed to send webhook to {endpoint}: {str(e)}")
                success = False
        
        return success
    
    def _send_to_endpoint(self, endpoint: str, payload: Dict[str, Any]):
        """Send webhook to specific endpoint"""
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': self._generate_signature(payload)
        }
        
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        logger.info(f"Webhook sent successfully to {endpoint}")
    
    def _generate_signature(self, payload: Dict[str, Any]) -> str:
        """Generate webhook signature"""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def _get_timestamp(self) -> int:
        """Get current timestamp"""
        import time
        return int(time.time())
    
    def verify_signature(self, payload: str, signature: str) -> bool:
        """Verify incoming webhook signature"""
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        expected_signature = f"sha256={expected_signature}"
        
        return hmac.compare_digest(signature, expected_signature)
