'''
app/core/nav.py

This file exists to map navigation endpoints to UI state.
'''

NAV_MAP = {
    "main.index": "home",
    "main.about": "about",
    "main.contact": "contact",
    "help.index": "help",
    "user.user_profile": "user",
    "call.call": "call",
}

# apparently you define constant variables using capslock in python. don't like this coming from c and c++
# delete later