import json
import os

jsonPath = "test\\savesList.json"

def update_config(saved):
  with open(jsonPath, 'r') as f:
    configObj = json.load(f)
  
  paths = configObj['paths']

  if len(paths) >= configObj['keep']:
    oldest = configObj['paths'][-1]
    if os.path.exists(oldest):
      os.remove(oldest)
  paths.insert(0,saved)
  configObj['paths']=paths[:5]

  with open(jsonPath, 'w') as out:
    json.dump(configObj, out, indent=2)

update_config('path/newest')
