[app]
# Basic app info
title = SMS Reader
package.name = smsreader
package.domain = org.example
version = 0.1

# Where your main.py is
source.dir = .
source.include_exts = py,kv,png,jpg,ttf,ogg

# Python / Kivy requirements
# (pyjnius = Android APIs, plyer = TTS etc.)
requirements = python3,kivy,pyjnius,plyer

# App display settings
orientation = portrait
fullscreen = 1
log_level = 2

# Android permissions (for SMS reader)
android.permissions = READ_SMS,RECEIVE_SMS,INTERNET

# Android SDK / build settings
android.api = 35
android.minapi = 21
android.archs = armeabi-v7a, arm64-v8a

# Prefer a stable build-tools version
android.build_tools_version = 35.0.1

# IMPORTANT: auto-accept SDK license (no y/N prompt)
android.accept_sdk_license = True


[buildozer]
# Buildozer settings
log_level = 2
warn_on_root = 0
