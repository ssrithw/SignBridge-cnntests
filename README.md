# SignBridge - Real-Time Sign Language Detection and Translation
SignBridge is a video calling application intended to aid with translating Sri Lankan Sign Language into text. It consists of a conventional two-person video call interface combined with a deep learning model that captures the camera feed and displays a text transcript in real time. 

The application is developed with Flask, HTML, CSS and JavaScript. The deep learning model is developed with Python, TensorFlow and TensorFlow.js.

The demo for this application can be viewed at https://signbridge-pzm3.onrender.com/ 

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
python3 -m venv venv
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
pip install -r requirements.txt
```
or
```
python3 -m pip install -r requirements.txt
```

<b>6) Run the development server with the following command:</b>

```
python signbridge.py
```

## Changelog - Version 0.3.11
* Created a default email - admin.signbridge@gmail.com. Please bother me if I forgot to tell you guys the password
* Added email support to the contact page
* Added admin dashboard (it's ugly, someone fix it)
* Added user id-based rate limiting
* Added user autoblock after too many failed login attempts. Currently requires an admin to unblock (email issues)

## Documentation
This application uses Sphinx for documentation - please visit https://www.sphinx-doc.org/en/master/usage/quickstart.html for help.

Use `cd docs` followed by `build html` to build the documentation on your machine.

Please note that the documentation is currently UNFINISHED!

## todo
* add a rate limit cooldown of 60 seconds
* disable clicking buttons after rate limits are triggered
* let users switch mic and cam off if needed
* fix error.html or just delete it atp
* fix call room
* add model toggle
* add gradcam heatmaps
* polish ui

## Academic Supervision
This application was guided and supervised by Ann Roshanie Appuhamy as part of undergraduate coursework.
