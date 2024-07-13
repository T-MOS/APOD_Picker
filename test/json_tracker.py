import json
import os
from dataclasses import dataclass

jsonPath = "config.json"

# def default_dir_initializer():
#   # open/read config
#   with open(jsonPath, 'r') as f:
#     configObj = json.load(f)
#   # check if default is initialized
#   if configObj['default_dir_path'] == "":
#     current_dir = os.path.dirname(os.path.realpath('apod_picker.py'))
#     default_relative_path = os.path.join(current_dir, 'test')
#     configObj['default_dir_path'] = default_relative_path
#     with open(jsonPath, 'w') as out:
#       json.dump(configObj, out, indent=2)
#       print(configObj['default_dir_path'])
#   return default_relative_path
# default_dir_initializer()

# def update_config(saved):
#   with open(jsonPath, 'r') as f:
#     configObj = json.load(f)
  
#   paths = configObj['paths']

#   if len(paths) >= configObj['keep']:
#     oldest = configObj['paths'][-1]
#     if os.path.exists(oldest):
#       os.remove(oldest)
#   paths.insert(0,saved)
#   configObj['paths']=paths[:5]

#   with open(jsonPath, 'w') as out:
#     json.dump(configObj, out, indent=2)
# # update_config('path/')

def events():
  with open(jsonPath, 'r') as f:
    configObj = json.load(f)
  
  @dataclass
  class eventItem:
    date: int
    url: str
    dupCheck_result: tuple
  
  @dataclass
  class logs:
    number: int
    eventInfo: eventItem

  logsObj = configObj['logs']
  print(logsObj[1])

events()