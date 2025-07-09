
# USDA 
# Torrence Washington
# July 2025

from phew import server, template, logging, access_point, dns, connect_to_wifi, disconnect_from_wifi
from phew.template import render_template
from phew.server import redirect
import json
import time
import os
import gc
import utime # type: ignore
import machine # type: ignore
gc.threshold(50000) # setup garbage collection

APP_TEMPLATE_PATH = "app_templates"
AP_NAME = "Pi Pico"
DOMAIN = "pipico.net"
WIFI_FILE = "wifi.json"
SETTINGS_FILE = "settings.json"
onboard_led = machine.Pin("LED", machine.Pin.OUT)

# resets pico, can be ignored for now
def machine_reset():
    utime.sleep(1)
    print("Resetting...")
    machine.reset()

@server.route("/wrong-host-redirect", methods=["GET"])
def wrong_host_redirect(request):
  # if the client requested a resource at the wrong host then present 
  # a meta redirect so that the captive portal browser can be sent to the correct location
  body = "<!DOCTYPE html><head><meta http-equiv=\"refresh\" content=\"0;URL='http://" + DOMAIN + "'/ /></head>"
  logging.debug("body:",body)
  return body

# starting page 
def app_index(request):
    return render_template(f"{APP_TEMPLATE_PATH}/index.html")

def app_configure(request):
    # writes save data from form onto a json file in string
    with open(WIFI_FILE, "w") as f:
        json.dump(request.form, f)
        f.close()
    # grabs library data from json file and uses it to connect to wifi 
    with open(WIFI_FILE) as f:
        wifi_credentials = json.load(f)
        connect_to_wifi(wifi_credentials["ssid"], wifi_credentials["password"])
        return render_template(f"{APP_TEMPLATE_PATH}/configured.html")

# LED toggle, can ignore
def app_toggle_led(request):
        onboard_led.toggle()
        return "OK"

# disconnects from wireless wifi, fixing to show page first then disconnect 
def app_reset(request):
     with open(WIFI_FILE, "w") as f:
         json.dump(" ", f)
         f.close()
     disconnect_from_wifi()
     return render_template(f"{APP_TEMPLATE_PATH}/reset.html", access_point_ssid = AP_NAME)

# options page 
def app_change_options(request):
    return render_template(f"{APP_TEMPLATE_PATH}/options.html")

def app_save_changes(request):
     # writes down saved changes to a json file
     with open(SETTINGS_FILE, "w") as f:
         json.dump(request.form, f)
         f.close()
     return render_template(f"{APP_TEMPLATE_PATH}/save_changes.html")

# temperature reader on pico, can ignore/delete
def app_get_temperature(request):
    # Not particularly reliable but uses built in hardware.
    # Algorithm used here is from:
    # https://www.coderdojotc.org/micropython/advanced-labs/03-internal-temperature/
    sensor_temp = machine.ADC(4)
    reading = sensor_temp.read_u16() * (3.3 / (65535))
    temperature = 27 - (reading - 0.706)/0.001721
    return f"{round(temperature, 1)}"


def app_catch_all(request):
        return "Not found.", 404

# Routes to different pages
server.add_route("/", handler = app_index, methods = ["POST", "GET"])
server.add_route("/configure", handler = app_configure, methods= ["POST", "GET"])
server.add_route("/reset", handler = app_reset, methods = ["GET"])
server.add_route("/toggle", handler = app_toggle_led, methods = ["GET"])
server.add_route("/temperature", handler = app_get_temperature, methods = ["GET"])
server.add_route("/options", handler = app_change_options, methods= ["POST", "GET"])
server.add_route("/savechanges", handler = app_save_changes, methods= ["POST", "GET"])


server.set_callback(app_catch_all)
# Set to Accesspoint mode
ap = access_point("USAP")  # Change this to whatever Wi-Fi SSID you wish
ip = ap.ifconfig()[0]                   # Grab the IP address and store it
logging.info(f"starting DNS server on {ip}")
dns.run_catchall(ip)                    # Catch all requests and reroute them
server.run()                            # Run the server
logging.info("Webserver Started")


