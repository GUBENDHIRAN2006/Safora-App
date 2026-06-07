import logging

logger = logging.getLogger(__name__)

def trigger_sms_dispatch_log(session_id: str, contact_name: str, mobile_number: str, tracking_url: str) -> bool:
    """
    Logs backend-side acknowledgement of direct on-device SMS triggers.
    Since the application sends SMS natively via the Android phone, the mobile client
    notifies the backend of dispatch status. This logs the action for auditing.
    """
    message_body = (
        f"EMERGENCY ALERT: Safora user has triggered a critical health event. "
        f"Track their real-time GPS coordinates here: {tracking_url}"
    )
    
    logger.info(
        f"[NATIVE SMS DISPATCH TRIGGERED ON DEVICE]\n"
        f"Session ID    : {session_id}\n"
        f"Recipient     : {contact_name} ({mobile_number})\n"
        f"Message Body  : {message_body}\n"
    )
    return True
