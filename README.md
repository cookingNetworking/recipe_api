# **Cookingnetwork api**
- version : 1.0
- Swagger api document : https://cookingnetwork.co

## Feature
- Offering endpoint enable for frontend access and manage culinary data on the Cookingnetwork platform, including recipes, user reviews, ingredient inventory, and cooking tutorials.
- Designed with REST principles!

## Core function
-  **Account Management**: Facilitate user sign-up, sign-in, and logouts. 
-  **Recipe Management**: Create , retrieve, update and delete recipe.
-  **Community Engagement**: Post comments, rate, save and like recipes ingredients and tags, and follow other users.
-  **Cooking Tutorials**: Access a variety of cooking tutorials with pictures.
-  (Upcoming)**Live steaming system**: Allow cook demenstrate recipe step in live straming.

## System architecture
![cookingnetwork_architecture](https://github.com/cookingNetworking/recipe_api/assets/122463207/d5146125-3e16-4ff1-a3a4-c7b893484d77)


## Side feature

### Register user 
- **Sign up locally**

  <img src=https://github.com/cookingNetworking/recipe_api/assets/122463207/b7a4e8c4-cef7-4325-9e53-a47ff43975e1 width=60% />
  
  - User registration and account activation process. If the email address provided during registration already exists, the user is directed to the login page. New users will receive an activation link via email. After clicking it, they will complete account activation and redirect to the login page. Accounts that are not activated within the specified time will be automatically deleted.

- **Google oauth**

  <img src=https://github.com/cookingNetworking/recipe_api/assets/122463207/f3cd2139-4890-4720-9454-ccc37f7d0ef3 width=60% />

  - When a user choose log in using Google OAuth, the backend server makes a request to Google's OAuth server with the client ID, scope, and redirect URL. The user is then redirected to Google's login page where they can enter their email and password. The user must also approve the requested consents. Once consent is granted, Google's OAuth server responses access and refresh tokens back the backend server. Upon receiving the tokens, the backend server creates a user account and returns a session ID to the client to maintain the user's logged-in state.

### Cache & Redis

- **Normal cache**

  <img src=https://github.com/cookingNetworking/recipe_api/assets/122463207/b7e4da27-c487-4128-bb7e-4b4226831a6e width=60% />

- **High-Frequency Update Data**

  <img src=https://github.com/cookingNetworking/recipe_api/assets/122463207/dca3561c-218e-48da-8530-4c1b69ff9794 width=80% />

  <img src=https://github.com/cookingNetworking/recipe_api/assets/122463207/3481f44a-4c98-4fd4-a031-2f1d0254cc0b width=30% />

### Task queue (Celery)

 <img src=https://github.com/cookingNetworking/recipe_api/assets/122463207/7baea866-ca4c-48f4-a745-39f9a588f7cd width=60% />

  - The system utilizes a message queue to accomplish asynchronous tasks such as sending emails, as well as scheduled tasks like synchronizing Redis and SQL database data. This setup ensures that tasks are processed efficiently without blocking the main application flow, allowing for operations that require more time, like email dispatch or database synchronization, to be handled in the background.



### Notificaiotn system (websocket)
- **Architecture**

  <img src=https://github.com/cookingNetworking/recipe_api/assets/122463207/ecc57308-9207-4f7b-8d09-19a0e9d68864 width=20% />

  - The notification system is based on WebSocket connections, achieved by implementing Django Channels and Daphne, which enable ASGI-compliant communication.The channel layer acts as a messaging hub for sending and receiving messages across various consumer instances and WebSocket clients. 

- **Notifiaction**

  <img src=https://github.com/cookingNetworking/recipe_api/assets/122463207/a946d568-2634-4776-be9e-06c97e8c9cdb width=60% />

  -  The notification system leverages Django Channels and WebSocket technology to enable persistent connections between the user and the Django application server. The Channel Layer serves as an intermediary, handling the routing and distribution of messages and managing group and channel subscriptions to maintain WebSocket connections. When User2 creates a new recipe, a Django signal triggers a notification that is then pushed to User1, facilitating real-time communication.

### Database schema


 <img src=https://github.com/cookingNetworking/recipe_api/assets/122463207/2c5591a1-8ec6-49d5-8e23-1111dd86ecb7 width=60% />


### Backend Technique 

**Infrastructure**
  - Docker
  - Docker-compose

**Environment**
  - Python/ django / django restframework

**Database**
   - Postgres SQL

 **Cache**
   - Redis

**Cloud Service** 
  - AWS EC2
  - AWS RDS
  - AWS S3
  - AWS Cloudfront
  - AWS Route53
  - AWS certificate Manger

**Networking**
  - HTTP&HTTPS
  - Websocket
  - NGINX
  - Domain name server(DNS)
  - SSL
 
**CI/CI** 
  - Github Actions

**Test**
 - django test

**Third pary library**
  - celery
  - django-channel

**Version Control**
  - Git/Git hub

### Contact
---
 :black_nib: JI-SHIN, KUO  
 :mailbox_with_mail: Email: as2229181@gmail.com
