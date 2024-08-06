import subprocess
import log

# Windows: scheduler
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

# Mac: cron
def cron_job(exe_path):
  from os import system
  #passthrough script v1
  script = f"""
      do shell script "
      cron_job_exists=$(crontab -l 2>/dev/null| grep -c 'APOD')
      if [$cron_job_exists -eq 0]; then
        (crontab -l 2>/dev/null; echo '0 10,20 * * * {exe_path} # APOD')
      fi
      "
      """
  system(f"/usr/bin/osascript -e '{script}'")
  # passthrough script v2
  # script = f"""
  #     cron_job_exists=$(crontab -l 2>/dev/null| grep -c 'APOD')
  #     if [$cron_job_exists -eq 0]; then
  #       (crontab -l 2>/dev/null; echo '0 12 * * * {exe_path} # APOD')
  #     fi
  #     """
  # 0system(f"/usr/bin/osascript -e '{script}'")
