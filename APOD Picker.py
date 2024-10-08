import ctypes, os, sys, platform, json, random, requests, logging, tempfile, re
from log import to_errlog, json_log
import Stegappend, scheduler
# from Mac_specifics import mac_dual_display
from screeninfo import get_monitors
from tkinter import Tk
from datetime import datetime
from io import BytesIO
from bs4 import BeautifulSoup
from PIL import Image

if len(sys.argv) == 2:
  Stegappend.APOD_decoding()

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_base_path():
  if getattr(sys,'frozen',False): # executable
    app_path = os.path.dirname(sys.executable)
    task_action = os.path.join(app_path, sys.executable)
  else: # script
    app_path = os.path.dirname(os.path.abspath(__file__))
    task_action = os.path.join(app_path,__file__) 
  return app_path, task_action

def default_dir_initializer():
  base_dir = get_base_path()[0]
  default_relative_path = os.path.join(base_dir, 'APOD Saves')

  # make the main saves dir & faves subdir 
  os.makedirs(os.path.join(default_relative_path, 'faves'), exist_ok=True)

  return default_relative_path

#check for &/or init attempts log
def init_all():
  default_relative_path = default_dir_initializer()
  
  # create/write log info w/ init
  info = os.path.join(default_relative_path, 'info.txt')
  if not os.path.exists(info):
    with open(info,'a') as file:
      dt=datetime.now().strftime("%Y-%m-%d %H:%M,%S")
      file.write(f"initialized {dt}\n\n")\
  
  # create/dump config.json + default configObj w/ base path
  config_file = os.path.join(default_relative_path,"config.json")
  if not os.path.exists(config_file):
    with open(config_file,'x') as file:
      configObj = {
        "base path": f"{default_relative_path}",
        "keep": 4,
        "last daily": "",
        "saves": [],
        "faves": []
      }
      json.dump(configObj,file,indent=2)
  return info 

def scheduling(task_action):
  if getattr(sys,'frozen',False): # only check/schedule if executable runs
    try:
      if scheduler.task_exists():
        return
      else:
        scheduler.create_task(task_action)
    except Exception as e:
      to_errlog(f"Task scheduler (win) error:{e}")

def sanitize_filename(url_string):
  pattern = r'([^/]+)\.[^.]+$' #read: "after last '/' before last '.'"
  rinsed = re.search(pattern, url_string)
  return rinsed

def resize(image,mn):
  # init dimensions
  if isinstance(image, Image.Image):
    img = image
  else:
    img = Image.open(image)
  iw, ih = img.size
  mw, mh = mn.width, mn.height
  wscale = iw/mw
  hscale = ih/mh

  #scale by relatively larger dim to constrain in disp.
  newiw, newih = int(iw/max(hscale,wscale)), int(ih/max(hscale,wscale))
  resized_image = img.resize((newiw,newih),Image.Resampling.LANCZOS)

  return resized_image

