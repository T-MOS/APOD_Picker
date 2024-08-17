import os
# 'Darwin':
script0 = f"""
tell application "Finder"
  set desktop picture to POSIX file "{path}"
end tell
"""
script0_1 = f"""
tell application "Finder" to set desktop picture to POSIX file "{path}"
"""


script1 = f"""
tell application "System Events"
  tell desktop 2
    set desktop picture to POSIX file "{path2}"
  end tell
end tell
"""
script1_1 = f"""
tell application "System Events" to tell desktop 2 to set desktop picture to POSIX file "{path2}" end tell
"""

script2 = f"""
tell application "Finder"
  tell desktop 2
    set desktop picture to POSIX file "{path2}"
  end tell
end tell
"""
script2_1 = f"""
tell application "Finder" to tell desktop 2 to set desktop picture to POSIX file "{path2}" end tell
"""

