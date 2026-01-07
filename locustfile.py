from locust import HttpUser, task, between

class CertUser(HttpUser):
    # wait_time = between(1, 2) simulates users clicking reasonably fast
    wait_time = between(1, 2) 

    @task
    def download_cert(self):
        # NOTE: Use valid roll_no and event for accurate test
        roll_no = "test_roll" 
        event = "test_event"
        self.client.get(f"/download?roll={roll_no}&event={event}")

    @task(3)
    def visit_home(self):
        self.client.get("/")
