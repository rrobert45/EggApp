from flask import Flask, render_template
import time
import Adafruit_DHT
import RPi.GPIO as GPIO
import csv
from threading import Thread
from queue import Queue
import datetime


app = Flask(__name__)

# Set the sensor type (DHT22) and the GPIO pin number
sensor = Adafruit_DHT.DHT22
pin = 4

# Set the relay pin number
relay = 17

# Set the interval for logging data and turning on the relay (in seconds)
log_interval = 600 # 10 minutes
relay_interval = 14400 # 4 hours

# Initialize the GPIO pin for the relay
GPIO.setmode(GPIO.BCM)
GPIO.setup(relay, GPIO.OUT)

data_queue = Queue()

def read_sensor_data():
    # Read the humidity and temperature
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    if humidity is not None and temperature is not None:
        temperature = (temperature * 9/5) + 32
        return round(temperature,0), round(humidity,0)
    else:
        print('Failed to read data from sensor')
        return None, None

def log_data(temperature, humidity, relay_status):
    # Log the temperature and humidity data
    temp_humidity_writer.writerow([time.strftime("%m-%d-%Y %H:%M:%S"), temperature, humidity])
    temp_humidity_file.flush()
    relay_writer.writerow([time.strftime("%m-%d-%Y %H:%M:%S"), relay_status])
    relay_file.flush()
    

def check_relay():
    global last_relay_on
    current_time = time.time()
    if current_time - last_relay_on >= relay_interval:
        # Turn on the relay for 2 minutes
        GPIO.output(relay, GPIO.HIGH)
        last_relay_on = current_time
        log_data(None, None, "ON")
        time.sleep(120)
        GPIO.output(relay, GPIO.LOW)
        log_data(None, None, "OFF")
        print("relay has been turned on")
    else:
        log_data(None, None, "OFF")


def read_and_log_data():
    try:
        while True:
            # Open the CSV files for writing
            temp_humidity_file = open('temp_humidity_data.csv', 'w', newline='')
            temp_humidity_writer = csv.writer(temp_humidity_file)
            relay_file = open('relay_data.csv', 'w', newline='')
            relay_writer = csv.writer(relay_file)
            
            temperature, humidity = read_sensor_data()
            data_queue.put((temperature, humidity, last_relay_on))
            log_data(temperature, humidity, last_relay_on)
            check_relay()
            
            # Close the CSV files
            temp_humidity_file.close()
            relay_file.close()
            
            time.sleep(log_interval)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up the GPIO pins
        GPIO.cleanup()

@app.route("/")
def index():
    thread = Thread(target=read_and_log_data)
    thread.start()
    temperature, humidity, last_relay_on = data_queue.get()
    last_relay_on_date=datetime.datetime.fromtimestamp(last_relay_on).strftime('%m-%d-%Y --- %H:%M:%S %p')
    return render_template("index.html", temperature=temperature, humidity=humidity, last_relay_on=last_relay_on_date)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)