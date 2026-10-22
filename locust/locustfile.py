import os
from locust import HttpUser, TaskSet, between, task

SCENARIO = os.environ.get("SCENARIO", "1")


class UserTasks(TaskSet):
    @task
    def index(self):
        if SCENARIO == "1":
            # Cenário 1: Blog post com uma imagem de aproximadamente 1MB
            self.client.get("/?p=1", name="/?p=1 (Imagem 1MB)")
        elif SCENARIO == "2":
            # Cenário 2: Blog post com um texto de aproximadamente 400KB
            self.client.get("/?p=2", name="/?p=2 (Texto 400KB)")
        elif SCENARIO == "3":
            # Cenário 3: Blog post com uma imagem de 300KB
            self.client.get("/?p=3", name="/?p=3 (Imagem 300KB)")


class WebsiteUser(HttpUser):
    tasks = [UserTasks]
    wait_time = between(0.1, 0.5)
