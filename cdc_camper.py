#!/usr/bin/env python3

import tempfile
import argparse
import datetime
import os
import platform
import smtplib
import socket
import sys
from time import sleep
import traceback
from email.message import EmailMessage


from cdc_website import CDCWebsite, Types
from utils.logger import Logger


from utils.util import reload_config_yml


# converts custom format date (16/Jan/2021) and time (10:20 - 12:00) to datetime
def convert_to_date_time(date_str: str, time_str: str) -> datetime:
    # take only start time for date_time creation
    time_str = time_str.split(' ')[0]
    return datetime.datetime.strptime(f'{date_str} | {time_str}', '%d/%b/%Y | %H:%M')


# sends out an email to the user, if any of the following conditions is true:
# a) there are available sessions AND user has not booked any yet
# b) there are available sessions AND earliest available session is earlier than booked session of user
def inform_user_if_earlier_session_available(user, type: str):
    # define base vars
    inform_user = False
    mail_body = ""

    # define vars based on type (practical/rtt/btt)
    if "Windows" in platform.system():
        last_cdc_session_file_path = f'{tempfile.gettempdir()}\\last_cdc_session_{user}_{type}'
    elif 'Linux' in platform.system():
        last_cdc_session_file_path = f'{tempfile.gettempdir()}/last_cdc_session_{user}_{type}'

    available_sessions = {}
    booked_sessions = {}
    if type == Types.PRACTICAL:
        available_sessions = cdc_website.available_sessions_practical
        booked_sessions = cdc_website.booked_sessions_practical
    elif type == Types.BTT:
        available_sessions = cdc_website.available_sessions_btt
        booked_sessions = cdc_website.booked_sessions_btt
    elif type == Types.RTT:
        available_sessions = cdc_website.available_sessions_rtt
        booked_sessions = cdc_website.booked_sessions_rtt
    elif type == Types.PT:
        available_sessions = cdc_website.available_sessions_pt
        booked_sessions = cdc_website.booked_sessions_pt

    if len(available_sessions) == 0:
        # delete last cdc session file to ensure a clean state once
        # there are sessions available yet
        if os.path.exists(last_cdc_session_file_path):            
            os.remove(last_cdc_session_file_path)
        logger.info(
            f"There are no {type} sessions available for booking yet, exit early")
        return
    else:
        if type == Types.PRACTICAL:
            mail_body += f"There are the following available sessions for your ({user}) next 2B practical lesson ({cdc_website.lesson_name_practical}) @ CDC:\n\n"
        else:
            mail_body += f"There are the following availuserable {type.upper()} sessions for you ({user}):\n\n"

        index = 1
        for i, (available_session_date, available_session_times) in enumerate(available_sessions.items()):
            for available_session_time in available_session_times:
                mail_body += f"- Available session #{index}: {available_session_date} @ {available_session_time}\n"
                index += 1

        if len(booked_sessions) > 0:
            mail_body += "\nYou have already booked the following session(s):\n\n"
            for i, (booked_session_date, booked_session_time) in enumerate(booked_sessions.items(), 1):
                mail_body += f"- Booked session #{i}: {booked_session_date} @ {booked_session_time}\n"

            # Step 2: Find out if there is an earlier slot available
            booked_session_date = list(booked_sessions.keys())[0]
            booked_session_time = list(booked_sessions.values())[0]
            booked_session_datetime = convert_to_date_time(
                booked_session_date, booked_session_time)
            earliest_available_session_date = None
            earliest_available_session_time = None
            # TODO: Make accessing of the first item of the dict easier
            for i, (available_session_date, available_session_time) in enumerate(available_sessions.items()):
                if i == 0:
                    earliest_available_session_date = available_session_date
                    # it's a list, so take first entry always
                    earliest_available_session_time = available_session_time[0]
                    break

            # convert to real datetime for proper date comparison
            earliest_available_session_datetime = convert_to_date_time(
                earliest_available_session_date, earliest_available_session_time)

            # only send email if earliest available session is before booked one
            if earliest_available_session_datetime < booked_session_datetime:
                mail_body += "\n-> There is an earlier session available - Consider rebooking!"

                # check if email has been sent out already with that earliest available session
                earliest_available_session_datetime_string = earliest_available_session_datetime.strftime(
                    '%Y%m%d-%H%M')
                if not os.path.isfile(last_cdc_session_file_path):
                    inform_user = True
                    # write datetime of earliest available session into file
                    with open(last_cdc_session_file_path, 'w') as stream:
                        stream.write(
                            earliest_available_session_datetime_string)
                else:
                    try:
                        with open(last_cdc_session_file_path, 'r+') as stream:
                            last_cdc_session_datetime = datetime.datetime.strptime(
                                stream.read().replace("\n", ""), '%Y%m%d-%H%M')
                            if last_cdc_session_datetime == earliest_available_session_datetime:
                                logger.info(
                                    "No need to send out another email as there is no earlier session available")
                            else:
                                inform_user = True
                                # write datetime of earliest available session into file
                                stream.seek(0)
                                stream.write(
                                    earliest_available_session_datetime_string)
                                stream.truncate()
                    except Exception as e:
                        inform_user = True
            else:
                mail_body += "\n-> There is no earlier session available."

                # Inform user always, if configured
                if config['notify_always']:
                    inform_user = True
        else:
            mail_body += "\nYou have not booked any session yet!"
            inform_user = True

            # Step 3: Send email about latest updates (if there is something worth notifying)
        if mail_body != "":
            logger.info(mail_body)

    if inform_user:
        # send email
        mailserver = None
        try:
            mailserver = smtplib.SMTP(
                config['smtp_server'], config['smtp_port'])
            mailserver.ehlo()
            mailserver.starttls()
            mailserver.login(config['smtp_user'], config['smtp_pw'])

            from_email_address = config['from_email']
            to_email_address = config['to_email']

            msg = EmailMessage()
            msg.set_content(mail_body)
            msg['From'] = from_email_address
            msg['To'] = to_email_address
            msg['Subject'] = f"CDC {'Practical Lesson' if type == 'practical' else type.upper()} Sessions"

            logger.info(f"Sending out email to {to_email_address}")
            mailserver.sendmail(from_addr=from_email_address,
                                to_addrs=to_email_address, msg=msg.as_string())
        except socket.gaierror:
            logger.warning(
                "Socket issue while sending email - Are you in VPN/proxy?")
        except Exception as e:
            logger.error(f"Something went wrong while sending an email: {e}")
        finally:
            if mailserver != None:
                mailserver.quit()


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()

    PARSER.add_argument('--log_level', type=int,
                        help='The log level (10-50)', default=20, required=False)
    PARSER.add_argument('--headless',
                        help='Headless mode', required=False, action='store_true')
    ARGS = PARSER.parse_args()

    logger = Logger.logger
    logger.setLevel(ARGS.log_level)

    config = reload_config_yml()

    try:
        logger.info(f"------------------------------")
        logger.info(f"Running for user {config['username']}")
        logger.info(f"------------------------------")

        # Step 1: Open CDC website and login
        with CDCWebsite(config['username'], config['password'], headless=ARGS.headless) as cdc_website:
            cdc_website.open_home_website()
            cdc_website.login()

            while True:
                # Step 2: Get booking information
                cdc_website.open_booking_overview()
                cdc_website.get_booked_lesson_date_time()

                # Step 3: Check for practical lesson availability
                if config['check_practical']:
                    cdc_website.open_practical_lessons_booking(
                        type=Types.PRACTICAL)
                    if "REVISION" in cdc_website.lesson_name_practical:
                        logger.debug(
                            "No practical lesson available for user, seems user has completed practical lessons")
                    else:
                        cdc_website.get_all_session_date_times(
                            type=Types.PRACTICAL)
                        cdc_website.get_all_available_sessions(
                            type=Types.PRACTICAL)
                        if cdc_website.can_book_next_practical_lesson:
                            inform_user_if_earlier_session_available(
                                config['username'], type=Types.PRACTICAL)

                # # Step 4: Check for road revision availability
                # if config['check_rr']:
                #     cdc_website.open_practical_lessons_booking(type=Types.ROAD_REVISION)
                #     if "REVISION" in cdc_website.lesson_name_practical:
                #         logger.debug(
                #             "No practical lesson available for user, seems user has completed practical lessons")
                #     else:
                #         cdc_website.get_all_session_date_times(
                #             type=Types.PRACTICAL)
                #         cdc_website.get_all_available_sessions(
                #             type=Types.PRACTICAL)
                #         if cdc_website.can_book_next_practical_lesson:
                #             inform_user_if_earlier_session_available(
                #                 config['username'], type=Types.PRACTICAL)

                # Step 4: Check for btt availability as well
                if config['check_btt']:
                    if cdc_website.open_theory_test_booking_page(type=Types.BTT):
                        cdc_website.get_all_session_date_times(type=Types.BTT)
                        cdc_website.get_all_available_sessions(type=Types.BTT)
                        inform_user_if_earlier_session_available(
                            config['username'], type=Types.BTT)
                    else:
                        logger.debug("BTT not bookable for user")

                # Step 4: Check for rtt availability as well
                if config['check_rtt']:
                    if cdc_website.open_theory_test_booking_page(type=Types.RTT):
                        cdc_website.get_all_session_date_times(type=Types.RTT)
                        cdc_website.get_all_available_sessions(type=Types.RTT)
                        inform_user_if_earlier_session_available(
                            config['username'], type=Types.RTT)
                    else:
                        logger.debug("RTT not bookable for user")

                # Step 6: Check for pt (practical test) availability as well
                if config['check_pt']:
                    if cdc_website.open_practical_test_booking_page():
                        cdc_website.get_all_session_date_times(type=Types.PT)
                        cdc_website.get_all_available_sessions(type=Types.PT)
                        if cdc_website.can_book_pt:
                            inform_user_if_earlier_session_available(
                                config['username'], type=Types.PT)
                    else:
                        logger.debug("PT not bookable for user")

                # Step 7: Check if stay_alive is configured
                if not config['stay_alive']:
                    break
                else:
                    logger.debug(f"Sleeping for {config['refresh_rate']}s...")
                    sleep(config['refresh_rate'])

            cdc_website.logout()
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        sys.exit(1)
