import time
import sys
import requests


def rate_limited_request(url):
    # Call library catalog search, by building URL
    # searchscope=10 is the code for all libraries in Barcelona
    max_retries = 1
    retries = 0
    success = False
    response = None
    while not success and retries <= max_retries:
        try:
            response = requests.get(url)
            success = True
        except Exception as e:
            wait = retries * 10
            print(f'Error! Waiting {wait} secs and re-trying...')
            sys.stdout.flush()
            time.sleep(wait)
            retries += 1

    # site is using rate-limiting, so we wait 1 second between requests
    time.sleep(1)
    return response