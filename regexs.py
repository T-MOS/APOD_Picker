import re

dummyString = "Apple M1:\r\n\nChipset Model: Apple M1\r\n      Type: GPU\r\n      Bus: Built-In\r\n      Total Number of Cores: 8\r\n      Vendor: Apple (0x106b)\r\n      Metal Support: Metal 3\r\n      Displays:\r\n        Color LCD:\r\n          Display Type: Built-In Retina LCD\r\n          Resolution: 2560 x 1600 Retina\r\n          Main Display: Yes\r\n          Mirror: Off\r\n          Online: Yes\r\n          Automatically Adjust Brightness: Yes\r\n          Connection Type: Internal\r\n        Sidecar Display:\r\n          Resolution: 2732 x 2048\r\n          UI Looks like: 1366 x 1024 @ 60.00Hz\r\n          Framebuffer Depth: 24-Bit Color (ARGB8888)\r\n          Mirror: Off\r\n          Connection Type: AirPlay\r\n          Virtual Device: Yes"

def mac_display_info(text):
  SysParam_pattern = re.compile(r"(\w+ \w+):\r?\n(?:\s+.*?\r?\n)*?\s+Resolution: (\d+ x \d+)(?:.*?\r?\n)*?(?:\s+UI Looks like: (\d+ x \d+))?(?:.*?\r?\n)*?\s+Main Display: (Yes|No)")
  alt_pattern = 
  matches = SysParam_pattern.findall(text)
  
  displays_list = []
  # if len(matches)>1:
  for i, match in enumerate(matches, 1):
    display_name, resolution, looks_like, main_display = match
    display_info = {
      "Display Name": display_name,
      "Resolution": resolution,
      "Looks Like": looks_like,
      "Main Display": main_display
    }
    displays_list.append(display_info)
  return matches