def img_combine(images, m):
  resizeds = {}
  canvas_y = 0
  canvas_x = 0

  if len(images) != len(m):
    to_errlog(f"{ValueError} -> images:monitors parity ")

  #monitor object order varies; find index of primary disp
  primary_index = next((i for i,mn in enumerate(m) if mn.is_primary), None)
  #swap to ensure primary is first
  m[0], m[primary_index] = m[primary_index], m[0]
  
  pairs = list(zip(images,m))

  for i, (image,mn) in enumerate(pairs):
    resizeds[f"{i}"] = resize(image, mn)
    #set the canvas base width/height = to largest w/h found 
    if mn.width > canvas_x:
      canvas_x = mn.width
    if mn.height > canvas_y:
      canvas_y = mn.height

  primary_x_adjust, primary_y_adjust = (m[0].width - resizeds['0'].size[0])//2, (m[0].height - resizeds['0'].size[1])//2
  secondary_x_adjust, secondary_y_adjust = (m[1].width - resizeds['1'].size[0])//2, (m[1].height - resizeds['1'].size[1])//2
  for i, mn in enumerate(m):
    if (mn.x < 0): # (-)x
      if (m[0].width + abs(mn.x))> canvas_x: 
        # add abs val of x-offset to primary display's width for new canvas width since,
        # in canvas coordinates, primary is the one translated from origin across x
        canvas_x = m[0].width + abs(mn.x)
      if mn.y < 0: # (-)x, (-)y
        if (m[0].height + abs(mn.y)) > canvas_y:
        # add abs val of y-offset to primary height for canvas relative height
          canvas_y = m[0].height + abs(mn.y)

        secondary_x = 0
        secondary_y = 0
        primary_x = abs(mn.x)
        primary_y = abs(mn.y)
      else: # (-)x,(+)y
        if (m[1].height + mn.y) > canvas_y:
          canvas_y = m[1].height + mn.y

        secondary_x = 0
        secondary_y = mn.y
        primary_x = abs(mn.x)
        primary_y = 0
    elif (mn.x > 0): # (+)x
      # inverse of behavior from (-)x; nonprimary == translated
      if (m[1].width + abs(mn.x)) > canvas_x: 
        canvas_x = m[1].width + abs(mn.x)
      if mn.y < 0: # (+)x, (-)y
        if (m[0].height + abs(mn.y)) > canvas_y:
        # add abs val of y-offset to primary height for canvas relative height
          canvas_y = m[0].height + abs(mn.y)
          
        secondary_x = mn.x
        secondary_y = 0
        primary_x = 0
        primary_y = abs(mn.y)
      else: # (+)x, (+)y
        if (m[1].height + mn.y) > canvas_y:
          canvas_y = m[1].height + mn.y

        secondary_x = mn.x
        secondary_y = mn.y
        primary_x = 0
        primary_y = 0

  combo_canvas = Image.new('RGB', (canvas_x,canvas_y))
  primario = combo_canvas.paste(resizeds['0'], (primary_x + primary_x_adjust, primary_y + primary_y_adjust))
  segundo = combo_canvas.paste(resizeds['1'], (secondary_x + secondary_x_adjust, secondary_y + secondary_y_adjust))
  
  return combo_canvas

def image_pool_selector(config):
  faves = config['faves']
  pool = "fetch"
  if 1 < len(faves) < 10: # (essentially) no faves
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
        to_errlog(f"{response.status_code}\n URL...{response.url}")
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

def fetch_fave(configObj):
  shuffaves = configObj['faves']
  random.shuffle(shuffaves)
  image_path = os.path.join(os.path.join(configObj['base path'],'faves'),shuffaves[0])
  return image_path

def simple_formatter(text):
    if text:
      lines = text.splitlines()
      concatenated_description = ''
      for line in lines:
        if len(line) > 0:
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

def update_saves(saved):
  configObj = open_config()
  saves = configObj['saves']
  keep = configObj['keep']
  saves.insert(0,saved)

  #pop/swap list items 
  if len(saves) >= keep:
    while len(saves) > keep:
      oldest = configObj['saves'][-1]
      oldest_path = os.path.join(configObj['base path'], oldest)
      if os.path.exists(oldest_path):
        os.remove(oldest_path)
        saves.pop(-1)
      else:
        saves.pop(-1)

  configObj['saves'] = saves
  dump2json_file(configObj)

def open_config():
  config_file = os.path.join("APOD saves","config.json")
  try:
    with open(config_file, 'r') as f:
      configObj = json.load(f)
  except(FileNotFoundError, json.JSONDecodeError) as e:
    to_errlog(f"{e}\n")
  return configObj

def dump2json_file(config):
  try:
    with open(os.path.join("APOD saves",'config.json'), 'w') as out:
      json.dump(config, out, indent=2)
  except Exception as e: 
    to_errlog(f"dump2json_file() error: {e}\n")

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
  dump2json_file(configObj)
  return configObj

def duplicate_paths(url, configs):
  files = configs['faves'] + configs['saves']
  clean_filename = sanitize_filename(url).group(1)

  if len(files) > 0:
    for file in files:
      if clean_filename in file:
        return True, file #path of existing image
    return False, clean_filename # pass to select_save()
  else:
    return None, clean_filename # no paths

def select_save_path(input, title, description):
  configObj = open_config()
  defaultDir = configObj.get('base path')
  inputImage = input

  if os.path.exists(defaultDir) == False:
    os.makedirs(defaultDir,exist_ok=True)

  file_path = os.path.join(defaultDir, title + '.png')
  if file_path:
    if description is not None:
      inputImage = Stegappend.APOD_encoding(input, description)
    try:
      update_saves(title + '.png')
      inputImage.save(file_path)
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
    to_errlog("Error", f"Failed to set the desktop background: {e}")
    return False

