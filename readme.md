# Navra Cloud

## Run by Docker
```bash
cd Navra
docker compose build
docker compose up -d
```

## Installation
### Pre Insatallation
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
sudo apt update
sudo apt install python3
sudo apt install python3-pip
sudo apt install mysql-server
cd src
sudo pip3 install -r requirements.txt
```
### Prepare MySQL Database
Connect to MySQL as root user and Run these queries to prepare database for this project.
```
CREATE USER 'navra'@'localhost' IDENTIFIED BY 'N@vRa';
CREATE DATABASE navra_db;
CREATE TABLE navra_db.Discount_Table (Discount_Code varchar(255), PersonID int);
GRANT INSERT, UPDATE, SELECT on navra_db.Discount_Table TO 'navra'@'localhost';
```

### Run without Docker

```bash
cd src
sudo python3 Main.py
```

## Test Cases
### Normal Requests
#### Generate Gift Codes API

**Request**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/json
Content-Length: 18

{
	"count" : 3
}
```
**Response**
```
HTTP/1.1 200 OK
Content-Length: 86
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:22:10 GMT
Server: Cloud Server :)
Via: waitress

{"gift_ids": ["QNQJMPRU9OE5QU2QCBQV", "OABUUKL9FZC0MQI0IOI9", "B6QG7TMNZOIF2P8Q33LO"]}
```
#### Submit Gift Codes API
**Request**
```
POST /api/submit-gift HTTP/1.1
Content-Type: application/json
Content-Length: 60

{
	"gift_id" :"QNQJMPRU9OE5QU2QCBQV",
"user_id":"1337" 
}
```
**Response**
```
HTTP/1.1 200 OK
Content-Length: 44
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:27:21 GMT
Server: Cloud Server :)
Via: waitress

{"Message": "Your account has been charged"}
```
### Malicious Requests
#### Gift Code Generation
1. OPTIONS Method\
**Request**
```
OPTIONS /api/generate-gift HTTP/1.1


```
**Response**
```
HTTP/1.1 200 OK
Allow: POST, OPTIONS
Content-Length: 0
Content-Type: text/html; charset=utf-8
Date: Tue, 23 Aug 2022 16:31:19 GMT
Server: Cloud Server :)
Via: waitress

```
---
2. Unwanted Method (GET)\
**Request**
```
GET /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/json
Content-Length: 18

{
	"count" : 3
}
```
**Response**
```
HTTP/1.1 405 METHOD NOT ALLOWED
Content-Length: 142
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:29:06 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "The method is not allowed for the requested URL. Contact to System Administration. Error ID: 62044b4f-b402-47df-b991-6fc7cf850a96"}
```
---
3. X-Admin-token Tests\
**Request 1**
```
POST /api/generate-gift HTTP/1.1
Content-Type: application/json
Content-Length: 18

{
	"count" : 3
}
```
**Response 1**
```
HTTP/1.1 403 FORBIDDEN
Content-Length: 33
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:33:03 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Insert X-Admin-token"}
```
**Request 2**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: NULL
Content-Type: application/json
Content-Length: 18

{
	"count" : 3
}
```
**Response 2**
```
HTTP/1.1 403 FORBIDDEN
Content-Length: 39
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:34:46 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "X-Admin-token is not valid"}
```
**Request 3**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: true
Content-Type: application/json
Content-Length: 18

{
	"count" : 3
}
```
**Response 3**
```
HTTP/1.1 403 FORBIDDEN
Content-Length: 39
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:36:01 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "X-Admin-token is not valid"}
```
---
4. Content Type\
**Request 1**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Length: 18

{
	"count" : 3
}
```
**Response 1**
```
HTTP/1.1 403 FORBIDDEN
Content-Length: 52
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:36:43 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Bad Request: Insert content-type header"}
```
**Request 2**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/xml
Content-Length: 18

{
	"count" : 3
}
```
**Response 2**
```
HTTP/1.1 400 BAD REQUEST
Content-Length: 70
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:39:15 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Bad Request: Invalid Data. Server just accept JSON Format"}
```
---
5. Body Tests\
**Request 1**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/json
Content-Length: 0


```
**Response 1**
```
HTTP/1.1 400 BAD REQUEST
Content-Length: 38
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:43:55 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Bad Request: Invalid Data"}
```
**Request 2**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/json
Content-Length: 2

{}
```
**Response 2**
```
HTTP/1.1 400 BAD REQUEST
Content-Length: 59
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:47:49 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Bad Request: Please Insert count value in JSON"}
```
**Request 3**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/json
Content-Length: 2

