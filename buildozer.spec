[app]
title = Bank Voprosov
package.name = bankvoprosov
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,xlsx
source.include_patterns = test.xlsx
version = 0.1
requirements = python3==3.11.5,kivy==2.3.0,openpyxl==3.1.2
orientation = portrait
fullscreen = 0
android.api = 34
android.minapi = 24
android.archs = arm64-v8a
android.permissions = READ_EXTERNAL_STORAGE
android.accept_sdk_license = True
android.skip_update = False
android.allow_replace = True
android.sdk_path = /home/runner/.buildozer/android/platform/android-sdk
p4a.branch = master
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 0
