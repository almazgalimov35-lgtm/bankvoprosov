[app]
title = Bank Voprosov
package.name = bankvoprosov
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,xlsx
source.include_patterns = test.xlsx
version = 0.1
requirements = python3,kivy,openpyxl
orientation = portrait
fullscreen = 0
android.api = 31
android.minapi = 24
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 0
