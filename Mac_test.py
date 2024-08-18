import subprocess,os

script_wrapper = """
tell application "System Events"
    {}      
end tell
      """
inner_1 = """ 
set currDesktop to item {idx} of desktops
set currDesktop's picture to "{image_path}" 
"""

inner_2 = """ 
set currDesktop to item {idx} of desktops
set currDesktop's picture to POSIX file "{image_path}" 
"""

images = [os.path.join(root,file) for root,subdir,files in os.walk("test_images/") for file in files]

# def set_wallpapers(images):

#     script_contents = ""
#     for i, img in enumerate(images):
#         idx = i+1
#         script_contents += inner_1.format(idx=idx, image_path=img)

#     scripts = script_wrapper.format(script_contents)
#     # subprocess.check_call(scripts, shell=True)
#     os.system(f"/usr/bin/osascript -e '{scripts}'")

def set_wallpapers(images):

    script_contents = ""
    for i, img in enumerate(images):
        idx = i+1
        script_contents += inner_1.format(idx=idx, image_path=img)
    oneoff = r"""
        set currDesktop to item 1 of desktops
        set currDesktop's picture to "test_images/EtnaLightPillar_Tine_5100.jpg"
    """
    scripts = script_wrapper.format(oneoff)
    # subprocess.check_call(scripts, shell=True)
    os.system(f"/usr/bin/osascript -e '{scripts}'")

set_wallpapers(images) 
