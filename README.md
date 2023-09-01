
# ZoleoTracker

## About

ZoleoTracker is an automated Python script to post a _ZOLEO_ device user's current location to slack or other social media (coming soon).

## Why?

My housemate decided that it would be fun to bike across the country, and I wanted to automate how friends and family were updated on his location.
Since _ZOLEO_ devices (the gps that he took with him), don't have a REST API available, I decided to parse the automated emails that are sent every time he checks in.

I also wanted an excuse to build a python app that integrates with slack and social media backends!

## Getting Started

ZoleoTracker is designed to run in a python virtual environment using poetry. It is a single run script, and I've set up a cronjob to run it every 30mins for my use. 

1. Clone this repository
2. Edit the *config.py* to include your email server and inbox settings.
3. Set environment variables for `SLACK_TOKEN`, `EMAIL_ACCOUNT`, and `EMAIL_PASSWORD`
4. Run `poetry install` from the high level directory.
5. If you want to automate the script, create a cronjob that executes `poetry run ZoleoTracker` from the high level project directory.

Example cronjob: `*/30 * * * * cd {project_directory} && ./runtracker.zsh` Where `runtracker.zsh` just calls `poetry run zoleotracker` with the appropriate permissions and environment variables.

## Contributions

To contribute, please visit the [contributing](CONTRIBUTING.md) guidelines.

### Pending Features

In no particular order, here are some of the future plans for ZoleoTracker:

- Finish test coverage
- CI/CD coverage
- Add X(Twitter) integration
- Add Threads / Instagram integration
- Move from CSV file location data to SQL
- Package as an application that can run at any chosen interval
- Update to use _ZOLEO_ API when available (2024?)
