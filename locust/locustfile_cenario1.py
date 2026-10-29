from locust import HttpUser, between, task

# Requisição sem resposta em 10 s conta como falha (critério de erro da calibragem)
TIMEOUT_S = 10


class WebsiteUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def index(self):
        # Cenário 1: Blog post com uma imagem de aproximadamente 1MB
        self.client.get("/?p=1", name="/?p=1 (Imagem 1MB)", timeout=TIMEOUT_S)
