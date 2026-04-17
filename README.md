# SignBridge - Real-Time Sign Language Detection and Translation
SignBridge is a video calling application intended to aid with translating Sri Lankan Sign Language into text. It consists of a conventional two-person video call interface combined with a deep learning model that captures the camera feed and displays a text transcript in real time. 

The application is developed with Flask, HTML, CSS and JavaScript. The deep learning model is developed with Python, TensorFlow and TensorFlow.js.

This application was built in partial fulfilment of CSG3101 - Applied Project at Edith Cowan University Sri Lanka.

## How to run this application locally

<b>1) Clone the repository to your local drive:</b>

```
git clone https://github.com/nuhaaaaaaa24/SignBridge.git
```

<b>2) Navigate to the folder you just created:</b>

```
cd your/path/here/SignBridge
```

<b>3) Create a Python virtual environment.</b>

In your terminal, run the following command:

```
python3 -venv venv
```

<b>4) Activate the virtual environment</b>

On Windows Command Prompt, run the following:

```
venv\Scripts\activate
```

On Windows PowerShell, run the following:

```
venv\Scripts\Activate.ps1
```

On MacOS, run the following:

```
venv\bin\activate
```

On Linux, run the following:

```
source venv/bin/activate
```

<b>5) Install the required dependencies</b>

Run ONE of the following commands: 

```
pip install requirements.txt
```
or
```
python -m pip install requirements.txt
```

<b>6) Run the development server with the following command:</b>

```
python signbridge.py
```

## Changelog - Version 0.3.0
Please read the files carefully. I did not document every change I made here.

* Refactored all code to fit Flask best practices.
* All html files now use Jinja templating - they inherit from base.html, with additional code as needed.
* app.py has been removed and its code aggressively modularized. Parts of it can be found in __init__.py, handlers.py, routes.py, signbridge.py... you get the idea. Not an exhaustive list. Please read all the files.
* Most JavaScript has been removed and replaced with server-side Python code.
* On that note, app.js and main.js have been removed. Page-specific Javascript files are used instead.
* Database now uses the SQLAlchemy package instead of SQLite3
* Replaced eventlet with gevent because eventlet has been deprecated.
* Replaced werzkreug with flask-bcrypt
* profile.html has been renamed to user.html
* landing.html has been renamed to join.html
* Landing page is now index.html 
* waiting.html has been removed and its code integrated into call.html 
* New rooms are created in profile
* Added secret key (check config.py) to protect forms against cross-site request forgery (CSRF) attacks
* Username, email and password validation should work correctly now
* Changed contact phone number to Dulitha's because it's funny
* Database has been updated to include additional tables for messages and transcripts
* Added support for profile pictures via Gravatar.
* Added email support for admins
* Added logging capabilities. Logs are saved to /logs/signbridge.log. Need to add more logs.
* Users can now reset their passwords via email.
* Added tests.py for testing capabilities.
* Added rate limiting back into the app (for some reason it disappeared in the last version on GitHub). Thanks Dulneth!
* Added webcam and microphone support
* Added CNN support - model is stored in /static/models

## Quick guide to repository navigation

The refactored version of this codebase uses Flask blueprints to manage application components. The components are as follows:
```
├── app
│   ├── auth
│   ├── call
│   ├── core
│   ├── errors
│   ├── help
│   ├── main
│   ├── user

```
<b>Auth</b> maintains authentication components such as user logins and password resets.
<b>Call</b> is responsible for the call room - handling the waiting room, model loading, WebRTC and SocketIO integrations
<b>Core</b> is NOT a blueprint. It houses utilities reused across components.
<b>Errors</b> contains error handlers for HTTP errors.
<b>Help</b>, while not strictly necessitated by code, houses the static help pages.
<b>Main</b> is responsible for the index page and various static pages that don't belong elsewhere
<b>User</b> handles non-authentication-required components related to users, such as the ability to edit your profile.

static/ and templates/ are used to house CSS, JS and HTML as normal. The folder structure in /templates/ follows the structure of the blueprints. Additionally, it contains a folder, /partials/, which houses the navbar and footer HTML. `base.html` is the base template reused across every webpage and therefore does not belong to any folder.

Outside of the blueprints, `config.py` is used to define configuration settings for Flask. It references an `.env` file which I have NOT pushed to GitHub due security concerns - please let me know if this causes you issues. `extensions.py` is used to initialize all the extensions relevant to the application (e.g. flask-limiter, flask-login). `models.py` contains the database models. app/\__init__.py initializes the application. `signbridge.py` calls `create_app()` from app/\__init__.py to start the application. Please let me know if you have any questions.

## todo
* let users switch mic and cam off if needed
* look up ip based limiting vs user based limiting and diff limits for users vs guests
* fix error.html
* fix call room
* set a real secret key
* add model toggle
* add gradcam heatmaps
* polish ui

## Academic Supervision
This application was guided and supervised by Ann Roshanie Appuhamy as part of undergraduate coursework.
