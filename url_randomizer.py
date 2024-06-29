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

# example archive url format, replace '240623' with appropriate format generated suffix (e.g, ".../ap{YYMMDD}.html")
""" https://apod.nasa.gov/apod/ap240623.html """

def fetch_apod_data():
  # Send GET request to APOD website and parse HTML response with BeautifulSoup
  try:
    url = 'https://apod.nasa.gov/apod/astropix.html'
    # url = 'https://apod.nasa.gov/apod/ap240625.html'
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

i,d = fetch_apod_data()