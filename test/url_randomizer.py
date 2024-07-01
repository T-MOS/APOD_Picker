import random
import requests
from tkinter import messagebox
from bs4 import BeautifulSoup

# example archive url format, replace '240623' with appropriate format generated suffix (e.g, ".../ap{YYMMDD}.html")
""" https://apod.nasa.gov/apod/ap240623.html """

# beginning (ideally) 5/20/95 -> curr
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

""" def fetch_apod_data():
  # Send GET request to APOD website and parse HTML response with BeautifulSoup
  baseUrl = 'https://apod.nasa.gov/apod/'
  testCase1 = 'https://apod.nasa.gov/apod/2406'
  testCase2 = 'https://apod.nasa.gov/apod/ap240626.html'
  try:
    response = requests.get(testCase2)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    img_tag = soup.find('img')
    if img_tag is not None:
      # Grab parent (<a>[href]) rather than <img>[src] for FULL RES URL
      a = img_tag.find_parent('a')
      img_url = baseUrl + a['href']
      description = img_tag.find_next('p').text.strip()
      return img_url, description
    else:  
      while img_tag is None:
        try:
          randomPost = baseUrl + urlRandomizer()
          response = requests.get(randomPost)
          response.raise_for_status()
          soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
          img_tag = soup.find('img')
        except requests.RequestException as e:
          messagebox.showerror("Error",f"{e}")
  except requests.RequestException as e:
    messagebox.showerror("Error",f"Failed to fetch APOD data: {e}")
  return None, None """

def fetch_apod_data():
  # Send GET request to APOD website and parse HTML response with BeautifulSoup
  baseUrl = 'https://apod.nasa.gov/apod/'
  testCase1 = 'https://apod.nasa.gov/apod/2406'
  testCase2 = 'https://apod.nasa.gov/apod/ap240626.html'
  try:
    response = requests.get(testCase2)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    img_tag = soup.find('img')
    while img_tag is None:
      try:
        randomPost = baseUrl + urlRandomizer()
        response = requests.get(randomPost)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
        img_tag = soup.find('img')
      except requests.RequestException as e:
        messagebox.showerror("Error",f"{e}")
    else:
      # Grab parent (<a>[href]) rather than <img>[src] for FULL RES URL
      a = img_tag.find_parent('a')
      img_url = baseUrl + a['href']
      description = img_tag.find_next('p').text.strip()
      return img_url, description      
  except requests.RequestException as e:
    messagebox.showerror("Error",f"Failed to fetch APOD data: {e}")
  return None, None

print(fetch_apod_data())
