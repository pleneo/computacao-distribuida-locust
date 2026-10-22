from locust import HttpLocust, TaskSet, task


class UserTasks(TaskSet):
    @task
    def post_imagem_1mb(self):
        # Cenário 1: Blog post com uma imagem de aproximadamente 1MB
        self.client.get("/?p=1", name="Cenario 1 - Post HTML (?p=1)")
        self.client.get("/wp-content/uploads/img_1mb.bmp", name="Cenario 1 - Imagem 1MB")


class WebsiteUser(HttpLocust):
    task_set = UserTasks
    min_wait = 1000
    max_wait = 3000
