import random
import requests
from datetime import datetime
from tkinter import messagebox
from bs4 import BeautifulSoup

# example archive url format, replace '240623' with appropriate format generated suffix (e.g, ".../ap{YYMMDD}.html")
""" https://apod.nasa.gov/apod/ap240623.html """

# beginning (ideally) 5/20/95 -> curr
def urlRandomizer():
  """ The following ensures ~1,000 years of usable random outputs
  if APOD archive posts adopt 3 digit (YyyMmDd) url structure after 2099 
  (e.g, 'ap1000411.html' for April 11, 2100)""" 
  yearsElapsed = datetime.now().year - 1995
  yy = random.randint(0,yearsElapsed)
  if yy < 10:
    yyStr = str(yy).zfill(2)
  elif 9 < yy < 100:
    yyStr = str(yy)[-2:]
  else:
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
      # Find image's title in <center> w/ child <b>
      post_title = soup.find('b').text.strip()
      # Extract description text
      description = img_tag.find_next('p').text.strip()
      # Grab parent (<a>[href]) rather than <img>[src] for FULL RES URL
      a = img_tag.find_parent('a')
      img_url = baseUrl + a['href']

      return img_url, description, post_title 
  except requests.RequestException as e:
    messagebox.showerror("Error",f"Failed to fetch APOD data: {e}")
  return None, None, None

print(urlRandomizer())
