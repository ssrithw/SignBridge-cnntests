.. SignBridge documentation master file, created by
   sphinx-quickstart on Sat Apr 18 12:01:21 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

SignBridge documentation
========================

Welcome!
========

SignBridge is a real-time video call and chat application that uses machine learning to automatically detect and translate Sri Lankan Sign Language.

Quick Guide to Repository Navigation
====================================

The refactored version of this codebase uses Flask blueprints to manage application components. The components are as follows:

::

    app/
        auth/
        call/
        core/
        errors/
        help/
        main/
        user/

Auth
----

**Auth** maintains authentication components such as user logins and password resets.

Call
----

**Call** is responsible for the call room — handling the waiting room, model loading, WebRTC, and SocketIO integrations.

Core
----

**Core** is *not* a blueprint. It houses utilities reused across components.

Errors
------

**Errors** contains error handlers for HTTP errors.

Help
----

**Help**, while not strictly required by the codebase, contains static help pages.

Main
----

**Main** is responsible for the index page and various static pages that do not belong elsewhere.

User
----

**User** handles non-authentication-required user features such as editing profiles.

Admin
----

**Admin** handles admin-only routes.

Static and Templates
====================

``static/`` and ``templates/`` are used to store CSS, JavaScript, and HTML files as usual.

The structure inside ``templates/`` mirrors the blueprint structure.

Additionally, there is a ``partials/`` folder that contains reusable UI components such as the navbar and footer.

The ``base.html`` template is the global base layout used across all pages and does not belong to any specific folder.

Project Configuration Files
===========================

Outside of the blueprints:

- ``config.py`` defines Flask configuration settings.
- ``extensions.py`` initializes Flask extensions (e.g., Flask-Login, Flask-Limiter).
- ``models.py`` contains database models.
- ``app/__init__.py`` initializes and configures the Flask application.
- ``signbridge.py`` runs the application by calling ``create_app()``.

Architecture Note
=================

This application **does not** follow MVC architecture.

Instead, it is structured around Flask's **blueprint-based modular architecture**, where each feature is separated into independent components.

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents:

