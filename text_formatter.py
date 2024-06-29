import re

description = """ Explanation: 
Jets of material blasting
from newborn stars, are captured in this James Webb Space Telescope
close-up of the Serpens Nebula.

The powerful protostellar outflows are bipolar,
twin jets spewing
in opposite directions.

That result was expected, but has only now come into clear view
with Webb's
detailed exploration
of the active young star-forming region.

Brighter foreground stars exhibit Webb's characteristic
diffraction spikes.

At the Serpens Nebula's estimated distance of 1,300 light-years, this
cosmic close-up frame is about 1 light-year across.

 Tomorrow's picture: Olber's comet

 Authors & editors:
Robert Nemiroff
(MTU) &
Jerry Bonnell (UMCP)
NASA Official:  Amber Straughn
Specific rights apply.
NASA Web Privacy,
Accessibility Notices

A service of:
ASD at
NASA /
GSFC,
 NASA Science Activation
& Michigan Tech. U. """

def OLD_format_description(text):
  if text:
    lines = text.splitlines()
    concatenated_description = ''
    current_line_length = 0
    for line in lines:
      if len(line) >0:
        line = line.strip() # Remove whitespace at the beginning and end of the line
        if line.startswith('Explanation:'):
          concatenated_description += ''
          print(concatenated_description)
          current_line_length = len(line)
        elif line.startswith('Tomorrow'):
          return concatenated_description
        else:
          # line = line.replace('\n', ' ') # Replace line breaks within the line with a space
          if current_line_length + len(line) > 1920 // 10:
            concatenated_description += '\n' + line
            current_line_length = len(line)
          else:
              if concatenated_description == '':
                concatenated_description += line
              else:
                concatenated_description += " "+line
                current_line_length += len(line)
    return concatenated_description
  return None

def simple_formatter(text):
  if text:
    lines = text.splitlines()
    concatenated_description = ''
    # current_line_length = 0
    for line in lines:
      if len(line) >0:
        line = line.strip() # Remove whitespace at the beginning and end of the line
        if line.startswith('Explanation:'):
          concatenated_description += ''
          print(concatenated_description)
          # current_line_length = len(line)
        elif line.startswith('Tomorrow'):
          return concatenated_description
        else:
          if concatenated_description ==  "":
            concatenated_description += line
          else:
            concatenated_description += " " + line
    return concatenated_description
  return None
# simple = simple_formatter(description)
# stupid = OLD_format_description(description)
# with open('simple.txt', 'a') as f:
#   print(simple + "\n" + stupid, file=f)

filename = " 13b/Olbers Comet? "

def sanitize_filename(input_string):
  # Define disallowed filename chars' regex pattern
  unsanitized = input_string.strip()
  pattern1 = r'[\:*?"<>|]'
  rinsed = re.sub(pattern1, "", unsanitized)
  pattern2 = r'[ \/]'
  sanitized = re.sub(pattern2, '_', rinsed)
  return sanitized

print(sanitize_filename(filename))