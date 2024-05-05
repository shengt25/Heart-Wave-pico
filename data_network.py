import network
from utils import GlobalSettings, print_log, get_datetime
import urequests as requests
import json
from umqtt.simple import MQTTClient


class DataNetwork:
    def __init__(self):
        self._wlan = network.WLAN(network.STA_IF)
        self._mqtt_client = MQTTClient("", GlobalSettings.mqtt_broker_ip)

    def connect_wlan(self):
        if not self._wlan.isconnected():
            self._wlan.active(True)
            self._wlan.connect(GlobalSettings.wifi_ssid, GlobalSettings.wifi_password)

    def connect_mqtt(self):
        try:
            self._mqtt_client.connect(clean_session=True)
        except:
            return False
        return True

    def mqtt_publish(self, result):
        measurement = {"mean_hr": result["HR"], "mean_ppi": result["PPI"],
                       "rmssd": result["RMSSD"], "sdnn": result["SDNN"]}
        topic = "hwp/measurement"
        message = json.dumps(measurement)
        try:
            self._mqtt_client.publish(topic, message)
        except:
            return False
        return True

    def is_wlan_connected(self):
        return self._wlan.isconnected()

    def get_wlan_ip(self):
        return self._wlan.ifconfig()[0]

    def get_broker_ip(self):
        return GlobalSettings.mqtt_broker_ip

    def is_mqtt_connected(self):
        try:
            self._mqtt_client.publish("hwp/test", "test connection")
        except:
            return False
        return True

    def get_kubios_analysis(self, ibi_list):
        """Return: success, response"""
        try:
            APIKEY = GlobalSettings.kubios_apikey
            CLIENT_ID = GlobalSettings.kubios_client_id
            CLIENT_SECRET = GlobalSettings.kubios_client_secret
            TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
            response = requests.post(url=TOKEN_URL, data='grant_type=client_credentials&client_id={}'.format(CLIENT_ID),
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                     auth=(CLIENT_ID, CLIENT_SECRET))
            response = response.json()  # Parse JSON response into a python dictionary
            access_token = response["access_token"]  # Parse access token
            dataset = {"type": "RRI", "data": ibi_list, "analysis": {"type": "readiness"}}
            response = requests.post(url="https://analysis.kubioscloud.com/v2/analytics/analyze",
                                     headers={"Authorization": "Bearer {}".format(access_token), "X-Api-Key": APIKEY},
                                     json=dataset)
            analysis = response.json()["analysis"]
            result = {"DATE": get_datetime(),
                      "HR": str(round(analysis["mean_hr_bpm"], 2)) + "BPM",
                      "PPI": str(round(analysis["mean_rr_ms"], 2)) + "ms",
                      "RMSSD": str(round(analysis["rmssd_ms"], 2)) + "ms",
                      "SDNN": str(round(analysis["sdnn_ms"], 2)) + "ms",
                      "SNS": str(round(analysis["sns_index"], 2)),
                      "PNS": str(round(analysis["pns_index"], 2)),
                      "STRESS": str(round(analysis["stress_index"], 2))}
        except Exception as e:
            print_log(f"Kubios analysis failed: {e}")
            return False, None
        return True, result
