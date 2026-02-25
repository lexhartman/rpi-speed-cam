import requests
import logging

class NotificationManager:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("NotificationManager")

    def update_config(self, config):
        self.config = config

    def notify(self, message, image_path=None):
        if not self.config.get("enabled", False):
            return

        if self.config.get("telegram", {}).get("enabled"):
            self.send_telegram(message, image_path)
        if self.config.get("pushover", {}).get("enabled"):
            self.send_pushover(message, image_path)
        if self.config.get("webhook", {}).get("enabled"):
            self.send_webhook(message, image_path)

    def send_telegram(self, message, image_path=None):
        try:
            token = self.config["telegram"]["bot_token"]
            chat_id = self.config["telegram"]["chat_id"]
            if not token or not chat_id:
                return

            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": message}
            requests.post(url, data=data, timeout=10)
            
            if image_path:
                url_photo = f"https://api.telegram.org/bot{token}/sendPhoto"
                with open(image_path, "rb") as f:
                    files = {"photo": f}
                    requests.post(url_photo, data={"chat_id": chat_id}, files=files, timeout=30)
        except Exception as e:
            self.logger.error(f"Telegram error: {e}")

    def send_pushover(self, message, image_path=None):
        try:
            user_key = self.config["pushover"]["user_key"]
            api_token = self.config["pushover"]["api_token"]
            if not user_key or not api_token:
                return

            url = "https://api.pushover.net/1/messages.json"
            data = {"token": api_token, "user": user_key, "message": message}
            
            files = None
            if image_path:
                files = {"attachment": ("image.jpg", open(image_path, "rb"), "image/jpeg")}
            
            requests.post(url, data=data, files=files, timeout=30)
        except Exception as e:
            self.logger.error(f"Pushover error: {e}")

    def send_webhook(self, message, image_path=None):
        try:
            url = self.config["webhook"]["url"]
            method = self.config["webhook"].get("method", "POST")
            if not url:
                return
            
            # Simple webhook payload
            data = {"message": message, "has_image": bool(image_path)}
            # Typically webhooks might not support direct file upload easily unless specified
            # For now just send metadata
            
            if method == "POST":
                requests.post(url, json=data, timeout=10)
            else:
                requests.get(url, params=data, timeout=10)
        except Exception as e:
            self.logger.error(f"Webhook error: {e}")
