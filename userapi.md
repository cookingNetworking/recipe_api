## Api for user `sign in/up`, `user list`, `user detail`, `user edit`, `user delete` and `forget user password`.

## User Sign in
- **Endpoint** :
  - `/login`
- **HTTP Method**
  - `POST`

- **Description** :
  - User can login in `Recipe_social_media_name` with this API.
  - User need to input **EMAIL** and **Password** to login.
  - If **EMAIL** and **Password** is corretly match, server will return a `cookie` contain `session ID`.

- **Request**
  - **Data Type** :
    - `application/json`
  - **Parameter** :

        | Name     | Type    | Required |
        |----------|---------|----------|
        | email    | string  | Yes      |
        | password | string  | Yes      |
        - `example :`

        {"email": "login@example.com", "password": "loginpassword"}

- **Response**

- `HTTP Status :` 200
  - **Data Type** :
    - `application/json`
  - **Header** :

        | Name     |     Type    | Required |
        |----------|-------------|----------|
        |   auth   |   string    |   Yes    |
  - `example :`
        {
        "auth" : "afiewo3210fn 20f2834=rv jkweopqfk"
        }

  - **Body** :

        | Name     |     Type    | Required |
        |----------|-------------|----------|
        | Message  | Json string |   Yes    |
  - `example :`
        {
        "message": "User successfully login!!!"
        }

**note :**The auth cookies must set `HttpOnly`.

- `HTTP Status :` 400
  - **Data Type** :
    - `application/json`
  - **Body** :

        | Name     |     Type    | Required |
        |----------|-------------|----------|
        | Message  | Json string |   Yes    |
  - `example :`
        {
        "message": "Email or password is not correct, please check again."
        }

## User Sign out
- **Endpoint** :
  - `/logout`

- **HTTP Method**
  - `POST`

- **Description** :
  - User can logout in `Recipe_social_media_name` with this API.
  - After post this api, clear cookies.

- **Request**

  - None

- **Response**
- `HTTP Status :` 200
  - **Data Type** :
    - `application/json`
  - **Body** :

        | Name     |     Type    | Required |
        |----------|-------------|----------|
        | Message  | Json string |   Yes    |

  - `example :`
        {"message": "User successfully Logout!!!"}
- `HTTP Status :` 408
  - **Data Type** :
    - `application/json`
  - **Body** :

        | Name     |     Type    | Required |
        |----------|-------------|----------|
        | Message  | Json string |   Yes    |

  - `example :`
        {"message": "Time Out!"}
- `HTTP Status :` 500
  - **Data Type** :
    - `application/json`
  - **Body** :

        | Name     |     Type    | Required |
        |----------|-------------|----------|
        | Message  | Json string |   Yes    |

  - `example :`
        {"message": "Internal Server Error"}



## Response recipe 
  - {
  "count": 123,
  "next": "http://api.example.org/accounts/?page=4",
  "previous": "http://api.example.org/accounts/?page=2",
  "results": [
    {
      "id": 0,
      "title": "string",
      "cost_time": "string",
      "description": "string",
      "ingredients": [
        "string"
      ],
      "tags": [
        "string"
      ],
      "photos": [
        {
          "id": 0,
          "recipe": 0,
          "photo": "string",
          "upload_date": "2023-11-12T07:29:51.970Z",
          "category": "main"
        }
      ],
      "steps": [
        {
          "id": 0,
          "recipe": 0,
          "step": 32767,
          "description": "string",
          "image": "string"
        }
      ]
    }
  ]
}