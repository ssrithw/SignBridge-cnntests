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
python3 -m pip install requirements.txt
```

<b>6) Run the development server with the following command:</b>

```
python signbridge.py
```

## Changelog - Version 0.3.7
* Converted database from SQLite to PostgreSQL (SQLite still exists for fallback)
* Patched CSRF token handling
* Fixed HTML forms

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

<b>Main</b> is responsible for the index page and various static pages that don't belong elsewhere.

<b>User</b> handles non-authentication-required components related to users, such as the ability to edit your profile.

static/ and templates/ are used to house CSS, JS and HTML as normal. The folder structure in /templates/ follows the structure of the blueprints. Additionally, it contains a folder, /partials/, which houses the navbar and footer HTML. `base.html` is the base template reused across every webpage and therefore does not belong to any folder.

Outside of the blueprints, `config.py` is used to define configuration settings for Flask. `extensions.py` is used to initialize all the extensions relevant to the application (e.g. flask-limiter, flask-login). `models.py` contains the database models. app/\__init__.py initializes the application. `signbridge.py` calls `create_app()` from app/\__init__.py to start the application. Please let me know if you have any questions.

This application DOES NOT follow MVC architecture. It relies on Flask's blueprint system instead.

## todo
* let users switch mic and cam off if needed
* fix error.html
* fix call room
* set a real secret key
* add model toggle
* add gradcam heatmaps
* polish ui

## Academic Supervision
This application was guided and supervised by Ann Roshanie Appuhamy as part of undergraduate coursework.
