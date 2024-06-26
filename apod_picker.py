import ctypes
import os
import platform
import tkinter as tk
from io import BytesIO
from tkinter import messagebox, scrolledtext, filedialog

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageTk


""" Platform specifics """
# OS type == 'Windows' --> Get screen dimensions for "..."
if platform.system() == 'Windows':
  user32 = ctypes.windll.user32
  w = user32.GetSystemMetrics(0)
  h = user32.GetSystemMetrics(1)
# OS type == 'Linux' --> Get screen dimensions for "..."
if platform.system() == 'Linux':
  def get_linux_resolution():
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
    return screen_width, screen_height
  w, h = get_linux_resolution()
  get_linux_resolution()
# OS type -== 'Darwin' aka MacOS --> Get screen dimensions for "..."
if platform.system() == 'Darwin':
  def get_mac_resolution():  
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
    return screen_width, screen_height
  w,h = get_mac_resolution()
  get_mac_resolution()
if w is not None:
  print("w: ",w,", h:", h)

""" Web handling """
# Send GET request to APOD website and parse HTML response with BeautifulSoup
# url = 'https://apod.nasa.gov/apod/astropix.html'
url = 'https://apod.nasa.gov/apod/ap240625.html'
response = requests.get(url)
if response.status_code == 200:
  soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
  img_tag = soup.find('img')
  if img_tag != None:
    # Grab parent (<a>[href]) rather than <img>[src] for FULL RES URL
    a = img_tag.find_parent('a')
    img_url = 'https://apod.nasa.gov/apod/' + a['href']
  else:
    print("The post contains no accepted image formats")
else:
  print(f"Bad response from server... code: {response.status_code}")

# Find the first <p> tag after the image and get its text content
description = soup.find('img').find_next('p').text.strip()

# Request the image and open it with PIL
image_response = requests.get(img_url)
image = Image.open(BytesIO(image_response.content))

# Adjust messagebox height if it exceeds screen height
if image.height > h:
  max_description_height = h - image.height - 100 # Adjust the padding as needed
  max_description_lines = max_description_height // 20 # Assuming each line is around 20 pixels
lines = description.splitlines()
concatenated_description = ''
current_line_length = 0
for line in lines:
  line = line.strip() # Remove whitespace at the beginning and end of the line
  if line.startswith('Explanation:' + '\n'):
    concatenated_description += '\n' + line
    current_line_length = len(line)
  else:
    line = line.replace('\n', ' ') # Replace line breaks within the line with a space
    if current_line_length + len(line) > w // 10:
      concatenated_description += '\n' + line
      current_line_length = len(line)
    else:
      concatenated_description += line
      current_line_length += len(line)

# Display the image in a preview window
root = tk.Tk()
root.title('APOD Image Preview')

# Set the width of the scrolledtext widget to screen width
scroll_text = scrolledtext.ScrolledText(root,
width=w // 10, height=10, wrap=tk.WORD)
scroll_text.pack(fill=tk.BOTH, expand=True)
scroll_text.insert(tk.END, concatenated_description)

# Create a label and display the image
image_label = tk.Label(root)
image_label.pack()
photo = ImageTk.PhotoImage(image)
image_label.configure(image=photo)

# Prompt user to confirm before setting the image as desktop background
messagebox.showinfo('Image Preview', f'Image URL: {img_url}')
response = messagebox.askquestion(
    'Set Desktop Background', 'Set this image as your desktop background?')

def select_save_path():
  file_path = filedialog.asksaveasfilename(defaultextension='.jpg', filetypes=[("JPEG","*.jpg"),("All files","*.*")])
  if file_path:
    print(f"Image saved to: {file_path}")
    image.save(file_path)
    return file_path
  else:
    print("No destination selected")
    
# ask to save
if response == 'yes':
  image_path = select_save_path()

  # Set the image as desktop background
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
root.mainloop()
