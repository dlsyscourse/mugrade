import os
import sys
import numpy as np
import requests
import pickle
import base64
import json
import inspect
import copy
import gzip
import re
import types
import pytest


"""
Note: This use of globals is pretty ugly, but it's unclear to me how to wrap this into 
a class while still being able to use pytest hooks, so this is the hacky solution for now.
"""

_server_url = "https://mugrade.dlsyscourse.org/_/api/"
_values = []
_submission_key = ""
_errors = 0


def b64_pickle(obj):
    return base64.b64encode(pickle.dumps(obj)).decode("ASCII")

def start_submission(func_name):
    """ Begin a submisssion to the mugrade server """
    response = requests.post(_server_url + "submission",
                             params = {"user_key": os.environ["MUGRADE_KEY"],
                                       "func_name": func_name})
    if response.status_code != 200:
        raise Exception(f"Error : {response.text}")
    return response.json()["submission_key"]

def submit_test():
    """ Submit a single grader test. """
    global _values, _submission_key, _errors
    response = requests.post(_server_url + "submission_test",
                             params = {"user_key": os.environ["MUGRADE_KEY"],
                                       "submission_key":_submission_key, 
                                       "test_case_index":len(_values)-1,
                                       "output":b64_pickle(_values[-1])})
    if response.status_code != 200:
        print(f"Error : {response.text}")
    elif response.json()["status"] != "Passed":
        print(f"Grader test {len(_values)} failed: {response.json()['status']}")
        _errors += 1
    else:
        print(f"Grader test {len(_values)} passed")



def publish(func_name):
    """ Publish an autograder. """
    global _values
    response = requests.post(server_url + "publish_grader",
                             params = {"user_key": os.environ["MUGRADE_KEY"],
                                       "func_name": func_name,
                                       "target_values": b64_pickle(_values),
                                       "overwrite": True})
    if response.status_code != 200:
        print(f"Error : {response.text}")
    else:
        print(response.json()["status"])


@pytest.mark.hookwrapper
def pytest_pyfunc_call(pyfuncitem):
    ## prior to test, initialize submission
    global _values, _submission_key, _errors
    _values = []
    _errors = 0
    func_name = pyfuncitem.name[7:]
    if os.environ["MUGRADE_OP"] == "submit":
        _submission_key = start_submission(func_name)
        print(f"\nSubmitting {func_name}...")

    # run test
    output = yield


    # raise excepton if tests failed (previously keep running)
    if os.environ["MUGRADE_OP"] == "submit":
        if _errors > 0:
            pytest.fail(pytrace=False)

    # publish tests
    if os.environ["MUGRADE_OP"] == "publish":
        #print(values)
        publish(func_name)



def submit(result):
    global _values
    _values.append(result)
    if os.environ["MUGRADE_OP"] == "submit":
        submit_test()


