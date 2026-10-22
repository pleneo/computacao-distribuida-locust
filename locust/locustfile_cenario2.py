from locust import HttpUser, TaskSet, between, task


class UserTasks(TaskSet):
    @task
    def index(self):
        # Cenário 2: Blog post com um texto de aproximadamente 400KB
        self.client.get("/?p=2", name="/?p=2 (Texto 400KB)")


class WebsiteUser(HttpUser):
    tasks = [UserTasks]
    wait_time = between(0.1, 0.5)
