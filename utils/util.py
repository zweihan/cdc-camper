import datetime
import os
import yaml


def reload_config_yml() -> dict:
    global config
    config = {}
    config_file_path = f'{os.path.dirname(os.path.realpath(__file__))}/../config.yml'
    if not os.path.isfile(config_file_path):
        raise Exception("Please create config.yml first")
    with open(config_file_path, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return config


def clean_appium_avd_env():
    # kill all running processes & delete files before the first run
    # this is to prevent the following issues
    # - "Cannot find any free port in range 8200..8299" appium error
    # - "System UI is not responding" emulator error (which then blocks the UI from finding the right element)
    # - "emulator: ERROR: A snapshot operation for '<emulator>' is pending and timeout has expired. Exiting"
    os.system("pkill -f appium || true")
    os.system("pkill -f qemu || true")
    os.system("pkill -f adb || true")
    for emulator in config['android_emulator_names']:
        os.system(
            f"rm -f ~/.android/avd/{emulator}.avd/*.lock")


# converts custom format date (16/Jan/2021) and time (10:20 - 12:00) to datetime
def convert_to_date_time(date_str: str, time_str: str) -> datetime:
    # take only start time for date_time creation
    time_str = time_str.split(' ')[0]
    try:
        return datetime.datetime.strptime(f'{date_str} | {time_str}', '%d/%b/%Y | %H:%M')
    except ValueError:
        return datetime.datetime.strptime(f'{date_str} | {time_str}', '%d/%m/%Y | %H:%M')


# Returns true if date is not excluded by filter
def is_date_in_range(date_time: datetime.datetime, date_filter: str) -> bool:
    if date_filter == 'na':
        return True
    date_weekday = date_time.strftime('%A').lower()[:2]
    try:
        date_filter_weekdays = date_filter.split(';')
        if date_weekday in date_filter_weekdays:
            return True
        else:
            return False
    except Exception as e:
        print(
            f"An error occured parsing '{date_filter}': {e}")
        return True


# Returns true if time is not excluded by filter
def is_time_in_range(date_time: datetime.datetime, time_filter: str) -> bool:
    if time_filter == 'na':
        return True
    date_time_hour = date_time.hour
    try:
        date_filter_start_hour = int(time_filter.split('-')[0])
        date_filter_end_hour = int(time_filter.split('-')[1])
        # e.g. x = 13 -> 8 <= x < 14
        if date_time_hour >= date_filter_start_hour and date_time_hour < date_filter_end_hour:
            return True
        else:
            return False
    except Exception as e:
        print(
            f"An error occured parsing '{time_filter}': {e}")
        return True
