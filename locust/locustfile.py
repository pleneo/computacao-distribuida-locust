import os
from locust import HttpLocust, TaskSet, task

SCENARIO = os.environ.get("SCENARIO", "1")


class UserTasks(TaskSet):
    @task
    def execute_scenario(self):
        if SCENARIO == "1":
            # Cenário 1: Blog post com uma imagem de aproximadamente 1MB
            self.client.get("/?p=1", name="Cenario 1 - Post HTML (?p=1)")
            self.client.get("/wp-content/uploads/img_1mb.bmp", name="Cenario 1 - Imagem 1MB")
        elif SCENARIO == "2":
            # Cenário 2: Blog post com um texto de aproximadamente 400KB
            self.client.get("/?p=2", name="Cenario 2 - Post Texto 400KB (?p=2)")
        elif SCENARIO == "3":
            # Cenário 3: Blog post com uma imagem de 300KB
            self.client.get("/?p=3", name="Cenario 3 - Post HTML (?p=3)")
            self.client.get("/wp-content/uploads/img_300kb.bmp", name="Cenario 3 - Imagem 300KB")


class WebsiteUser(HttpLocust):
    task_set = UserTasks
    min_wait = 1000
    max_wait = 3000
