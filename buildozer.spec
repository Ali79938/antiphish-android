[app]
title = AntiPhish
package.name = antiphish
package.domain = org.antiphish

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
source.include_patterns = analyzer/*.py,static/*.png

version = 0.1

requirements = python3,charset-normalizer

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/static/icon.png

android.permissions = RECEIVE_SMS,READ_SMS,READ_PHONE_STATE,POST_NOTIFICATIONS,FOREGROUND_SERVICE,INTERNET

android.api = 33
android.minapi = 24
android.archs = arm64-v8a

android.allow_backup = True
android.private_storage = True

android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