[]
```
**Response 3**
```
HTTP/1.1 400 BAD REQUEST
Content-Length: 59
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:48:32 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Bad Request: Please Insert count value in JSON"}
```
**Request 4**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/json
Content-Length: 20

{{
	"count" : 3
}}
```
**Response 4**
```
HTTP/1.1 400 BAD REQUEST
Content-Length: 59
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:48:32 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Bad Request: Please Insert count value in JSON"}
```
**Request 5**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/json
Content-Length: 20

{
	"count" : [3]
}
```
**Response 5**
```
HTTP/1.1 400 BAD REQUEST
Content-Length: 38
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:52:54 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Bad Request: Invalid Data"}
```
**Request 6**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/json
Content-Length: 20

{
	"count" : 3.1
}
```
**Response 6**
```
HTTP/1.1 400 BAD REQUEST
Content-Length: 38
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:53:56 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Bad Request: Invalid Data"}
```
**Request 7**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/json
Content-Length: 20

{
	"count" : 3.1
}
```
**Response 7**
```
HTTP/1.1 400 BAD REQUEST
Content-Length: 38
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:53:56 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Bad Request: Invalid Data"}
```
**Request 8**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/json
Content-Length: 19

{
	"count" : -3
}
```
**Response 8**
```
HTTP/1.1 400 BAD REQUEST
Content-Length: 38
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:56:09 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Bad Request: Invalid Data"}
```
**Request 9**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/json
Content-Length: 17

{
	"count" :0
}
```
**Response 9**
```
HTTP/1.1 400 BAD REQUEST
Content-Length: 38
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:56:09 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Bad Request: Invalid Data"}
```
**Request 10**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/json
Content-Length: 20

{
	"count" :1000
}
```
**Response 10**
```
HTTP/1.1 400 BAD REQUEST
Content-Length: 62
Content-Type: application/json
Date: Tue, 23 Aug 2022 16:58:14 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Bad Request: count value must be between 1 to 100"}
```
**Request 11**
```
POST /api/generate-gift HTTP/1.1
X-Admin-token: fde1b6cb2caf24a52e0780d077e3d
Content-Type: application/json
Content-Length: 9

})";'|/#\
```
**Response 11**
```
HTTP/1.1 400 BAD REQUEST
Content-Length: 38
Content-Type: application/json
Date: Tue, 23 Aug 2022 17:00:32 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Bad Request: Invalid Data"}
```
---
6. Rate Limit\
Blocks more than 10 requests per minute\
**Request 1**
```
POST /api/generate-gift HTTP/1.1


```
**Response 1**
```
HTTP/1.1 429 TOO MANY REQUESTS
Content-Length: 47
Content-Type: application/json
Date: Tue, 23 Aug 2022 18:58:02 GMT
Server: Cloud Server :)
Via: waitress

{"Error": "Too Many Requests. Retry-After: 60 seconds..."}
```
---
#### Gift Code Submition
1. OPTIONS Method\
**Request**
```
OPTIONS /api/submit-gift HTTP/1.1


```
**Response**
```
HTTP/1.1 200 OK
Allow: POST, OPTIONS
Content-Length: 0
Content-Type: text/html; charset=utf-8
Date: Tue, 23 Aug 2022 19:01:55 GMT
Server: Cloud Server :)
Via: waitress


```
---
2. Double Use of Gift Code\
**Request**
```
POST /api/submit-gift HTTP/1.1
Content-Type: application/json
Content-Length: 60

{
	"gift_id" :"QNQJMPRU9OE5QU2QCBQV",
	user_id":"1337" 
}
```
**Response**
```
HTTP/1.1 200 OK
Content-Length: 40
Content-Type: application/json
Date: Tue, 23 Aug 2022 19:03:17 GMT
Server: Cloud Server :)
Via: waitress

{"Message": "Failed to apply gift card"}
```
---
3. Use an other valid Gift Code for Previous User\
**Request**
```
POST /api/submit-gift HTTP/1.1
Content-Type: application/json
Content-Length: 60

{
	"gift_id" :"B6QG7TMNZOIF2P8Q33LO",
	"user_id":"1337" 
}
```
**Response**
```
HTTP/1.1 200 OK
Content-Length: 40
Content-Type: application/json
Date: Tue, 23 Aug 2022 19:05:59 GMT
Server: Cloud Server :)
Via: waitress

{"Message": "Failed to apply gift card"}
```
---
4. Use Pre Used Gift Code for an other User\
**Request**
```
POST /api/submit-gift HTTP/1.1
Content-Type: application/json
Content-Length: 60

{
	"gift_id" :"QNQJMPRU9OE5QU2QCBQV",
	"user_id":"9999" 
}
```
**Response**
```
HTTP/1.1 200 OK
Content-Length: 40
Content-Type: application/json
Date: Tue, 23 Aug 2022 19:07:58 GMT
Server: Cloud Server :)
Via: waitress

{"Message": "Failed to apply gift card"}
```
---












