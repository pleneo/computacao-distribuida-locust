from locust import HttpLocust, TaskSet, task


class UserTasks(TaskSet):
    @task
    def post_imagem_300kb(self):
        # Cenário 3: Blog post com uma imagem de 300KB
        self.client.get("/?p=3", name="Cenario 3 - Post HTML (?p=3)")
        self.client.get("/wp-content/uploads/img_300kb.bmp", name="Cenario 3 - Imagem 300KB")


class WebsiteUser(HttpLocust):
    task_set = UserTasks
    min_wait = 1000
    max_wait = 3000
