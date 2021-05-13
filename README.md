# cdc-lesson-tracker

Monitoring script for the CDC 2B motorcycle license practical lessons & RTT/BTT/PT booking website.

Works for single user only.

The `cdc_camper.py` script does the following:

* Login to website
* Wait for user to complete recaptcha
* Find booked sessions (if any)
* Find available sessions for next practical lesson / RTT / BTT / PT
* Compare booked session with earliest available session
  * if earlier session available: send email to configured email address
  * if no earlier session available / no lesson booked: do nothing unless `notify_always` config is set True
* if `stay_alive` config is set to True: Sleep for `refresh_rate` config time and do the whole thing again (except login); else: quit

## Prerequisites

### Install dependencies

First, you need to install Python on your PC: <https://realpython.com/installing-python/> (not needed on Ubuntu).

Then, install Chrome and Chromedriver. For Linux, run

```bash
sudo apt install chromium-browser chromium-chromedriver
```

For Windows, you need to follow the steps mentioned in: <https://chromedriver.chromium.org/getting-started>.

Then, you have to install some dependencies to make the script work via pip (on Ubuntu/Windows/Mac)

```bash
pip3 install -r requirements.txt
```

### Create config.yml

In order to work properly, you must create a config file with your credentials.

A file `config.yml` has to be created to read configurations. Here is an example:

```yml
###########################
# email notification config
############################

# the email SMTP server of your email server (just google it for gmail, etc.)
smtp_server: 'smtp.office365.com'
# the email SMTP server port of your email server (just google it for gmail, etc.)
smtp_port: 587
# your email address
smtp_user: 'test@outlook.com'
# your email password
smtp_pw: 'pw123'
# the email address which should be shown as sender (should be same as smtp_user)
from_email: 'test@outlook.com'

###########################
# user config
###########################

# your cdc username (with which you login to the CDC website / app)
username: 00123456
# your cdc password (with which you login to the CDC website / app)
password: 123456
# your email address (can be the same as above)
to_email: "test@outlook.com"
# whether you want to check for practical lessons etc.
check_practical: True
check_btt: True
check_rtt: True
check_pt: True
check_rr: True
# whether you want to be notified even though the lesson is after your earliest booking
notify_always: True
# whether you want the bot to run continuously
stay_alive: True
# how long the bot should wait between each run, in seconds
refresh_rate: 60
```

Store the `config.yml` in the project directory. No worries regarding your credentials, the file is ignored by the `.gitignore` file.

## Run it

After cloning and creation of the config file, the script can be easily executed by running

```bash
python3 cdc_camper.py
```

Once the website spins off, you need to solve the recaptcha. From there on, you can just keep the browser open in the background. It will refresh itself and notify you via email alerts.
