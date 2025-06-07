import requests
def send_notification(topic, message):
    requests.post(
        f"https://ntfy.sh/{topic}",
        data=f"{message}".encode(encoding='utf-8')
    )