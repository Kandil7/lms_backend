# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the functions below or add your own.
# Learn more at https://firebase.google.com/docs/functions

from firebase_functions import https_fn, options
from firebase_admin import initialize_app
import logging
import json

initialize_app()
logger = logging.getLogger(__name__)

@https_fn.on_request(
    cors=options.CorsOptions(
        cors_origins=["*"],
        cors_methods=["POST"],
    )
)
def sendEmail(req: https_fn.Request) -> https_fn.Response:
    """
    HTTP Cloud Function to send emails.
    Expected payload: {"to": "...", "subject": "...", "body": "..."}
    """
    if req.method != "POST":
        return https_fn.Response("Only POST requests are accepted", status=405)

    try:
        data = req.get_json()
        to_email = data.get("to")
        subject = data.get("subject")
        body = data.get("body")

        if not all([to_email, subject, body]):
            return https_fn.Response(
                json.dumps({"error": "Missing required fields: to, subject, body"}),
                status=400,
                mimetype="application/json"
            )

        # In a real scenario, integrate with an email provider (SendGrid, Resend, etc.)
        # For now, we log the email request.
        logger.info(f"Sending email to: {to_email} | Subject: {subject}")
        
        # Mock success response
        return https_fn.Response(
            json.dumps({
                "success": True, 
                "message_id": "mock-firebase-msg-id-12345",
                "message": "Email request received and logged"
            }),
            status=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Error processing email request: {str(e)}")
        return https_fn.Response(
            json.dumps({"error": "Internal server error"}),
            status=500,
            mimetype="application/json"
        )
