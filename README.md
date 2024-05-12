# A heart rate analysis system based on Raspberry Pi Pico W and MicroPython.
Hardware: 
- Raspberry Pi Pico W
- SSD1306 OLED screen
- Rotary Encoder
- Crowtail Heart Rate Sensor
# Getting Started
1. Clone the repository
```
git clone --recurse-submodules https://github.com/shengt25/Heart-Wave-pico.git
```
2. Connect the Raspberry Pi Pico W to your computer via USB
3. Install mpremote if you haven't already installed, use: `pip install mpremote` or `python -m pip install mpremote`
4. [optional] If you want to use MQTT or Kubios cloud: Edit the config.json to set the Wi-Fi SSID and password, MQTT broker IP address, and Kubios API keys.
5. [optional] If you used pin other than 26 for the heart rate sensor, open the main.py to modify it at `state_machine = StateMachine(heart_sensor_pin=26)`
6. Run the installation script  
in Linux or MacOS:
```
cd Heart-Wave-pico && ./install.sh
```
or in Windows:
```
cd Heart-Wave-pico && .\install.cmd
```
7. Restart the Raspberry Pi Pico W and it should be ready to use.

# Note
To ensure a faster system booting, MQTT will not be connected by default, because if it will block the whole system for about 15 seconds
if the broker is not available. You can connect it manually in the settings menu, if the Wi-Fi and MQTT broker is correctly set up.
