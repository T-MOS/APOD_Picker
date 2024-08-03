# APOD Picker
Standalone image retriever/background setter

This script fetches the Astronomy Picture of the Day (APOD) from the NASA website, displays a preview, and gives you the option to set it as your desktop background/save the image locally.

## Dependencies

This script requires several Python packages. Ensure you've installed all required packages with the command `pip install -r requirements.txt`. Use `apt` or other appropriate package manager for individual packages (or python virtual environment) as needed.

For my testers:
`python -m venv .`
Mac:
`source bin/activate`

Windows:
`source \Scripts\Activate.ps1`

Both: `pip install -r requirements.txt`
run via: `python apod_picker_main.py`
## Usage

To run the script, simply navigate to the directory containing the script and run the command `python apod_picker.py`.

The script will fetch the APOD and display it in a new window. It will also display any associated description of the image. You will then be prompted to confirm whether you want to set the image as your desktop background and/or save it locally.

## Platform Specifics

This script is designed to work on Windows, Linux, and macOS.
