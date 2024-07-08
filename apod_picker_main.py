import ctypes
import os
import platform
import re
import json
import random
import requests
from itertools import count # DELETE AFTER TESTING
from datetime import datetime
from io import BytesIO
from tkinter import messagebox

from bs4 import BeautifulSoup
from PIL import Image

def urlRandomizer():
  today = datetime.now()
#year
  y = random.randint(1995,today.year)
  if y < 100:
    yyStr = str(y)[-2:]
  else:
    yyStr = str(y)[-3:]
#month/day
  if yyStr in str(today.year)[-len(yyStr):]: #if y = now().year ...
    m = random.randint(1,today.month) #... mm value not > now().m
    d = random.randint(1,today.day)
  else:
    m = random.randint(1,12)
    d = random.randint(1,31)
  mmStr = str(m).zfill(2)
  ddStr = str(d).zfill(2)
#format -> output
  jointDate = yyStr+mmStr+ddStr
  urlFormatted = f"ap{jointDate}.html"
  return urlFormatted

# DELETE AFTER TESTING
calls = count(start=1)

def fetch_apod_data(use_random=False):
  # Send GET request to APOD; parse HTML w/ BeautifulSoup
  baseUrl = 'https://apod.nasa.gov/apod/'
  print(f'ran fetch()... {next(calls)} times') # DELETE AFTER TESTING
  try:
    if use_random:
      random_post = baseUrl + urlRandomizer()
      response = requests.get(random_post)
    else:
      response = requests.get(baseUrl)
    
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    img_tag = soup.find('img')
    
    while img_tag is None: # no usable image --> repeat w/ random
      try:
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
        img_tag = soup.find('img')
      except requests.RequestException as e:  
        messagebox.showerror("Error",f"{e}")
        fetch_apod_data(use_random=True)

    post_title = soup.find('b').text.strip() # Find image's title in: "<center> w/ child <b>"
    description = img_tag.find_next('p').text.strip() # Extract description text from: descendant <p>
    a = img_tag.find_parent('a') # Grab parent's href for full resolution (<a>[href] !== <img>[src])
    img_url = baseUrl + a['href'] # <- download/save from
    return img_url, description, post_title 
  except requests.RequestException as e:
    messagebox.showerror("Error",f"Failed to fetch APOD data: {e}")
    return None, None, None


def set_desktop_background(image_path):
  try:  
    if platform.system() == 'Linux':
      setterCommand = f'pcmanfm --set-wallpaper {image_path}'
      os.system(setterCommand)
    elif platform.system() == 'Windows':
      SPI_SETDESKWALLPAPER = 0x0014
      ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
    elif platform.system() == 'Darwin':
      script = f"""
      tell application "Finder"
        set desktop picture to POSIX file "{image_path}"
      end tell
      """
      os.system(f"/usr/bin/osascript -e '{script}'")
  except Exception as e:
    messagebox.showerror("Error", f"Failed to set the desktop background: {e}")

def sanitize_filename(input_string): #(post_title)
  unsanitized = input_string.strip() # remove lead/trail whitespace
  pattern1 = r'[\:*?"<>|]' # 1st RE for... disallowed chars
  rinsed = re.sub(pattern1, "", unsanitized)
  pattern2 = r'[ \/]' # 2nd RE for... fwd_slash --> underscore
  sanitized = re.sub(pattern2, '_', rinsed)
  return sanitized

def default_dir_initializer():
  try:
    with open('config.json', 'r') as f:
      configObj = json.load(f)
  except (FileNotFoundError, json.JSONDecodeError):
    configObj = {"default_dir_path": "","keep": 2,"paths": []}  
  
  current_dir = os.path.dirname(os.path.realpath(__file__))
  default_relative_path = os.path.join(current_dir, 'saves')
  make_saves_dir = os.makedirs(default_relative_path, exist_ok=True)
  configObj['default_dir_path'] = default_relative_path
  
  with open("config.json", 'w') as f:
    json.dump(configObj, f, indent=2)
  return default_relative_path

def update_config(saved):
  with open('config.json', 'r') as f:
    configObj = json.load(f)
  paths = configObj['paths']
  keep = configObj['keep']
  if len(paths) >= keep:
    oldest = configObj['paths'][-1]
    if os.path.exists(oldest):
      os.remove(oldest)
  paths.insert(0,saved)
  configObj['paths']=paths[:keep]
  with open('config.json', 'w') as out:
    json.dump(configObj, out, indent=2)

def select_save_path(input, title):
  try:
    with open('config.json', 'r') as f:
      configObj = json.load(f)
  except(FileNotFoundError, json.JSONDecodeError):
      messagebox.showerror("Error", f"Failed to load configuration file.")
  
  defaultDir = configObj.get('default_dir_path')
  if defaultDir == "": #empty str = first run or missing config
    defaultDir = default_dir_initializer()
  else:
    if os.path.exists(defaultDir) == False:
      os.makedirs(defaultDir,exist_ok=True)
  file_path = os.path.join(defaultDir, title + '.jpg')
  if file_path:
    try:
      update_config(file_path)
      if input.mode != "RGB":
        input.convert("RGB").save(file_path)
      else:
        input.save(file_path)
      return file_path
    except Exception as e:
      messagebox.showerror("Error", f"Failed to save image: {e}")
  return None

def main():
  try:
    with open('config.json', 'r') as f:
      configObj = json.load(f)
  except(FileNotFoundError, json.JSONDecodeError):
    configObj = {'default_dir_path': '', 'keep': 2, 'paths': []}

  img_url, description, post_title = fetch_apod_data(use_random=False)
  print(img_url)
  clean_filename = sanitize_filename(post_title)

  if not img_url:
    return

  for path in configObj['paths']: 
    if clean_filename not in path:# check for duplicate
      continue
    else:
      img_url, description, post_title = fetch_apod_data(use_random=True)
      print('RANDOM',img_url)
      clean_filename = sanitize_filename(post_title)
      break

  image_response = requests.get(img_url)
  image = Image.open(BytesIO(image_response.content))
  image_path = select_save_path(image, clean_filename)
  if image_path:
    set_desktop_background(image_path)
  

main()
