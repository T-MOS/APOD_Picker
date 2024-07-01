import ctypes
import os
import platform
import re
import json
import random
import requests
from io import BytesIO
from tkinter import messagebox

from bs4 import BeautifulSoup
from PIL import Image

def urlRandomizer():
  dd = random.randint(1,31)
  mm = random.randint(1,12)
  yy = random.randint(0,24)
  ddStr = str(dd).zfill(2)
  mmStr = str(mm).zfill(2)
  yyStr = str(yy).zfill(2)
  jointDate = yyStr+mmStr+ddStr
  urlFormatted = f"ap{jointDate}.html"
  return urlFormatted

def fetch_apod_data():
  testCase1 = 'https://apod.nasa.gov/apod/2406' # server error test
  testCase2 = 'https://apod.nasa.gov/apod/ap240626.html' # no image tag test 

  # Send GET request to APOD; parse HTML w/ BeautifulSoup
  baseUrl = 'https://apod.nasa.gov/apod/'
  try:
    response = requests.get(baseUrl)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    img_tag = soup.find('img')
    while img_tag is None: # no image = repeat w/ random
      try:
        randomPost = baseUrl + urlRandomizer()
        response = requests.get(randomPost)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
        img_tag = soup.find('img')
      except requests.RequestException as e:
        messagebox.showerror("Error",f"{e}")
    else: # get goodies
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

def sanitize_filename(input_string):
  unsanitized = input_string.strip() # for: lead/trail whitespace
  pattern1 = r'[\:*?"<>|]' # 1st disallowed chars' RE pattern
  rinsed = re.sub(pattern1, "", unsanitized)
  pattern2 = r'[ \/]' # 2nd RE for: fwd_slash --> space
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
  except (FileNotFoundError, json.JSONDecodeError):
    configObj = {"default_dir_path": "","keep": 2,"paths": []}
  
  defaultDir = configObj.get('default_dir_path')
  if defaultDir == "":
    defaultDir = default_dir_initializer()
  else:
    if os.path.exists(defaultDir) == False:
      os.makedirs(defaultDir,exist_ok=True)
  file_path = os.path.join(defaultDir, sanitize_filename(title) + '.jpg')
  if file_path:
    try:
      update_config(file_path)
      input.save(file_path)
      return file_path
    except Exception as e:
      messagebox.showerror("Error", f"Failed to save image: {e}")
  return None

def main():
  img_url, description, post_title = fetch_apod_data()
  if not img_url:
    return
  image_response = requests.get(img_url)
  image = Image.open(BytesIO(image_response.content))
  image_path = select_save_path(image, post_title)
  if image_path:
    set_desktop_background(image_path)

main()
