from locust import HttpUser, TaskSet, between, task


class UserTasks(TaskSet):
    @task
    def index(self):
        # Cenário 3: Blog post com uma imagem de 300KB
        self.client.get("/?p=3", name="/?p=3 (Imagem 300KB)")


class WebsiteUser(HttpUser):
    tasks = [UserTasks]
    wait_time = between(0.1, 0.5)
