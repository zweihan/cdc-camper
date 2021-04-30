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
# email notification config
smtp_server: 'smtp.office365.com'
smtp_port: 587
smtp_user: 'test@outlook.com'
smtp_pw: 'pw123'
from_email: 'test@outlook.com'
# user config
username: 00123456
password: 123456
to_email: "test@outlook.com"
check_practical: True
check_btt: True
check_rtt: True
check_pt: True
check_rr: True
notify_always: True
stay_alive: True
refresh_rate: 60
```

Store the `config.yml` in the project directory. No worries regarding your credentials, the file is ignored by the `.gitignore` file.

## Run it

After cloning and creation of the config file, the script can be easily executed by running

```bash
python3 cdc_camper.py
```

Once the website spins off, you need to solve the recaptcha. From there on, you can just keep the browser open in the background. It will refresh itself and notify you via email and desktop alerts.
