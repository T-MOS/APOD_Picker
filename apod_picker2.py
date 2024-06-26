import ctypes
import os
import platform
import tkinter as tk
from io import BytesIO
from tkinter import messagebox, scrolledtext, filedialog
import threading

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageTk


def get_resolution():
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
    return screen_width, screen_height

# OS type == 'Windows' --> Get screen dimensions for "..."
if platform.system() == 'Windows':
  user32 = ctypes.windll.user32
  w = user32.GetSystemMetrics(0)
  h = user32.GetSystemMetrics(1)
# OS type == 'Linux' --> Get screen dimensions for "..."
if platform.system() == 'Linux':
  w, h = get_resolution()
  get_resolution()
# OS type -== 'Darwin' aka MacOS --> Get screen dimensions for "..."
if platform.system() == 'Darwin':
  w,h = get_resolution()
  get_resolution()

""" Web handling """
def fetch_apod_data():
  # Send GET request to APOD website and parse HTML response with BeautifulSoup
  try:
    url = 'https://apod.nasa.gov/apod/astropix.html'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    img_tag = soup.find('img')
    if img_tag is not None:
      # Grab parent (<a>[href]) rather than <img>[src] for FULL RES URL
      a = img_tag.find_parent('a')
      img_url = 'https://apod.nasa.gov/apod/' + a['href']
      description = img_tag.find_next('p').text.strip()
      return img_url, description
    else:
      messagebox.showerror("Error", "The post contains no accepted image formats")
  except requests.RequestException as e:
    messagebox.showerror("Error",f"Failed to fetch APOD data: {e}")
  return None, None

# # Request the image and open it with PIL
# image_response = requests.get(img_url)
# image = Image.open(BytesIO(image_response.content))

""" # Adjust messagebox height if it exceeds screen height
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
      current_line_length += len(line) """

# # Display the image in a preview window
# root = tk.Tk()
# root.title('APOD Image Preview')

# # Set the width of the scrolledtext widget to screen width
# scroll_text = scrolledtext.ScrolledText(root,
# width=w // 10, height=10, wrap=tk.WORD)
# scroll_text.pack(fill=tk.BOTH, expand=True)
# scroll_text.insert(tk.END, concatenated_description)

# # Create a label and display the image
# image_label = tk.Label(root)
# image_label.pack()
# photo = ImageTk.PhotoImage(image)
# image_label.configure(image=photo)

# # Prompt user to confirm before setting the image as desktop background
# messagebox.showinfo('Image Preview', f'Image URL: {img_url}')
# response = messagebox.askquestion(
#     'Set Desktop Background', 'Set this image as your desktop background?')

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
      # new alt
      # script = 'tell application "Finder" set desktop picture to POSIX file "%s" end tell' % path
      # 2nd new alt
      # script = f'tell application "Finder" set desktop picture to POSIX file {path} end tell'
      os.system(f"/usr/bin/osascript -e '{script}'")
    messagebox.showinfo('Set Background Successful', 'Desktop background has been set.')
  except Exception as e:
    messagebox.showerror("Error", f"Failed to set the desktop background: {e}")

def select_save_path(image):
  root = tk.Tk()
  root.withdraw()
  file_path = filedialog.asksaveasfilename(defaultextension='.jpg', filetypes=[("JPEG","*.jpg"),("All files","*.*")])
  if file_path:
    try:
      image.save(file_path)
      print(f"Image saved to: {file_path}")
      return file_path
    except Exception as e:
      messagebox.showerror("Error", f"Failed to save image: {e}")
  return None

def main():
  root = tk.Tk()
  root.withdraw()

  w,h = get_resolution()

  img_url, description = fetch_apod_data()
  if not img_url:
    return

  response = requests.get(img_url)
  image = Image.open(BytesIO(response.content))
  photo = ImageTk.PhotoImage(image)

  image_label = tk.Label(root, image=photo)
  image_label.pack()
  root.update()

  description_label = tk.Label(root, text=description, wraplength=w)
  description_label.pack()

  messagebox.showinfo('Image Preview', f'Image URL: {img_url}')
  user_response = messagebox.askquestion('Set Desktop Background', 'Set this image as your desktop background?')

  # ask to save
  if response == '  ':
    image_path = select_save_path()
    if image_path:
      set_desktop_background(image_path)
  else:
    messagebox.showinfo('Set Background Declined','Desktop background has not been changed.')
  
  root.mainloop()

if __name__ == "__main__":
  threading.Thread(target=main).start()



