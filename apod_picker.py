import ctypes
import os
import platform
import re
import json
import requests
import random
import tkinter as tk
from datetime import datetime
from io import BytesIO
from tkinter import messagebox, filedialog


from bs4 import BeautifulSoup
from PIL import Image, ImageTk

class ImageViewer:
  def __init__(self, root, image_path, text, title):
    self.root = root
    self.root.title(title)
    self.description = self.simple_formatter(text)

    # Load the original image
    self.original_image = image_path
    self.original_width, self.original_height = self.original_image.size
    # self.photo = self.original_image

    # Create a labels to display the image and description
    self.desc_label = tk.Label(root, text=self.description, bg='dim grey',fg="white", font=('Arial Bold',), justify='center')
    self.desc_label.pack(side="top", fill='x')
    self.image_label = tk.Label(root, bg="grey23")
    self.image_label.pack(fill=tk.BOTH, expand=tk.YES)

    # Bind the resize event
    self.root.bind("<Configure>", self.resize_image)

  def resize_image(self, event):
    # Get the new size of the window
    new_width = event.width
    new_height = event.height

    # Calculate the new size while maintaining the aspect ratio
    aspect_ratio = self.original_width / self.original_height
    if new_width / new_height > aspect_ratio:
      new_width = int(new_height * aspect_ratio)
    else:
      new_height = int(new_width / aspect_ratio)
    
    # Resize the image
    resized_image = self.original_image.resize((new_width, new_height))
    self.photo = ImageTk.PhotoImage(resized_image)

    # Update the label with the new image
    self.image_label.config(image=self.photo)
    self.image_label.image = self.photo  # Keep a reference to avoid garbage collection
    self.desc_label.config(wraplength=self.root.winfo_width() - 20)

  def simple_formatter(self, text):
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

def urlRandomizer():
  yearsElapsed = datetime.now().year - 1995
  yy = random.randint(0,yearsElapsed)
  if yy < 10:
    yyStr = str(yy).zfill(2)
  elif 9 < yy < 100:
    yyStr = str(yy)[-2:]
  else: # in case APOD's still kicking in 2,100
    yyStr = str(yy)[-3:]
  mm = random.randint(1,12)
  dd = random.randint(1,31)
  mmStr = str(mm).zfill(2)
  ddStr = str(dd).zfill(2)

  jointDate = yyStr+mmStr+ddStr
  urlFormatted = f"ap{jointDate}.html"
  print(dd, ddStr, mm, mmStr, yy, yyStr)
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
      post_title = soup.find('b').text.strip() # title in: "<center> w/ child <b>"
      description = img_tag.find_next('p').text.strip() # description text from: descendant <p>
      a = img_tag.find_parent('a') # parent's href = full resolution (<a>[href] !== <img>[src])
      img_url = baseUrl + a['href'] # <- download/save from
      return img_url, description, post_title 
  except requests.RequestException as e:
    messagebox.showerror("Error",f"Failed to fetch APOD data: {e}")
  return None, None, None

def set_desktop_background(image_path):
  try:  
    if platform.system() == 'Linux':
      setterCommand = f'pcmanfm --set-background {image_path}'
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
    messagebox.showinfo('Set Background Successful', 'Desktop background has been set.')
  except Exception as e:
    messagebox.showerror("Error", f"Failed to set the desktop background: {e}")

def sanitize_filename(input_string):
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
  except (FileNotFoundError, json.JSONDecodeError):
    configObj = {"default_dir_path": "","keep": 2,"paths": []}
  
  defaultDir = configObj.get('default_dir_path')
  if defaultDir == "":
    defaultDir = default_dir_initializer()
  else:
    if os.path.exists(defaultDir) == False:
      os.makedirs(defaultDir,exist_ok=True)
  file_path = filedialog.asksaveasfilename(defaultextension='.jpg', filetypes=[("JPEG","*.jpg"),("All files","*.*")],initialfile= sanitize_filename(title), initialdir=defaultDir)
  if file_path:
    try:
      update_config(file_path)
      input.save(file_path)
      return file_path
    except Exception as e:
      messagebox.showerror("Error", f"Failed to save image: {e}")
  return None

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

def main():
  w,h = get_resolution()
  root = tk.Tk()
  img_url, description, post_title = fetch_apod_data()
  if not img_url:
    root.destroy()
    return
  
  image_response = requests.get(img_url)
  image = Image.open(BytesIO(image_response.content))
  # photo = ImageTk.PhotoImage(image)
  # description_label = tk.Label(root, text=formatted, justify='left', wraplength=w).pack(side='top')

  # initial-s-ize
  root.geometry(f"{w//2}x{h//2}")
  # root.withdraw()

  app = ImageViewer(root, image, description, post_title)

  # ask to save
  user_response = messagebox.askquestion('Set Desktop Background', 'Set this image as your desktop background?')
  if user_response == 'yes':
    image_path = select_save_path(image, post_title)
    if image_path:
      set_desktop_background(image_path)
  # else:
  #   messagebox.showinfo('Set Background Declined','Desktop background has not been changed.')
  
  root.mainloop()

main()
