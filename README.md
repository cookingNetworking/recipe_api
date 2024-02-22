# **Cookingnetwork api**
- version : 1.0
- Swagger api document : https://cookingnetwork.co

## Feature
- Offering endpoint enable for frontend access and manage culinary data on the Cookingnetwork platform, including recipes, user reviews, ingredient inventory, and cooking tutorials.
- Designed with REST principles!

## Core function
-  **Account Management**: Facilitate user sign-ups, sign-ins, and logouts. 
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


