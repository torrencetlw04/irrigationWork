
# USDA 
# Torrence Washington
# July 2025

from phew import server, template, logging, access_point, dns, connect_to_wifi, disconnect_from_wifi
from phew.template import render_template
from phew.server import redirect
import network # type: ignore
import json
import os
import gc
import utime # type: ignore
import machine # type: ignore
gc.threshold(50000) # setup garbage collection

APP_TEMPLATE_PATH = "app_templates"
DOMAIN = "pipico.net"
WIFI_FILE = "wifi.json"
onboard_led = machine.Pin("LED", machine.Pin.OUT)

#resets pico, can be ignored for now
def machine_reset():
    utime.sleep(1)
    print("Resetting...")
    machine.reset()


@server.route("/", methods=['GET','POST'])
def index(request):
    """ Render the Index page and respond to form requests """
    if request.method == 'GET':
        logging.debug("Get request")
        return render_template(f"{APP_TEMPLATE_PATH}/index.html")
    if request.method == 'POST':
        text = request.form.get("text", None)
        logging.debug(f'posted message: {text}')
        return render_template(f"{APP_TEMPLATE_PATH}/index.html")

@server.route("/wrong-host-redirect", methods=["GET"])
def wrong_host_redirect(request):
  # if the client requested a resource at the wrong host then present 
  # a meta redirect so that the captive portal browser can be sent to the correct location
  body = "<!DOCTYPE html><head><meta http-equiv=\"refresh\" content=\"0;URL='http://" + DOMAIN + "'/ /></head>"
  logging.debug("body:",body)
  return body

#starting page 
def app_index(request):
    return render_template(f"{APP_TEMPLATE_PATH}/index.html")

def app_configure(request):
    with open(WIFI_FILE, "w") as f:
        #grabs data from html save and connects it to be wireless via python 
        wifi_credentials = json.load(f)
        ip_address = connect_to_wifi(wifi_credentials['ssid'], wifi_credentials['password'])

        #prints ip address of pico, connect to wifi used by pico to continue
        print(f"Connected to wifi, IP address {ip_address}")
        return render_template(f"{APP_TEMPLATE_PATH}/configure.html")
    
#LED toggle, can ignore
def app_toggle_led(request):
        onboard_led.toggle()
        return "OK"

#disconnects from wireless wifi, fix to show page first then disconnect 
def app_reset(request):
     disconnect_from_wifi()
     return render_template(f"{APP_TEMPLATE_PATH}/reset.html")

#options page 
def app_change_options(request):
    return render_template(f"{APP_TEMPLATE_PATH}/options.html")

#temperature reader on pico, can ignore 
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
server.add_route("/", handler = app_index, methods = ["GET"])
server.add_route("/configure", handler = app_configure, methods= ["POST"])
server.add_route("/reset", handler = app_reset, methods = ["GET"])
server.add_route("/toggle", handler = app_toggle_led, methods = ["GET"])
server.add_route("/temperature", handler = app_get_temperature, methods = ["GET"])
server.add_route("/options", handler = app_change_options, methods= ["GET"])


server.set_callback(app_catch_all)
# Set to Accesspoint mode
ap = access_point("USAP")  # Change this to whatever Wi-Fi SSID you wish
ip = ap.ifconfig()[0]                   # Grab the IP address and store it
logging.info(f"starting DNS server on {ip}")
dns.run_catchall(ip)                    # Catch all requests and reroute them
server.run()                            # Run the server
logging.info("Webserver Started")


