import os
import numpy as np
import requests
import pytest
import datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning


"""
Note: This use of globals is pretty ugly, but it's unclear to me how to wrap this into 
a class while still being able to use pytest hooks, so this is the hacky solution for now.
"""


_values = []
_submission_id = ""
_errors = 0
_server_url = "https://api.mugrade.org/"
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def encode_json(data):
    """ Encode a dictionary to our JSON serialization """
    if isinstance(data, dict):
        return {k:encode_json(v) for k,v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [encode_json(d) for d in data]
    elif isinstance(data, np.ndarray):
        return {"_encoded_type":"np.ndarray", "data":encode_json(data.tolist())}
    elif isinstance(data, datetime.datetime):
        return {"_encoded_type":"datetime", "data":data.isoformat()}
    elif isinstance(data, (type, np.dtype)):
        return {"_encoded_type":"type", "data":repr(data)}
    elif isinstance(data, (np.float16, np.float32, np.float64)):
        return float(data)
    elif isinstance(data, (np.int8, np.int16, np.int32, np.int64,
                           np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(data)
    else:
        return data


def start_submission(func_name):
    """ Begin a submisssion to the mugrade server """

    response = requests.post(_server_url + "submit",
                             params = {"user_key": os.environ["MUGRADE_KEY"],
                                       "assignment": os.environ["MUGRADE_HW"],
                                       "problem": func_name},
                             verify=False)

    if response.status_code != 200:
        raise Exception(f"Error : {response.text}")
    return response.json()["submission_id"]

def submit_test():
    """ Submit a single grader test. """
    global _values, _submission_id, _errors

    response = requests.post(_server_url + "submit_test",
                            params = {"user_key": os.environ["MUGRADE_KEY"],
                                      "submission_id":_submission_id, 
                                      "test_case_index":len(_values)-1},
                            json=encode_json(_values[-1]),
                            verify=False)


    if response.status_code != 200:
        print(f"Error : {response.text}")
    elif not response.json()["correct"]:
        print(f"Grader test {len(_values)} failed")
        _errors += 1
    else:
        print(f"Grader test {len(_values)} passed")



def publish(func_name):
    """ Publish an autograder. """
    global _values
    response = requests.post(_server_url + "publish",
                            params = {"user_key": os.environ["MUGRADE_KEY"],
                                      "assignment": os.environ["MUGRADE_HW"],
                                      "problem": func_name},
                            json=encode_json(_values),
                            verify=False)

    if response.status_code != 200:
        print(f"Error : {response.text}")
    else:
        print(response.json())


@pytest.hookimpl(hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    ## prior to test, initialize submission
    global _values, _submission_id, _errors
    _values = []
    _errors = 0
    func_name = pyfuncitem.name[7:]
    if os.environ["MUGRADE_OP"] == "submit":
        _submission_id = start_submission(func_name)
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


