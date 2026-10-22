from locust import HttpLocust, TaskSet, task


class UserTasks(TaskSet):
    @task
    def post_texto_400kb(self):
        # Cenário 2: Blog post com um texto de aproximadamente 400KB
        self.client.get("/?p=2", name="Cenario 2 - Post Texto 400KB (?p=2)")


class WebsiteUser(HttpLocust):
    task_set = UserTasks
    min_wait = 1000
    max_wait = 3000
