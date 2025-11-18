[app]
title = SMS Reader
package.name = smsreader
package.domain = org.example
source.dir = .
source.include_exts = py,kv,png,jpg,ttf,ogg
fullscreen = 0
log_level = 2

# Your main .py file
entrypoint = main.py

# (str) Supported orientations
orientation = portrait

# (list) Application requirements
requirements = python3,kivy,pyjnius,plyer

# (str) Application versioning (method 1)
version = 0.1

# (str) Presplash of the application
presplash.filename =

# (str) Icon of the application
icon.filename =

[buildozer]
log_level = 2
warn_on_root = 1

[app.android]
android.api = 36
android.minapi = 23
android.sdk_path =
android.archs = arm64-v8a,armeabi-v7a
android.permissions = READ_SMS,RECEIVE_SMS,INTERNET
