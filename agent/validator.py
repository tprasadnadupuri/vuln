import subprocess
import time
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
        "docker", "run", "--rm", "-p", "8082:8081", "user-crud-lab:candidate"
    ])

    try:
        r = wait_for_health("http://localhost:8082/health")
        print("Validation successful:", r.json())
    finally:
        container.terminate()
        try:
            container.wait(timeout=5)
        except subprocess.TimeoutExpired:
            container.kill()


if __name__ == "__main__":
    validate()