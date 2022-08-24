import logging
import time
import uuid
import json
import threading
import traceback
import random
import string
import mysql.connector

from flask import Flask, request, Response
from werkzeug.exceptions import HTTPException

# Disable flask default logging
werkzeug_log = logging.getLogger('werkzeug')
main_log = logging.getLogger('Main')
werkzeug_log.setLevel(logging.CRITICAL + 1)
main_log.setLevel(logging.CRITICAL + 1)


# werkzeug_log.setLevel(logging.DEBUG) # Uncomment for Debugging
# main_log.setLevel(logging.DEBUG) # Uncomment for Debugging


class customFlask(Flask):
    def process_response(self, response):
        # Every response will be processed here first # but it cannot replace the previous server header
        response.headers['Server'] = 'Cloud Server :)'
        return (response)


# setup custom logger
logging.basicConfig(filename='./Flask-Log/Flask-APP.log', filemode='a', format='[%(asctime)s] [%(name)s] [%(levelname)s] -> %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
app = customFlask(__name__)

req_id = 0
lock_id = threading.Lock()
lock_discount_code_submission = threading.Lock() # prevent race condition on discount code submission
lock_discount_code_generation = threading.Lock() # prevent race condition on discount code generation
lock_rate_limit = threading.Lock()
allowed_methods = ["POST"]
request_count_per_ip = dict()
retry_after = 60
rate_limit_request_count = 10
global db_connection
global cursor


def get_req_id():
    global req_id
    global lock_id
    lock_id.acquire()
    req_id += 1
    lock_id.release()
    return str(req_id)


def do_log(data, log_func, req_id, obj):
    global logger
    if type(data) == str:
        log_msg = data
    elif type(data) == Response:
        headers = ""
        for key in data.headers.keys():
            headers += key + ": " + data.headers[key] + "\n"
        headers = headers.strip()
        log_msg = "Response For Req id: " + str(req_id) + "\n" + \
                  "Status : " + str(data.status) + "\n" + \
                  "Headers : " + headers + "\n" + \
                  "Data : " + str(data.data)
        if data.status_code == 500:
            log_msg += "\nTrace : \n" + traceback.format_exc() + "\n" + \
                       "Error Code: " + str(obj.code) + "\n" + \
                       "Error Name: " + obj.name + "\n" + \
                       "Error Description: " + obj.description
        if data.status_code // 100 == 4:
            if data.status_code == 405:
                log_msg += "\nReason : " + obj.description
            elif type(obj) == str:
                log_msg += "\nReason : " + obj
    else:
        headers = ""
        for key in data.headers.keys():
            headers += key + ": " + data.headers[key] + "\n"
        headers = headers.strip()
        log_msg = "Req id: " + str(req_id) + "\n" + \
                  "Method : " + str(data.method) + "\n" + \
                  "Url : " + str(data.url) + "\n" + \
                  "Headers : " + headers + "\n" + \
                  "Data : " + str(data.data) + "\n" + \
                  "Client IP : " + data.remote_addr
    log_msg += "\n" + ("=" * 100)
    log_func(log_msg)
    logger.handlers[0].flush()
    return data


def error_json(msg):
    return json.dumps({"Error": msg})


def db_query(query, inputs):
    result = None
    try:
        cursor.execute(query, inputs)
        result = cursor.fetchall()
        db_commit()
    except mysql.connector.Error as error:
        do_log("SQL Error: \nQuery: " + query + "\nInputs: " + str(inputs), logging.error, None, None)
        raise error
    return result


def db_commit():
    db_connection.commit()


def discount_code_generate(count):
    codes = list()
    letters = string.ascii_uppercase + string.digits
    for i in range(count):
        new_code = ''.join(random.choice(letters) for i in range(20))
        while len(db_query("SELECT Discount_Code FROM Discount_Table WHERE Discount_Code = %s;",
                           [new_code])) != 0 or new_code in codes:
            new_code = ''.join(random.choice(letters) for i in range(20))
        codes.append(new_code)
    for new_code in codes:
        db_query("INSERT INTO Discount_Table (Discount_Code, PersonID) VALUES (%s, %s);", (new_code, "-1"))
    return codes


@app.route("/api/generate-gift", methods=["POST"])
def generate_gift():
    global request_count_per_ip
    global lock_discount_code_generation
    global lock_rate_limit
    req_id = get_req_id()
    # log request
    do_log(request, logging.info, req_id, None)
    # rate limit check based on ip
    if request.remote_addr not in request_count_per_ip.keys():
        request_count_per_ip[request.remote_addr] = 1
    else:
        if request_count_per_ip[request.remote_addr] > rate_limit_request_count:
            return do_log(
                Response(error_json("Too Many Requests. Retry-After: " + str(retry_after) + " seconds..."),
                         content_type="application/json", status=429), logging.info, req_id, "Too Many Requests")
        else:
            lock_rate_limit.acquire()
            request_count_per_ip[request.remote_addr] += 1
            lock_rate_limit.release()
    if "X-Admin-token" not in request.headers:
        return do_log(Response(error_json("Insert X-Admin-token"), content_type="application/json", status=403),
                      logging.info, req_id, "Insert X-Admin-token")
    if request.headers["X-Admin-token"] != "fde1b6cb2caf24a52e0780d077e3d":
        return do_log(Response(error_json("X-Admin-token is not valid"), content_type="application/json", status=403),
                      logging.info, req_id, "X-Admin-token is not valid")
    if "Content-Type" not in request.headers:
        return do_log(Response(error_json("Bad Request: Insert content-type header"), content_type="application/json",
                               status=403),
                      logging.info, req_id, "Insert content-type header")
    if not request.headers["Content-Type"].startswith("application/json"):
        return do_log(
            Response(error_json("Bad Request: Invalid Data. Server just accept JSON Format"),
                     content_type="application/json", status=400), logging.info, req_id,
            "Content Type is not valid (application/json)")
    if int(request.headers["Content-Length"]) > 100:
        return do_log(
            Response(error_json("Bad Request: Invalid Data"), content_type="application/json", status=400),
            logging.info, req_id, "Content Length is too High")
    try:
        posted_data = json.loads(request.data)
    except json.decoder.JSONDecodeError:
        return do_log(
            Response(error_json("Bad Request: Invalid Data"), content_type="application/json", status=400),
            logging.info, req_id, "Requested Format is Not Json")
    if "count" not in posted_data:
        return do_log(
            Response(error_json("Bad Request: Please Insert count value in JSON"), content_type="application/json",
                     status=400),
            logging.info, req_id, "count value is not define")
    count = 0
    try:
        count = int(posted_data["count"])
    except (ValueError, TypeError):
        return do_log(
            Response(error_json("Bad Request: count value must be an integer"), content_type="application/json",
                     status=400), logging.info, req_id, "Count Value is Not Valid: " + str(posted_data["count"]))
    if count < 1 or count > 100:
        return do_log(
            Response(error_json("Bad Request: count value must be between 1 to 100"), content_type="application/json",
                     status=400),
            logging.info, req_id, "Count Value is invalid: " + str(posted_data["count"]))
    lock_discount_code_generation.acquire()  # Discount code generation Race Condition Prevention
    codes = discount_code_generate(count)
    lock_discount_code_generation.release()
    return do_log(
        Response(json.dumps({"gift_ids": codes}), content_type="application/json",
                 status=200),
        logging.info, req_id, None)


@app.route("/api/submit-gift", methods=["POST"])
def submit_gift():
    global request_count_per_ip
    global lock_rate_limit
    global lock_discount_code_submission
    req_id = get_req_id()
    # log request
    do_log(request, logging.info, req_id, None)
    # rate limit check based on ip
    if request.remote_addr not in request_count_per_ip.keys():
        request_count_per_ip[request.remote_addr] = 1
    else:
        if request_count_per_ip[request.remote_addr] > rate_limit_request_count:
            return do_log(
                Response(error_json("Too Many Requests. Retry-After: " + str(retry_after)),
                         content_type="application/json", status=429), logging.info, req_id, "Too Many Requests")
        else:
            lock_rate_limit.acquire()
            request_count_per_ip[request.remote_addr] += 1
            lock_rate_limit.release()
    if "Content-Type" not in request.headers:
        return do_log(Response(error_json("Bad Request: Insert content-type header"), content_type="application/json",
                               status=403),
                      logging.info, req_id, "Insert content-type header")
    if not request.headers["Content-Type"].startswith("application/json"):
        return do_log(
            Response(error_json("Bad Request: Invalid Data. Server just accept JSON Format"),
                     content_type="application/json", status=400), logging.info, req_id,
            "Content Type is not valid (application/json)")
    if int(request.headers["Content-Length"]) > 100:
        return do_log(
            Response(error_json("Bad Request: Invalid Data"), content_type="application/json", status=400),
            logging.info, req_id, "Content Length is too High")
    try:
        posted_data = json.loads(request.data)
    except json.decoder.JSONDecodeError:
        return do_log(
            Response(error_json("Bad Request: Invalid Data"), content_type="application/json", status=400),
            logging.info, req_id, "Requested Format is Not Json")
    if "gift_id" not in posted_data:
        return do_log(
            Response(error_json("Bad Request: Please Insert gift_id value in JSON"), content_type="application/json",
                     status=400),
            logging.info, req_id, "gift_id is not define")
    if "user_id" not in posted_data:
        return do_log(
            Response(error_json("Bad Request: Please Insert user_id value in JSON"), content_type="application/json",
                     status=400),
            logging.info, req_id, "user_id is not define")
    try:
        user_id = int(posted_data["user_id"])
    except (ValueError, TypeError):
        return do_log(
            Response(error_json("Bad Request: user_id value must be an integer"), content_type="application/json",
                     status=400), logging.info, req_id, "user_id Value is Not Valid: " + str(posted_data["user_id"]))
    if user_id < 999 or user_id > 10000:
        return do_log(
            Response(error_json("Bad Request: Invalid user id"), content_type="application/json",
                     status=400),
            logging.info, req_id, "user_id Value is not valid.")
    lock_discount_code_submission.acquire()
    if len(db_query("SELECT PersonID FROM Discount_Table WHERE PersonID = %s;", [str(user_id)])) != 0:
        lock_discount_code_submission.release()
        return do_log(
            Response(json.dumps({"Message": "Failed to apply gift card"}), content_type="application/json",
                     status=200),
            logging.info, req_id, "User (" + str(user_id) + ") attempt to use code: " + str(posted_data["gift_id"]))
    result = db_query("SELECT * FROM Discount_Table WHERE Discount_Code = %s;", [str(posted_data["gift_id"])])
    if len(result) == 0:
        lock_discount_code_submission.release()
        return do_log(
            Response(json.dumps({"Message": "Failed to apply gift card"}), content_type="application/json",
                     status=200),
            logging.info, req_id,
            "User (" + str(user_id) + ") attempt to use unknown code: " + str(posted_data["gift_id"]))
    if result[0][1] != -1:
        lock_discount_code_submission.release()
        return do_log(
            Response(json.dumps({"Message": "Failed to apply gift card"}), content_type="application/json",
                     status=200),
            logging.info, req_id,
            "User (" + str(user_id) + ") attempt to use pre used code: " + str(posted_data["gift_id"]))
    db_query("UPDATE discount_table set PersonID = %s where Discount_Code = %s;",
             (str(user_id), str(posted_data["gift_id"])))
    lock_discount_code_submission.release()
    return do_log(
        Response(json.dumps({"Message": "Your account has been charged"}), content_type="application/json",
                 status=200),
        logging.info, req_id,
        "User (" + str(user_id) + ") successfully used code: " + str(posted_data["gift_id"]))


@app.errorhandler(HTTPException)
def handle_exception(e):
    # Return JSON instead of HTML for HTTP errors.
    # start with the correct headers and status code from the error
    # replace the body with JSON
    salam = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    req_id = get_req_id()
    do_log(request, logging.info, req_id, None)
    error_msg = "Contact to System Administration. Error ID: " + str(uuid.uuid4())
    # append error descriptions except server internal errors.
    if (int(e.code) // 100) != 5:
        error_msg = e.description + " " + error_msg
        return do_log(Response(error_json(error_msg), content_type="application/json", status=e.code), logging.warning,
                      req_id, e)
    else:
        return do_log(Response(error_json(error_msg), content_type="application/json", status=e.code), logging.critical,
                      req_id, e)


# simple looper to reset rate limit counter
def reset_rate_limit():
    global request_count_per_ip
    global lock_rate_limit
    while True:
        time.sleep(retry_after)
        lock_rate_limit.acquire()
        request_count_per_ip = dict()
        lock_rate_limit.release()


def db_init():
    return mysql.connector.connect(
        host="localhost",
        user="navra",
        password="N@vRa",
        database="navra_db"
    )


# main thread of execution to start the server
if __name__ == '__main__':
    do_log("Application Listens on port 9000", logging.info, None, None)
    threading.Thread(target=reset_rate_limit, args=()).start()
    db_connection = db_init()
    cursor = db_connection.cursor(prepared=True)
    from waitress import serve
    serve(app, host="0.0.0.0", port=9000)
