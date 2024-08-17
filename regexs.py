import re

def sanitize_filename(url_string):
  pattern = r'([^/]+)\.[^.]+$' #read: "after last '/' before last '.'"
  rinsed = re.search(pattern, url_string)
  return rinsed

rawString = r"""Apple M1:

      Chipset Model: Apple M1
      Type: GPU
      Bus: Built-In
      Total Number of Cores: 8
      Vendor: Apple (0x106b)
      Metal Support: Metal 3
      Displays:
        Color LCD:
          Display Type: Built-In Retina LCD
          Resolution: 2560 x 1600 Retina
          Main Display: Yes
          Mirror: Off
          Online: Yes
          Automatically Adjust Brightness: Yes
          Connection Type: Internal
        Sidecar Display:
          Resolution: 2732 x 2048
          UI Looks like: 1366 x 1024 @ 60.00Hz
          Framebuffer Depth: 24-Bit Color (ARGB8888)
          Mirror: Off
          Connection Type: AirPlay
          Virtual Device: Yes """

def mac_display_info(text):
  # Disp. name, wdim x hdim, UI scale(looks like)
  alt_pattern = r"\s+(\w+ \w+): ?\r?\n(?:\s+.*\r?\n)*?\s+Resolution: (\d+ x \d+)(?:.*?\r?\n)*?(?:\s+UI Looks like: (\d+ x \d+))?(?:.*?\r?\n)*?"
  matches = alt_pattern.findall(text)
  
  displays_list = []
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

def mac_dual_display(text):
  pattern = r"\s+(\w+ \w+): ?\r?\n"
  matches = re.findall(pattern,text)
  lines = text.splitlines()
  indices = list()

  # extract the 2 blocks of text corresponding to disp.s' info
  for line in lines:
    for i in matches:
      if i in line:
        indices.append(lines.index(line))
  if len(indices) == 2:
    a = [lines[i].strip() for i in range(indices[0],indices[1])]
    b = [lines[i].strip() for i in range(indices[1],len(lines))]
    match_list = [a,b]

    displays_list = list()
    for i,d in enumerate(match_list,1):
      main = False
      resolutionTuple = ()
      scale = None
      for line in d:
        # Reso's
        resolutionsPattern = r"\d+[^ x.]\d+"
        if "Resolution:" in line:
          digits = re.findall(resolutionsPattern,line)
          resolutionTuple = tuple(digits)
        elif "Looks" in line:
          digits = re.findall(resolutionsPattern,line)
          scale = tuple(digits)
        # Primary
        elif "Main" in line:
          main = True
      display_info = {
      "Resolution": resolutionTuple,
      "UI Scale": scale,
      "Primary": main
      }  
      displays_list.append(display_info)
  return 
      