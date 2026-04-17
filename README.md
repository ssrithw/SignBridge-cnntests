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
* profile.html has been renamed to user.html
* landing.html has been renamed to join.html
* Landing page is now index.html 
* waiting.html has been removed and its code integrated into call.html 
* New rooms are created in profile
* Added secret key (check config.py) to protect forms against cross-site request forgery (CSRF) attacks
* Username, email and password validation should work correctly now
* Passwords are hashed with PBKDF2 - change to bcrypt if required
* Added session authentication
* Changed contact phone number to Dulitha's because it's funny
* Database has been updated to include additional tables for messages and transcripts
* Added support for profile pictures via Gravatar.
* Added email support for admins
* Added logging capabilities. Logs are saved to /logs/signbridge.log
* Users can now reset their passwords via email.
* Added tests.py for testing capabilities. Will add dummy tests soon.
* Added rate limiting back into the app (for some reason it disappeared in the last version on GitHub). Thanks Dulneth!
* Added webcam and microphone support
* Replaced eventlet use with gevent because eventlet has been deprecated.

## todo
* (done) modify landing to "join room", "sign up" or "sign in" a la Zoom
* (done) (looks ugly) add toasts
* (done) (well i deleted it lol) fix waiting room routing and integration
* (done) (ugly) remove create new room if signed out and remove its html, convert to button in user landing
* (done) fix static code in call.html
* (done) move tfjs models to static folder (off huggingface)
* (done) add visual indicator to signup password
* (done) refactor js in call.html
* (done) delete waiting.html
* (done) if logged in redirect to your profile. if not go to index.html
* add admins to user table
* let users switch mic and cam off if needed
* convert to model view controller
* look up ip based limiting vs user based limiting and diff limits for users vs guests
* figure out wtf is going on with error.html
* fix call room
* set a real secret key lol
* (done) skip room generation needing name if signed in
* add rate limiting to everything


## Academic Supervision
This application was guided and supervised by Ann Roshanie Appuhamy as part of undergraduate coursework.
