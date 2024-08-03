import subprocess
from apod_picker_main import to_errlog

def task_exists(task_name="APOD"):
  try: 
    result = subprocess.run(['schtasks', '/Query', '/TN', task_name], capture_output=True, text=True)
    if "ERROR: The system cannot find the file specified." in result.stderr:
      return False
    return True
  except Exception as e:
    to_errlog(f"task_exists error: {e}")
    return False

def create_task(task_name="APOD", task_action, task_trigger):
  try:
    subprocess.run(['schtasks', '/Create', '/TN', task_name, '/TR', task_action, '/SC', "DAILY", 'RI', 1], check=True)
    print("APOD task CREATED")
  except subprocess.CalledProcessError as e:
    print(f"FAILED to create APOD task: {e}")

if task_exists():
  print("APOD task found")
else:
  create_task()
  print("no task")