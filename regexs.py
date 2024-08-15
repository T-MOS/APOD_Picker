import re

def mac_display_info(text):
  SysParam_pattern = re.compile(r"(\w+ \w+):\r?\n(?:\s+.*\r?\n)*?\s+Resolution: (\d+ x \d+)(?:.*\r?\n)*?(?:\s+UI Looks like: (\d+ x \d+))?(?:.*\r?\n)*?\s+Main Display: (Yes|No)")
  matches = SysParam_pattern.findall(text)
  
  displays_list = []
  if len(matches)>1:
    for i, match in enumerate(matches, 1):
      display_name, resolution, looks_like, main_display = match
      display_info = {
        "Display Name": display_name,
        "Resolution": resolution,
        "Looks Like": looks_like,
        "Main Display": main_display
      }
      displays.append(display_info)
