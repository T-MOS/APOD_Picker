import ctypes
import os
import platform
import tkinter as tk
from io import BytesIO
from tkinter import messagebox, scrolledtext, filedialog
import threading

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageTk