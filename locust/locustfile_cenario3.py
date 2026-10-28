from locust import HttpUser, TaskSet, between, task

# Requisição sem resposta em 10 s conta como falha (critério de erro da calibragem)
TIMEOUT_S = 10


class UserTasks(TaskSet):
    @task
    def index(self):
        # Cenário 3: Blog post com uma imagem de 300KB
        self.client.get("/?p=3", name="/?p=3 (Imagem 300KB)", timeout=TIMEOUT_S)


class WebsiteUser(HttpUser):
    tasks = [UserTasks]
    wait_time = between(0.1, 0.5)
