[app]
title = SMS Reader
package.name = smsreader
package.domain = org.example
source.dir = .
source.include_exts = py,kv,png,jpg,ttf,ogg
fullscreen = 1
log_level = 2

# Your main .py file
entrypoint = main.py

# Requirements (Python packages)
requirements = python3,kivy

# Orientation
orientation = portrait

# Permissions
android.permissions = READ_SMS,RECEIVE_SMS,INTERNET

# (optional) icon
# icon.filename = %(source.dir)s/icon.png

[buildozer]
log_level = 2
warn_on_root = 1

# Android settings
android.api = 33
android.minapi = 21
android.sdk = 21
android.ndk = 25b
an  droid.arch = armeabi-v7a
  
