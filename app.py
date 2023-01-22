import pandas as pd
from flask import Flask, render_template
import time
import Adafruit_DHT
import RPi.GPIO as GPIO
from threading import Thread
from queue import Queue
import datetime
import os

print(os.getcwd())

app = Flask(__name__, static_folder='static')

# Set the sensor type (DHT22) and the GPIO pin number
sensor = Adafruit_DHT.DHT22
pin = 4

# Set the relay pin number
relay = 17

# Set the interval for logging data and turning on the relay (in seconds)
log_interval = 600 # 5 minutes
relay_interval = 14400 # 4 hours

# Initialize the GPIO pin for the relay
GPIO.setmode(GPIO.BCM)
GPIO.setup(relay, GPIO.OUT)


last_relay_on = time.time()

# Global variables to store the temperature and humidity values
global temperature
global humidity

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

def log_data(temperature, humidity):
    # Create a dataframe from the data
    data = {'Time': [time.strftime("%Y-%m-%d %H:%M:%S")], 'Temperature(F)': [temperature], 'Humidity(%)': [humidity]}
    df = pd.DataFrame(data)
    
    # Append the data to the CSV file
    df.to_csv('temp_humidity_data.csv', mode='a', header=False)

def check_relay():
    global last_relay_on
    current_time = time.time()
    if current_time - last_relay_on >= relay_interval:
        # Turn on the relay for 2 minutes
        GPIO.output(relay, GPIO.HIGH)
        last_relay_on = current_time
        log_relay_data("ON")
        time.sleep(120)
        GPIO.output(relay, GPIO.LOW)
        log_relay_data("OFF")
        print("relay has been turned on")
    else:
        log_relay_data("OFF")

def log_relay_data(status):
    # Create a pandas DataFrame with the current relay data
    data = {'Time': [time.strftime("%Y-%m-%d %H:%M:%S")], 'Relay Status': [status]}
    df = pd.DataFrame(data)
    
    # Append the data to the CSV file
    df.to_csv('relay_data.csv', mode='a', header=False)


def read_and_log_data():
    try:
        while True:
            temperature, humidity = read_sensor_data()
            data_queue.put((temperature, humidity))
            log_data(temperature, humidity)
            check_relay()
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
    temperature, humidity = data_queue.get()
    last_relay_on_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_relay_on))
   
    # Fetch the data from the CSV file
    df = pd.read_csv("temp_humidity_data.csv", names=["Time", "Temperature(F)", "Humidity(%)"])

    # Format the data for the graph
    x_data = df["Time"].tolist()
    y_data = df["Temperature(F)"].tolist()

    return render_template('index.html', temperature=temperature, humidity=humidity, last_relay_on=last_relay_on_time, x_data=x_data, y_data=y_data)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')