import re

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

def get_disp_data():
  import subprocess
  result = subprocess.run(['system_profiler SPDisplaysDataType'], capture_output=True, text=True) #, shell=True)
  return result.stdout

def mac_dual_display(text=get_disp_data()):
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
    for d in match_list:
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
  return displays_list


""" test scripts """
# (1)
""" 
tell application "System Events"
    tell every desktop
        set picture to ""
    end tell
end tell 
"""
# (1.1)
""" 
tell application "System Events" to tell every desktop to set picture to ""
"""