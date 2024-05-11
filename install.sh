#!/bin/bash

# prevent MinGW to messing up path names
export MSYS_NO_PATHCONV=1

# OSX and Linux have python3 with different names.
case "$(uname)" in

   Darwin*)
     #for OSX try to figure out which python version to use
     if [ "$(which python3 2>/dev/null | wc -l)" -gt "0" ] ; then
        python=python3
     elif [ "$(which python3.12 2>/dev/null | wc -l)" -gt "0" ] ; then
        python=python3.12
     else
        python=python
     fi
     ;;

   MINGW*)
     #for MINGW use python launcher
     python=py
     ;;

   Linux*)
     #for Linux use python3
     python=python3
     ;;
esac
echo Using: $python, `which python`
$python -m http.server &
comport=`$python -m mpremote connect list | grep 2e8a:0005 | cut -d' ' -f1`
echo Device: $comport
sleep 2
$python -m mpremote connect $comport mip install --target / http://localhost:8000/
kill $!
#pkill -f http.server
