[app]
title = SMS Reader
package.name = smsreader
package.domain = org.example
version = 0.1

# Where your main.py is
source.dir = .
source.include_exts = py,kv,png,jpg,ttf,ogg

# Kivy and Python
requirements = python3,kivy

# Basic app settings
orientation = portrait
fullscreen = 1
log_level = 2

# Android permissions (for SMS reader)
android.permissions = READ_SMS,RECEIVE_SMS,INTERNET

# (optional but good defaults)
android.api = 35
android.minapi = 21
android.archs = armeabi-v7a, arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
