# weight_tracking_api
A flask API for tracking weight - Work in progress

## Description
This flask application offers a simple API to track weight loss or weight gain over time via  rolling average.

## API
Simple API documentation can be found here: https://documenter.getpostman.com/view/13359083/UUxxgUAu


### Register /api/v1/register:
```
POST /api/v1/register HTTP/1.1
{
    "username":"snacktime",
    "password":"password"
}
```

### Login /api/v1/login:
```
POST /api/v1/login HTTP/1.1
{
    "username":"test",
    "password":"test"
}
```

Login will return a token to be used for further requests under the `x-access-token` HTTP header.

### Add a Weight /api/v1/track/{string:DATEYYYY-MM-DD}: 
```
POST /api/v1/track/{STR:DATE YYYY-MM-DD} HTTP/1.1
Host: 127.0.0.1:5000
x-access-token: {TOKEN}
{
    "weight": "192.5"
}
```

### Update a weight /api/v1/track/{string:DATEYYYY-MM-DD}:
```
PUT /api/v1/track/{string:DATEYYYY-MM-DD} HTTP/1.1
x-access-token: {TOKEN}
{
    "weight": "193.3"
}
```

### Get all weights /api/v1/track: 
```
GET /api/v1/track/{string:DATEYYYY-MM-DD}HTTP/1.1
x-access-token: {TOKEN}
```

### Get a weight for a specific date /api/v1/track/{string:DATEYYYY-MM-DD}: 
```
GET /api/v1/track/{DATE YYYY-MM-DD} HTTP/1.1
x-access-token: {TOKEN}
```

### Delete a weight for a specific date /api/v1/delete/{string:DATEYYYY-MM-DD}:
```
DELETE /api/v1/track/{DATE YYYY-MM-DD}HTTP/1.1
x-access-token: {TOKEN}
```

### Get a rolling average of weights /api/v1/average/{int:rolling window (default=7)}  
```
GET /api/v1/track/average HTTP/1.1
x-access-token: {TOKEN}
```
