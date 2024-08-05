import subprocess
import log

def task_exists(task_name="APOD"):
  try: 
    result = subprocess.run(['schtasks', '/Query', '/TN', task_name], capture_output=True, text=True)
    if "ERROR: The system cannot find the file specified." in result.stderr:
      return False
    return True
  except Exception as e:
    log.to_errlog(f"task_exists error: {e}")
    return False

def create_task(task_action, task_name="APOD"):
  try:
    subprocess.run(['schtasks', '/Create', '/TN', task_name, '/TR', f'"{task_action}"', '/SC', 'DAILY'], check=True)
    print("APOD task CREATED")
  except subprocess.CalledProcessError as e:
    print(f"FAILED to create APOD task: {e}")