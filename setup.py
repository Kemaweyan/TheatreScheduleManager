#!/usr/bin/env python3

from setuptools import setup, find_packages
from theatre.Preferences import is_windows

entry_points = {
    "gui_scripts": [
        "theatre=theatre.Theatre:start"
    ]
}

data_files = ["icons/*.png"]

if is_windows():
    data_files.append("icons/black_white_2_gloss/*.theme")
    data_files.append("icons/black_white_2_gloss/actions/*.png")

setup(
    name = "theatre",
    version = "2.0",
    fullname = "Theatre Shedule Manager",
    description = "Threatre shedule viewer and editor",
    author = "Taras Gaidukov",
    author_email = "kemaweyan@gmail.com",
    keywords = "shedule theatre",
    long_description = """The program is a theatre shedule manager.
                        You can create and edit shedules, sync it with
                        official website of the theatre and print it.""",
    url = "http://www.operetta.kharkiv.ua/",
    license = "GPLv3",
    package_data = {"theatre": data_files},
    packages=find_packages(),
    entry_points = entry_points
)
