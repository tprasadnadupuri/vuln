import subprocess
import time
import uuid
import requests


def run(cmd: list[str]):
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def wait_for_health(url: str, attempts: int = 10, delay: int = 2):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            print(f"Health check attempt {attempt}: {url}")
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            return r
        except Exception as e:
            last_error = e
            time.sleep(delay)
    raise last_error


def validate():
    run(["docker", "build", "-t", "user-crud-lab:candidate", "."])

    container = subprocess.Popen([
        "docker", "run", "--rm", "-p", "9092:9090", "user-crud-lab:candidate"
    ])

    try:
        r = wait_for_health("http://localhost:9092/health")
        print("Health successful:", r.json())

        unique_email = f"tulasi-{uuid.uuid4().hex[:8]}@example.com"
        payload = {"name": "Tulasi", "email": unique_email}

        create_resp = requests.post("http://localhost:9092/users", json=payload, timeout=5)
        print("Create response status:", create_resp.status_code)
        print("Create response body:", create_resp.text)
        create_resp.raise_for_status()
        created_user = create_resp.json()
        print("Create user successful:", created_user)

        list_resp = requests.get("http://localhost:9092/users", timeout=5)
        list_resp.raise_for_status()
        users = list_resp.json()
        print("List users successful:", users)

        user_id = created_user["id"]
        get_resp = requests.get(f"http://localhost:9092/users/{user_id}", timeout=5)
        get_resp.raise_for_status()
        print("Get user successful:", get_resp.json())

        print("Validation successful")

    finally:
        container.terminate()
        try:
            container.wait(timeout=5)
        except subprocess.TimeoutExpired:
            container.kill()


if __name__ == "__main__":
    validate()
