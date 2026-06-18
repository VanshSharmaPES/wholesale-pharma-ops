"""
Expiry Return Reminder System - WhatsApp Messenger and Logger

Handles sending of WhatsApp notifications to retailers using the UltraMsg API
and logging sent reminders to prevent duplicates.
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

def normalize_phone(phone: str) -> str:
    """Strip leading + from phone number for UltraMsg compatibility.
    Input: +919876543210 or 919876543210
    Output: 919876543210"""
    phone_str = str(phone).strip()
    if phone_str.startswith("+"):
        return phone_str[1:]
    return phone_str

def send_whatsapp_reminder(to_number: str, message: str) -> str:
    """
    Sends a WhatsApp message reminder to a retailer using the UltraMsg API.
    
    Args:
        to_number (str): The destination phone number.
        message (str): The reminder text to send.
        
    Returns:
        str: The message ID from the UltraMsg response on success.
        
    Raises:
        ValueError: If configuration is missing.
        requests.RequestException: If the API request fails.
    """
    to_number = normalize_phone(to_number)
    
    # Check if we should mock the WhatsApp sending process
    mock_whatsapp = os.getenv("MOCK_WHATSAPP", "false").lower() == "true"
    if mock_whatsapp:
        mock_id = f"mock_msg_{int(requests.utils.time.time())}"
        logger.info(f"[MOCK WHATSAPP] Mock sending to {to_number}. Msg ID: {mock_id}. Message: {message}")
        return mock_id
        
    instance_id = os.getenv("ULTRAMSG_INSTANCE_ID")
    token = os.getenv("ULTRAMSG_TOKEN")
    
    if not instance_id or not token:
        error_msg = "UltraMsg configuration is incomplete. Please check ULTRAMSG_INSTANCE_ID and ULTRAMSG_TOKEN in your .env file."
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    payload = {
        "token": token,
        "to": to_number,
        "body": message
    }
    
    logger.info(f"Sending WhatsApp message via UltraMsg to {to_number}...")
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        
        res_data = response.json()
        # UltraMsg typically returns a JSON containing {"sent": "true", "message": "ok", "id": <id>}
        msg_id = str(res_data.get("id", "unknown"))
        logger.info(f"Successfully sent WhatsApp message. UltraMsg ID: {msg_id}")
        return msg_id
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message via UltraMsg to {to_number}: {str(e)}")
        raise
