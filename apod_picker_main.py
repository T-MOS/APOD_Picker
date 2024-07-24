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
from tkinter import Tk
from datetime import datetime
from io import BytesIO
from bs4 import BeautifulSoup
from PIL import Image
#check for &/or init attempts log
if not os.path.exists('info.txt'):
  with open('info.txt','a') as file:
    dt=datetime.now().strftime("%Y-%m-%d %H:%M,%S")
    file.write(f"initialized {dt}\n\n")
logging.basicConfig(filename='info.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def to_errlog(error_message):
  logging.error(error_message)

def json_log(pool,url,dup,image):
  log_entry = {
    "pool": pool,
    "url/source": url,
    "duplicate": dup,
    "image": image
  }
  logging.info(json.dumps(log_entry, indent=2)+"\n")

def get_base_path():
  if getattr(sys,'frozen',False): # executable
    app_path = os.path.dirname(sys.executable)
  else: # script
    app_path = os.path.dirname(os.path.abspath(__file__))

  return app_path

def default_dir_initializer():
  configObj = open_config()
  base_dir = get_base_path()
  default_relative_path = os.path.join(base_dir, 'saves')
  
  # makes the main saves dir while making the faves subdir 
  make_dirs = os.makedirs(os.path.join(default_relative_path, 'faves'), exist_ok=True)
  configObj['base path'] = default_relative_path
  dump2json(configObj)
  return default_relative_path

def image_pool_selector(config):
  faves = config['faves']
  pool = "fetch"
  if 0 < len(faves) < 10: # (essentially) no faves
    small = random.randint(1,100) # set a minimum likelihood 
    if small <= 25: #25% chance to use image(s) from the  faves pool
      pool = "faves"
    return pool
  elif 10 <= len(faves) < 150: # medium amount
    #increase the likelihood/weight of using favorite images by .1% + floor constant
    scaled = ((len(faves) * .001) + .25)
    medium = random.randint(1,1000)
    if medium <= scaled * 1000: # normalize scaled float for comparison /w random's int
      pool = "faves"
    return pool
  elif len(faves) >= 150: # relatively large fave pool; fetch/fave weight parity
    large = random.randint(1,2)
    if large == 1:
      pool = "faves"
    return pool

  else:
    return pool

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

def fetch_apod_data(use_random=False,max=2):
  # Send GET request to APOD; parse HTML w/ BeautifulSoup
  baseUrl = 'https://apod.nasa.gov/apod/'
  tries = 0
  while tries <= max:  
    try:
      if use_random:
        random_post = baseUrl + urlRandomizer()
        response = requests.get(random_post)
      else:
        response = requests.get(baseUrl)
      if response.status_code != 200:
        logging.info(f"{response.status_code}\n URL...{response.url}")
        tries+=1
        continue
      soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
      img_tag = soup.find('img')
      if img_tag is None: # no usable image --> exit for retry
        tries+=1
        continue
      
      description = img_tag.find_next('p').text.strip() # Extract description text from: descendant <p>
      a = img_tag.find_parent('a') # Grab parent's href for full resolution (<a>[href] !== <img>[src])
      img_url = baseUrl + a['href'] # <- download/save from
      return img_url, simple_formatter(description) 
    
    except requests.RequestException as e:
      to_errlog(f"Failed to fetch APOD data: {e}\n")
  return None, None

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

def sanitize_filename(url_string):
  pattern = r'([^/]+)\.[^.]+$' #read: "after last '/' before last '.'"
  rinsed = re.search(pattern, url_string)
  return rinsed

def update_saves(saved):
  configObj = open_config()
  
  saves = configObj['saves']
  keep = configObj['keep']
  saves.insert(0,saved)

  #pop/swap list items 
  if len(saves) >= keep:
    while len(saves) > keep:
      oldest = configObj['saves'][-1]
      oldest_path = os.path.join(configObj['base path'],oldest)
      if os.path.exists(oldest_path):
        os.remove(oldest_path)
        saves.pop(-1)
      else:
        saves.pop(-1)

  configObj['saves'] = saves
  dump2json(configObj)

def open_config():
  try:
    with open('config.json', 'r') as f:
      configObj = json.load(f)
  except(FileNotFoundError, json.JSONDecodeError) as e:
    logging.warning("config.json not found or invalid, making a default configuration")
    to_errlog(f"{e}\n")
  finally:
    if not os.path.exists("config.json"):
      with open('config.json','w'):
        configObj = {
          "base path": "",
          "keep": 4,
          "last daily": "",
          "saves": [],
          "faves": []
        }
  return configObj

def dump2json(config):
  try:
    with open('config.json', 'w') as out:
      json.dump(config, out, indent=2)
  except Exception as e:
    to_errlog(f"JSON error: {e}\n")

def faves_updater():
  configObj = open_config()
  s = configObj['saves']
  f = configObj['faves']
  setS = set(s)
  set_of_saves = set()
  new_set_of_faves = set()

  for root,sub,files in os.walk(configObj["base path"]):
    for file in files:
      if (".jpg" or ".png" or ".bmp") in file:
        if 'faves' not in root: # image in \saves
          set_of_saves.add(file)
        else: # "faves" in root
          # find end point of faves string
          faves_index = root.index('faves') + len('faves') 
          # strip os sep's from everything after
          rel_path = root[faves_index:].strip(os.sep)
          # rejoin w/ file ++ sep's
          relative_file = os.path.join(rel_path,file) 
          new_set_of_faves.add(relative_file)
  uncounted_in_saves = list(set_of_saves.difference(setS))

  f = list(new_set_of_faves)
  f.extend(uncounted_in_saves)

  faves_dir = os.path.join(configObj["base path"],'faves')

  for img in uncounted_in_saves:
    orphan = os.path.join(configObj["base path"],img)
    foster = os.path.join(faves_dir,img)
    try:
      os.rename(orphan, foster)
    except Exception as e:
      to_errlog(f"{e}\n")
  configObj['faves'] = f
  dump2json(configObj)
  return configObj

def duplicate_paths(url, configs):
  files = configs['faves'] + configs['saves']
  clean_filename = sanitize_filename(url).group(1)

  if len(files) > 0:
    for file in files:
      if clean_filename not in file:
        logging.debug(f"Sanitized filename: {clean_filename}")
      else:
        logging.debug(f"dup found @ {file}")
        return True, file #path of existing image
    return False, clean_filename # pass to select_save()
  else:
    return None, clean_filename # no paths

def select_save_path(input, title):
  configObj = open_config()
  defaultDir = configObj.get('base path')

  if os.path.exists(defaultDir) == False:
    os.makedirs(defaultDir,exist_ok=True)

  file_path = os.path.join(defaultDir, title + '.jpg')
  if file_path:
    try:
      update_saves(title + '.jpg')
      input.save(file_path)
      return file_path
    except Exception as e:
      to_errlog(f"Failed to save image: {e}\n")
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
      logging.debug(f'set_BG() returned FALSE \n\nDELETED temp file @ ... {temp_path[:-16]} ')

def set_desktop_background(image_path):
  try:  
    if platform.system() == 'Linux':
      setterCommand = f'pcmanfm --set-wallpaper {image_path}'
      os.system(setterCommand)
    elif platform.system() == 'Windows':
      SPI_SETDESKWALLPAPER = 0x0014
      windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
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

def get_resolution():
  if platform.system() == ('Darwin' or 'Linux'):
    
    root = Tk()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.destroy()
    return w, h
  
  elif platform.system() == 'Windows':
    scale = windll.shcore.GetScaleFactorForDevice(0)
    factor = 1 # Initialize the scaling factor to 1
    user32 = windll.user32
    w, h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    
    if scale > 100: # Check if layout scale is greater than 100%
      factor = (scale/100) - 1
      w, h = w+w*factor, h+h*factor
    return w, h

def qa(image):
  w, h = get_resolution()
  wim, him = image.size
  
  if image.mode != "RGB":
    image = image.convert("RGB")
  
  # disp. orientation -> usable image aspect -> resolution scale factor 
  if w > h: # landscape
    if wim/him >= .6875*(w/h): #ascpect w/in margin
      if w <= 2560: # up to 2k disp
        if wim >= w*.8125:  # min. 13/16ths of w
          return image
      if 2560 < w < 3840: # up to 4k disp
        if wim >= w*.6875:  # min. 11/16ths of w
          return image
      else: # constant cap
        if wim > 2640:
          return image
    elif (wim >= w or him >= h) and wim/him > .98: # relatively high resolution but possibly sq.
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
    elif (max(h,w)<= wim) and wim/him > .98: # relatively high resolution but possibly sq.
      return image
    else:
      return None

def date_comparator(configObj):
  # stringify a date object; regionally formated
  dateStr = datetime.now().strftime('%x')
  
  # compare against record
  if dateStr != configObj['last daily']: # FIRST OF DAY
    configObj['last daily'] = dateStr # update configObj w/ new date str
    dump2json(configObj)
    return False
  else: # likely a RERUN...
    return True

def main():
  default_dir_initializer()
  configObj = faves_updater()
  pool = image_pool_selector(configObj)
  Image.MAX_IMAGE_PIXELS = 136037232 #adjust decompression bomb warning threshold to largest APOD image yet

  if pool == "fetch":
    img_url, description = None, None
    image = None
    while (not img_url or not image):
      daily = date_comparator(configObj)
      img_url, description = fetch_apod_data(daily)
      if img_url:
        image_response = requests.get(img_url)
        image_response.raise_for_status()
        try:
          image = qa(Image.open(BytesIO(image_response.content))) # returns None if image fails QA
        except Exception as e:
          to_errlog(f"{e}\n")

    dup_check = duplicate_paths(img_url, configObj)
    # dup_check returns: None,filename (no paths), True/path (found dup), False/filename (no match)
    if True in dup_check:
      set_desktop_background(dup_check[1])
      json_log(pool,img_url, "Duplicate found", dup_check[1])
    else:
      if configObj['keep'] > 0: # SAVE -> set
        image_path = select_save_path(image, dup_check[1])
        logging.debug(f"Image saved to path: {image_path}")
        if image_path:
          set_desktop_background(image_path)
          logging.debug("New Desktop background FETCHED/set")
          json_log(pool,img_url, "Original; saving", image_path)
      else:
        setter_no_save(image)
        json_log(pool,img_url, "Original; temporary", image)

  else: # from... pool = "faves"
    shuffaves = configObj['faves']
    random.shuffle(shuffaves)
    image_path = os.path.join(os.path.join(configObj['base path'],'faves'),shuffaves[0])
    set_desktop_background(image_path)
    logging.debug(f"OLD Desktop background FAVES -> set {image_path}")
    json_log(pool, "...\\faves...", "", shuffaves[0])

if __name__=="__main__":
  main()