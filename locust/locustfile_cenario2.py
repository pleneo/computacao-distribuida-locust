from locust import HttpUser, TaskSet, between, task

# Requisição sem resposta em 10 s conta como falha (critério de erro da calibragem)
TIMEOUT_S = 10


class UserTasks(TaskSet):
    @task
    def index(self):
        # Cenário 2: Blog post com um texto de aproximadamente 400KB
        self.client.get("/?p=2", name="/?p=2 (Texto 400KB)", timeout=TIMEOUT_S)


class WebsiteUser(HttpUser):
    tasks = [UserTasks]
    wait_time = between(0.1, 0.5)
