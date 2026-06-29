[app]
title = Love Notes
package.name = lovenotes
package.domain = org.moi
source.dir =.
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.2
requirements = python3,kivy==2.3.1,kivymd==1.2.0,pytz
orientation = portrait
android.archs = arm64-v8a
android.api = 34
android.minapi = 21
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.manifest.application_attributes = android:requestLegacyExternalStorage="true"
android.multidex = True
android.enable_androidx = True
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = False