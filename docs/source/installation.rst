How to Run This Application Locally
===================================

This guide explains how to set up and run the SignBridge application on your local machine.

Step 1: Clone the Repository
----------------------------

Clone the repository to your local drive:

::

    git clone https://github.com/nuhaaaaaaa24/SignBridge.git

Step 2: Navigate to the Project Folder
--------------------------------------

Move into the project directory:

::

    cd your/path/here/SignBridge

Step 3: Create a Virtual Environment
------------------------------------

Create a Python virtual environment:

::

    python3 -m venv venv

Step 4: Activate the Virtual Environment
----------------------------------------

Depending on your operating system, run one of the following commands:

**Windows Command Prompt:**

::

    venv\Scripts\activate

**Windows PowerShell:**

::

    venv\Scripts\Activate.ps1

**macOS:**

::

    venv/bin/activate

**Linux:**

::

    source venv/bin/activate

Step 5: Install Dependencies
----------------------------

Install required packages using one of the following commands:

::

    pip install -r requirements.txt

or

::

    python3 -m pip install -r requirements.txt

Step 6: Run the Development Server
----------------------------------

Start the Flask development server:

::

    python signbridge.py