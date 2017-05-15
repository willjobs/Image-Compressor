@echo off

SET gimp_path="C:\Program Files\GIMP 2\bin\gimp-2.8.exe"
SET src_dir_gimp=\"C:/Users/Geoff/Pictures/gimptest\"
SET src_dir_win=C:\Users\Geoff\Pictures\gimptest
SET src_dir_py=C:/Users/Geoff/Pictures/gimptest
SET key=<YOUR KEY GOES HERE>

if not exist %src_dir_win%\resized mkdir %src_dir_win%\resized
if not exist %src_dir_win%\compressed mkdir %src_dir_win%\compressed

echo Running resize on directory
%gimp_path% --no-interface -b "(python-fu-resize RUN-NONINTERACTIVE %src_dir_gimp%)" -b "(gimp-quit 0)"

echo Resize complete. Begin compression.

python %~dp0TinyPNG_compress.py %src_dir_py%/resized %src_dir_py%/compressed %key%
echo Compression complete

pause