import json
import os

jsonPath = "test\\savesList.json"

def default_dir_initializer():
  # open/read config
  with open(jsonPath, 'r') as f:
    configObj = json.load(f)
  # check if default is initialized
  if configObj['default_dir_path'] == "":
    current_dir = os.path.dirname(os.path.realpath(__file__))
    default_relative_path = os.path.join(current_dir, 'test')
  with open(jsonPath, 'w') as f:
    configObj = json.load(f)
    configObj['default_dir_path'] = default_relative_path
    json.dump(configObj, f, indent=2)
  return default_relative_path
# default_dir_initializer()

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
# update_config('path/')
