import sys
import numpy as np
import textwrap
from PIL import Image

def image_accessor(image):
  openInitial = Image.open(image)
  image_array = np.array(openInitial)
  return image_array

# ENCODE
def text_to_dec(text):
  with open(text, 'r',encoding="utf-8") as t:
    te = t.read()
    decimalized = np.array(bytearray(te, 'utf-8'))
    decimalShaped = pad_and_reshape_text_decimals(decimalized)
  return decimalShaped

def pad_and_reshape_text_decimals(decimal_array):
  fit = len(decimal_array) % 3
  rightPad = 0

  if fit != 0:
    rightPad = 3-fit

  padded = np.pad(decimal_array,(0,rightPad), mode = "constant").reshape(-1,3)
  return padded

def array_operations(padded_array):
  row_count = (len(padded_array)//len(image_array))+1
  cols = image_array.shape[1]
  zerows = np.zeros((row_count,cols,3))
  
  # flatten,add,rebuild
  flat_stacked = np.vstack((image_array,zerows)).reshape(-1,3)
  added_start = len(flat_stacked)-(row_count*cols)
  insert_stop = added_start+len(padded_array)
  for i in range(added_start,insert_stop):
    flat_stacked[i] = padded_array[i % len(padded_array)]
  rebuilt = flat_stacked.reshape(-1,cols,3).astype(np.uint8)
  
  text_embedded_image = Image.fromarray(rebuilt)
  return text_embedded_image


# DECODE 
def data_getter(image_array):
  # grab/flatten
  data_row = np.array(image_array[-1,...]).flatten()
  # trim padding
  trimmed = [num for num in data_row if num > 0]
  # characterize
  decoded_row = bytes(trimmed).decode('utf-8')
  return decoded_row

def printer(decoded_string):
  wrapped_description = textwrap.fill(decoded_string, width=50)
  print(f"{'*' * 50}\n{'APODescription':^50}\n{'-' * 50}\n{wrapped_description}\n{'*' * 50}")

# Run Conditions
if __name__ == "__main__":
  image_array = image_accessor(sys.argv[1]) # argv 1
  # 1) Encoding
  if len(sys.argv) == 3:
    decimal_shaped = text_to_dec(sys.argv[2]) # argv 2
    text_embedded = array_operations(decimal_shaped)
    text_embedded.save("test/embedded_iapetus.bmp")
    text_embedded.show()
  # 2) Decoding
  if len(sys.argv) == 2:
    decoded = data_getter(image_array)
    printer(decoded)
  else:
    sys.exit(1)
