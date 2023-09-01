
# ZoleoTracker

## About

ZoleoTracker is an automated Python script to post a _ZOLEO_ device user's current location to slack or other social media (coming soon).

## Why?

My housemate decided that it would be fun to bike across the country, and I wanted to automate how friends and family were updated on his location.
Since _ZOLEO_ devices (the gps that he took with him), don't have a REST API available, I decided to parse the automated emails that are sent every time he checks in.

I also wanted an excuse to build a python app that integrates with slack and social media backends!

## Example Slack Message
![Example-slack](https://github.com/ASignificantOtter/ZoleoTracker/assets/140848822/480824e3-d5b5-4857-8b7d-0385b1f4ffbf)


## Getting Started

ZoleoTracker is designed to run in a python virtual environment using poetry. It is a single run script, and I've set up a cronjob to run it every 30mins for my use. 

1. Clone this repository
2. Edit the *config.py* to include your email server and inbox settings.
3. Set environment variables for `SLACK_TOKEN`, `EMAIL_ACCOUNT`, and `EMAIL_PASSWORD`
4. Run `poetry install` from the high level directory.
5. If you want to automate the script, create a cronjob that executes `poetry run ZoleoTracker` from the high level project directory.

Example cronjob: `*/30 * * * * cd {project_directory} && ./runtracker.zsh` 

Example `runtracker.zsh`:

```
#!/bin/zsh
export SLACK_TOKEN="secret-slack-token"
export EMAIL_ACCOUNT="user@mail.com"
export EMAIL_PASSWORD="mailapppassword"
poetry run zoleotracker
```


## Contributions

To contribute, please visit the [contributing](CONTRIBUTING.md) guidelines.
