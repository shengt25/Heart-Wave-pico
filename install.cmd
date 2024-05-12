@echo off
start "mpremote.webserver" python -m http.server
@rem Extract comport name where pico is connected
for /f "tokens=1 delims= " %%a in ('python -m mpremote connect list ^| find "2e8a:0005"') do set comport=%%a
echo Device: %comport%
timeout /t 2 /nobreak
@rem Run mpremote
python -m mpremote connect %comport% mip install --target / http://localhost:8000/
@rem The following line terminates all processes with mpremote.webserver as the window title.
taskkill /fi "WINDOWTITLE eq mpremote.webserver"
