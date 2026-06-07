import logging
import os
import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Track initialization
firebase_initialized = False

def init_firebase() -> bool:
    """Initializes the Firebase Admin SDK if configurations are present."""
    global firebase_initialized
    if firebase_initialized:
        return True
        
    try:
        # Check if credential file exists
        cred_path = settings.FCM_CREDENTIALS_JSON or "app/google-services-sdk.json"
        
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            firebase_initialized = True
            logger.info("Firebase Admin SDK successfully initialized.")
            return True
        elif settings.FCM_SERVER_KEY:
            # Fallback check or logging
            logger.warning("FCM_SERVER_KEY is defined but credentials JSON is missing. Operating in Mock mode.")
        else:
            logger.warning("FCM credentials file not found. Operating in mock notification mode.")
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        
    return False

def send_push_notification(device_token: str, title: str, body: str, data: dict = None) -> bool:
    """Dispatches a push notification to a device token using Firebase Cloud Messaging."""
    # Ensure init
    init_firebase()
    
    if data is None:
        data = {}
        
    # Coerce all data values to string for FCM compliance
    fcm_data = {k: str(v) for k, v in data.items()}
    
    if not firebase_initialized:
        logger.info(
            f"[MOCK PUSH NOTIFICATION]\n"
            f"To Token: {device_token[:15]}...\n"
            f"Title   : {title}\n"
            f"Body    : {body}\n"
            f"Payload : {fcm_data}\n"
        )
        return True

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=fcm_data,
            token=device_token,
        )
        # Send message
        response = messaging.send(message)
        logger.info(f"FCM notification successfully dispatched. Message ID: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to dispatch FCM notification to {device_token[:15]}...: {e}")
        return False
