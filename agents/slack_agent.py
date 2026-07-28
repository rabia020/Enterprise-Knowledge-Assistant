import requests

def slack_agent(task):

    requests.post(
        "http://localhost:5678/webhook/send-slack",
        json={
            "task": task
        }
    )