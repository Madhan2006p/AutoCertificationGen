import time

def long_task(data):
    """
    Simulate a long running task.
    In a real application, this would be your heavy processing logic.
    """
    print(f"Task started: {data}")
    time.sleep(10)  # Simulate delay
    result = f"Processed {data}"
    print(f"Task finished: {result}")
    return result
