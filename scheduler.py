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

if task_exists():
  print("APOD task found")
else:
  print("no task")