
# JordanTracker

## About

JordanTracker is an automated Python script to post a _ZOLEO_ device user's current location to slack or other social media (coming soon).

## Why?

My housemate decided that it would be fun to bike across the country, and I wanted to automate how friends and family were updated on his location.
Since _ZOLEO_ devices (the gps that he took with him), don't have a REST API available, I decided to parse the automated emails that are sent every time he checks in.

I also wanted an excuse to build a decent python app, and integrate with slack and social media backends.

## Installation

JordanTracker is designed to run in a virtual environment using poetry. It is currently a single run script, and I've set up a cronjob to run it every 30mins for my use. 

Installation steps

- clone this repository 
- edit the *example_config.py* to include your login info and save as *config.py*
- run `poetry install` from the directory with the *pyproject.toml* file.
- if you want to automate the script, create a cronjob that executes `poetry run jordantracker` from the directory with the *pyproject.toml* file.