def get_resolution(): # single display only
  if platform.system() == ('Darwin' or 'Linux'):
    root = Tk()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.destroy()
    return w, h
  
  elif platform.system() == 'Windows':
    scale = ctypes.windll.shcore.GetScaleFactorForDevice(0)
    factor = 1 # Initialize the scaling factor to 1
    user32 = ctypes.windll.user32
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
    elif (wim >= w or him >= h) and wim/him >= 1: # relatively high resolution but possibly sq.
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
    dump2json_file(configObj)
    return False
  else: # likely a RERUN...
    return True

def fetch_segundo(): # "quick" run a random fetch_apod for use in second monitor if no favorites exist
  fetch, image = None, None 
  while (not fetch or not image):
    fetch = fetch_apod_data(True)
    if fetch[0]: # if img_url
      image_response = requests.get(fetch[0])
      image_response.raise_for_status()
      try:
        image = qa(Image.open(BytesIO(image_response.content))) # returns None if image fails QA
      except Exception as e:
        to_errlog(f"{e}\n")
    segundo_nombre = sanitize_filename(fetch[0]).group(1)
  return image, segundo_nombre

def main():
  logging.basicConfig(filename=init_all(), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

  if platform.system() == "Windows":
    scheduling(get_base_path()[1])
  elif platform.system() == "Darwin":
    scheduler.cron_job(get_base_path()[1])

  configObj = faves_updater()
  pool = image_pool_selector(configObj)
  multi_monitor = get_monitors()
  Image.MAX_IMAGE_PIXELS = 136037232 #adjust decompression bomb warning threshold to largest APOD image

  if pool == "fetch":
    img_url, image, description = None, None, None
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
    # dup_check returns: None,filename (no paths), False/filename (no match), True/path (found dup)

    if True in dup_check:
      if len(multi_monitor) == 2:
        if len(configObj['faves']) > 0:
          images = [dup_check[1], fetch_fave(configObj)]
          log_images = images
          pool = "fetched duplicate -> save-fave/fave"
        else:
          fs = fetch_segundo()
          images = [dup_check[1],fs[0]]
          log_images = [dup_check[1], fs[1]]
          pool = "fetched duplicate, no faves -> saves/fetch"
        setter_no_save(img_combine(images, multi_monitor))
        json_log(pool, img_url, "Duplicate found", log_images)
      else:
        set_desktop_background(dup_check[1])
        json_log(pool,img_url, "Duplicate found", dup_check[1])
    else:
      if configObj['keep'] > 0: # SAVE -> set
        image_path = select_save_path(image, dup_check[1], description)
        logging.debug(f"Image saved to path: {image_path}")
        if image_path:
          if len(multi_monitor) == 2:
            if len(configObj['faves']) > 0:
              images = [image_path, fetch_fave(configObj)]
              log_images = images
              pool = "fetch/fave"
            else:
              fs = fetch_segundo()
              images = [image_path, fs[0]]
              log_images = [image_path, fs[1]]
              pool = "No faves -> fetch/fetch"
            setter_no_save(img_combine(images, multi_monitor))
            json_log(pool, img_url, "None/False", log_images)
          else:
            set_desktop_background(image_path)
            json_log(pool, img_url, "Original; saving", image_path)
      else:
        if len(multi_monitor) == 2:
          if len(configObj['faves']) > 0:
            images = [image, fetch_fave(configObj)]
            log_images = images
            pool = "fetch/fave"
          else:
            fs = fetch_segundo()
            images = [image, fs[0]]
            log_images = [image, fs[1]]
            pool = "fetch/fetch"
          setter_no_save(img_combine(images,multi_monitor))
          json_log(pool, img_url, "Original; temporary", log_images)
        else:
          setter_no_save(image)
          json_log(pool, img_url, "Original; temporary", dup_check[1])

  else: # from... pool = "faves"
    if len(multi_monitor) == 2:
      images = [fetch_fave(configObj),fetch_fave(configObj)]
      setter_no_save(img_combine(images, multi_monitor))
      json_log("fave/fave", "n/a", "n/a; faves pool preselect", images)
    else:
      fave_img = fetch_fave(configObj)
      set_desktop_background(fave_img)
      json_log(pool, fave_img, "n/a; faves pool preselect", fave_img)

if len(sys.argv) == 1:
  if __name__=="__main__":
    main()