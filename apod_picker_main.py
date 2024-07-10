import ctypes
import os
import sys
import platform
import re
import json
import random
import requests
import logging
import tempfile
import tkinter as tk
from datetime import datetime
from io import BytesIO
from tkinter import messagebox
from exiftool import ExifToolHelper
from bs4 import BeautifulSoup
from PIL import Image

#logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def urlRandomizer():
  today = datetime.now()
  
  #year
  y = random.randint(1995,today.year)
  if y < 2095:
    yStr = str(y)[-2:]
  else:
    yStr = str(y)[-3:]
  
  #month/day
  m = random.randint(1,12)
  d = random.randint(1,31)
  if y == 1995: # truncated 1st year
    m = random.randint(5,12)
  elif y == today.year: #if y = current year ...
    # limit m/d values to be <= today.m/d 
    m = random.randint(1,today.month)
    d = random.randint(1,today.day)
  mStr = str(m).zfill(2)
  dStr = str(d).zfill(2)

  #format -> output
  jointDate = yStr+mStr+dStr
  urlFormatted = f"ap{jointDate}.html"
  return urlFormatted

def fetch_apod_data(use_random=False):
  # Send GET request to APOD; parse HTML w/ BeautifulSoup
  baseUrl = 'https://apod.nasa.gov/apod/'
  try:
    if use_random:
      random_post = baseUrl + urlRandomizer()
      response = requests.get(random_post)
    else:
      response = requests.get(baseUrl)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    img_tag = soup.find('img')
    if img_tag is None: # no usable image --> repeat w/ random
      try:
        fetch_apod_data(use_random=True)
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
        img_tag = soup.find('img')
      except requests.RequestException as e:  
        messagebox.showerror("Error",f"{e}")
    description = img_tag.find_next('p').text.strip() # Extract description text from: descendant <p>
    a = img_tag.find_parent('a') # Grab parent's href for full resolution (<a>[href] !== <img>[src])
    img_url = baseUrl + a['href'] # <- download/save from
    return img_url, description 
  except requests.RequestException as e:
    logging.error("Error",f"Failed to fetch APOD data: {e}")
    fetch_apod_data(use_random=True)
    # return None, None, None


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
    return True
  except Exception as e:
    logging.error("Error", f"Failed to set the desktop background: {e}")
    return False


def sanitize_filename(url_string):
  pattern = r'([^/]+)\.[^.]+$' #read: "after last '/' before last '.'"
  rinsed = re.search(pattern, url_string)
  return rinsed

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
    logging.error("Error", f"Failed to load configuration file. {e}")
  
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

def set_no_save(image):
  fd, temp_path = tempfile.mkstemp(suffix='.jpg')
  os.close(fd)
  try:
    image.save(temp_path, format="JPEG")
    logging.debug(f'Temp image CREATED @ {temp_path}')
  finally:
    if set_desktop_background(temp_path) == True:
      os.remove(temp_path)
      logging.debug(f'Temp file @ {temp_path} DELETED')
      # sys.exit("Exiting")
    else:
      os.remove(temp_path)
      print('failure')

def get_resolution():
  root = tk.Tk()
  screen_width = root.winfo_screenwidth()
  screen_height = root.winfo_screenheight()
  root.destroy()
  return screen_width, screen_height
# Platform/OS type
if platform.system() == 'Windows':
  user32 = ctypes.windll.user32
  w = user32.GetSystemMetrics(0)
  h = user32.GetSystemMetrics(1)
if platform.system() == 'Linux':
  w, h = get_resolution()
  get_resolution()
if platform.system() == 'Darwin':
  w,h = get_resolution()
  get_resolution()

def check_for_rotate(image):
  w,h = get_resolution()
  wim, him = image.size
  # print('wim/him:',(w/h)/(wim/him),'...him/wim:',(w/h)/(him/wim))
  if .75 <= wim/him <= 1/3:
    # print(image.info)
    return image
  if (w/h)/(wim/him) > (w/h)/(him/wim):
    image = image.rotate(90, expand=True)
    # print(image.size)
  return image

def main():
  logging.debug("Starting main()")
                
  try: #open config
    with open('config.json', 'r') as f:
      configObj = json.load(f)
    logging.debug("Loaded config.json successfully")
  except(FileNotFoundError, json.JSONDecodeError):
    logging.warning("config.json not found or invalid, instantiating default configuration")
    configObj = {'default_dir_path': '', 'keep': 2, 'paths': []}

  img_url, description = fetch_apod_data(use_random=False)
  logging.debug(f"Fetched APOD data: img_url={img_url}, description={description[:50]}")
  
  if not img_url:
    logging.error("No image URL found, exiting")
    return
  
  clean_filename = sanitize_filename(img_url).group(1)
  logging.debug(f"Sanitized filename: {clean_filename}")
  
  for path in configObj['paths']: 
    if clean_filename not in path:# check for duplicate
      continue
    else:
      logging.info("Duplicate filename found, fetching a new APOD data")
      img_url, description = fetch_apod_data(use_random=True)
      clean_filename = sanitize_filename(img_url).group(1)
      break
 
  logging.debug(f"Final image URL: {img_url}")
  image_response = requests.get(img_url)
  logging.debug("Image downloaded successfully")

  image = Image.open(BytesIO(image_response.content))

  configObj['keep'] = 0
  # NO SAVE
  if configObj['keep'] == 0:
    set_no_save(image)
    logging.debug('SUCCESSFUL set_no_save()')

  image_path = select_save_path(check_for_rotate(image), clean_filename)
  logging.debug(f"Image saved to path: {image_path}")


  # try:
  #   with ExifToolHelper() as et:
  #     # et.set_tags('HaloWinMoon48_claro.jpg',tags={"ImageDescription": description})
  #     for d in et.get_metadata():
  #       for k,v in d.items():
  #         logging.debug((f"Meta:{k} = {v}"))
  # except FileNotFoundError:
  #   logging.warning("ExifTool not found. Continuing without extracting metadata.")

  if image_path:
    set_desktop_background(image_path)
    logging.debug("Desktop background set successfully")

if __name__=="__main__":
  main()