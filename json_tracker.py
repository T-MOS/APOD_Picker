import json
import os

jsonPath = 'savesList.json'

def update_saves(saved):
  with open(jsonPath, 'r') as f:
    savesObj = json.load(f)

  if len(savesObj['paths']) == savesObj['max']:
    oldest = savesObj['paths'].pop()
    if os.path.exists(oldest):
      os.remove(oldest)
      print(f"deleted oldest file:{oldest}")
    else:
      print('no oldest')

  # recent_saves.insert(0,saved)
  # recent_saves = recent_saves[:5]

  # with open(jsonPath, 'w') as out:
  #   json.dump(recent_saves, out, indent=2)

update_saves('path/deletion_test.txt')
