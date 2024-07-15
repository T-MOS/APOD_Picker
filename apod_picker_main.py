import ctypes
import os
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
# from exiftool import ExifToolHelper
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
      fetch_apod_data(True)
    description = img_tag.find_next('p').text.strip() # Extract description text from: descendant <p>
    a = img_tag.find_parent('a') # Grab parent's href for full resolution (<a>[href] !== <img>[src])
    img_url = baseUrl + a['href'] # <- download/save from
    return img_url, simple_formatter(description) 
  except requests.RequestException as e:
    logging.error("Error",f"Failed to fetch APOD data: {e}")
    fetch_apod_data(True)
    # return None, None, None

def simple_formatter(text):
    if text:
      lines = text.splitlines()
      concatenated_description = ''
      for line in lines:
        if len(line) >0:
          line = line.strip() # Remove whitespace at the beginning and end of the line
          if line.startswith('Explanation:'):
            concatenated_description += ''
          elif line.startswith('Tomorrow'):
            return concatenated_description
          else:
            if concatenated_description ==  "":
              concatenated_description += line
            else:
              concatenated_description += " " + line
      return concatenated_description
    return None

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
  configObj = open_config()
  
  paths = configObj['paths']
  keep = configObj['keep']

  #pop/swap list items 
  if len(paths) >= keep:
    oldest = configObj['paths'][-1]
    if os.path.exists(oldest):
      os.remove(oldest)

  paths.insert(0,saved)
  configObj['paths']=paths[:keep]
  dump2json(configObj)

def open_config():
  try:
    with open('config.json', 'r') as f:
      configObj = json.load(f)
  except(FileNotFoundError, json.JSONDecodeError):
    logging.warning("config.json not found or invalid, making a default configuration")
    
    configObj = {'default_dir_path': '', 'keep': 1, 'paths': []}
  return configObj

def dump2json(config):
  try:
    with open('config.json', 'w') as out:
      json.dump(config, out, indent=2)
  except Exception as e:
    logging.debug(f"{e}")
    
def duplicate_paths(url, configurations):
  paths = configurations['paths']
  clean_filename = sanitize_filename(url).group(1)

  if len(paths) > 0:
    logging.debug(f"Sanitized filename: {clean_filename}")
    for path in paths:
      if clean_filename not in path:
        return False, clean_filename # pass to select_save()
      else:
        return True, path #path of existing image
  else:
    return None, clean_filename# no paths

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
      input.save(file_path)
      return file_path
    except Exception as e:
      logging.error("Error", f"Failed to save image: {e}")
  return None

def setter_no_save(image):
  fd, temp_path = tempfile.mkstemp(suffix='.jpg')
  os.close(fd)
  try:
    image.save(temp_path)
    logging.debug(f'CREATED temp file ... {temp_path[-16:]} ')
  finally:
    if set_desktop_background(temp_path) == True:
      os.remove(temp_path)
      logging.debug(f'DELETED temp file @ ... {temp_path[:-16]} ')
    else:
      os.remove(temp_path)

def get_resolution():
  if platform.system() == 'Darwin' or 'Linux':
    root = tk.Tk()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.destroy()
    return w, h
  elif platform.system() == 'Windows':
    user32 = ctypes.windll.user32
    w, h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    return w, h
# Platform/OS type
# if platform.system() == 'Windows':
#   user32 = ctypes.windll.user32
#   w = user32.GetSystemMetrics(0)
#   h = user32.GetSystemMetrics(1)
# if platform.system() == 'Linux':
#   w, h = get_resolution()
#   get_resolution()
# if platform.system() == 'Darwin':
#   w,h = get_resolution()
#   get_resolution()

def qa(image):
  w, h = get_resolution()
  wim, him = image.size
  
  if image.mode != "RGB":
    image = image.convert("RGB")

  print(image.size, "res:",w,h)
  
  # disp. orientation -> usable image aspect -> resolution scale factor 
  if w > h: # landscape
    if wim/him >= .75*(w/h): #ascpect w/in margin
      if w <= 2560: # up to 2k disp
        if wim >= w*.8125:  # min. 13/16ths of w
          return image
      if 2560 < w < 3840: # up to 4k disp
        if wim >= w*.6875:  # min. 11/16ths of w
          return image
      else: # constant cap
        if wim > 2640:
          return image
    else:
      return None
  else: # portrait
    if wim/him >= .75*(w/h): #ascpect w/in margin
      if w <= 2560: # up to 2k disp
        if wim >= w*.8125:  # min. 13/16ths of w
          return image
      if 2560 < w < 3840: # up to 4k disp
        if wim >= w*.6875:  # min. 11/16ths of w
          return image
      else: # constant cap
        if wim > 2640:
          return image
    else:
      return None

  #     if w > h: # check fit against monitor aspect to infer display orientation
  #       image = image.rotate(90, expand=True)



def main():
  configObj = open_config()

  # stringify a date object; regionally formated
  dtStr = datetime.now().strftime("%x")
  # compare against record
  if dtStr not in configObj['last_daily']: # no match; likely first run of day...
    img_url, description = fetch_apod_data() #  standard 
    configObj['last_daily'] = dtStr # update configObj w/ new date str
    dump2json(configObj)
  else: # matched; likely a rerun...
    img_url, description = fetch_apod_data(True) # ...randomized

  # logging.debug(f"Fetched APOD data: \n\nimg_url: {img_url} \n\ndescription[:150]: {description[:150]}...\n")
  if not img_url:
    logging.error("No image URL found, exiting")
    return
  
  image_response = requests.get(img_url)
  image_response.raise_for_status()
  image = qa(Image.open(BytesIO(image_response.content)))
  # logging.debug(f"Final image URL: {img_url}")

# dup returns: None,filename (no paths), True/path (found dup), False/filename (no match)
  dup_check = duplicate_paths(img_url, configObj) 
  if True in dup_check:
    set_desktop_background(dup_check[1])
  else:
    if configObj['keep'] > 0: # SAVE -> set
      image_path = select_save_path(image, dup_check[1])
      logging.debug(f"Image saved to path: {image_path}")
      if image_path:
        set_desktop_background(image_path)
        logging.debug("Desktop background set successfully")
    else:
      setter_no_save(image)

  # try:
  #   with ExifToolHelper() as et:
  #     # et.set_tags('HaloWinMoon48_claro.jpg',tags={"ImageDescription": description})
  #     for d in et.get_metadata(image_path):
  #       for k,v in d.items():
  #         logging.debug((f"Meta:{k} = {v}"))
  # except FileNotFoundError:
  #   logging.warning("ExifTool not found. Continuing without extracting metadata.")

if __name__=="__main__":
  main()