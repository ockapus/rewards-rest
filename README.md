# rewards-rest
Sample REST service for Fetch Rewards

## Installation

This basic web service requires Python3. Please visit the official [Python Downloads](https://www.python.org/downloads/) page for the latest version and instructions for your specific operating system.

In addition to the standard python libraries, this service uses web.py for basic HTTP framework needs. To install, please run:

    pip3 install web.py

## Running the Service

Once Python is installed properly, navigate to the directory that you installed this repo to and start the service with the following:

    python service.py

This will start a very simple web server on the local host, using port 8080. Available resources are documented below, and can be visited using standard REST methodology (for instance: curl commands, or a utility like Postman). Service can be valided as up by visiting the following url in any standard browser:

    http://localhost:8080/rest/users/1


## Resources

#### Request Query Parameters

All available endpoints use the same query parameters, as follows:

Parameter | Type | Description
--- | --- | ---
id | integer | The ID value of the user effected by the request

### rest/users

Provides information about users in the system. For demonstration purposes, only a single user (ID: 1) is available.

#### Get Current Points -> `GET`: `/rest/users/{id}`

Returns current point totals for that user, broken down by payer.

##### Responses

`status 200` - *application/json* - Returns totals of all available points

**Example:**

    {
        "points": {
            "DANNON": 1000,
            "UNILEVER": 0,
            "MILLER COORS": 5300
        }
    }

`status 404` - Returned if user ID not found


### rest/points

Provides end points for modifying the point log for a specified users

#### Add Points -> `POST`: `/rest/points/{id}`

Adds points to a user account for a specific payer and date. Point value can be negative, as long as total points for that specific payer at specified date would not be less than zero. Date cannot be in the future. 

##### Request Parameters

Parameter | Type | Description
--- | --- | ---
payer | string | Name of the specified payer
points | integer | Points to add or subtract from this user
timestamp | string | ISO Format date/time for this request

**Example:**

    {
        "payer": "DANNON",
        "points": 300,
        "timestamp": "2020-10-31 10:00:00"
    }

##### Responses

`status 200` - *application/json* - Returns `{"success": true}` if valid request

`status 400` - Returned if request malformed or invalid for some reason

`status 404` - Returned if user ID not found


#### Deduct Points -> `PUT`: `/rest/points/{id}`

Deducts points from the user account, such that oldest points are spent first, and no payer's balance go negative.

##### Request Parameters

Parameter | Type | Description
--- | --- | ---
deduct | integer | Points to deduct from this user account. Must be positive.

**Example:**

    { "deduct": 5000 }

##### Responses

`status 200` - *application/json* - Point values deducted by payer, and time deducted (always now)

**Example:**

    {
        "results": [
            {"payer": "DANNON", "points": -100, "timestamp": "2021-02-07 16:59:12"}, 
            {"payer": "UNILEVER", "points": -200, "timestamp": "2021-02-07 16:59:12"}, 
            {"payer": "MILLER COORS", "points": -4700, "timestamp": "2021-02-07 16:59:12"}
        ]
    }

`status 400` - Returned if request malformed or invalid for some reason

`status 404` - Returned if user ID not found