# Keras Code
from keras.models import load_model  # TensorFlow is required for Keras to work
from PIL import Image, ImageOps      # Install pillow instead of PIL
import RPi.GPIO as GPIO
import numpy as np 
import picamera
import time
import requests
import json
import pyrebase
'''
import board
import busio
import adafruit_lis3dh
'''
#firebase_config
firebaseConfig = {
  'apiKey': "AIzaSyBbGWVbdJK8aXTokq7VdmkAcobUrq_LD20",
  'authDomain': "fir-1-74ee2.firebaseapp.com",
  'projectId': "fir-1-74ee2",
  'storageBucket': "fir-1-74ee2.appspot.com",
  'messagingSenderId': "990281927735",
  'appId': "1:990281927735:web:d134c305ecfb96543d83b2",
  'measurementId': "G-QDN4Z704TD",
  'databaseURL': "https://fir-1-74ee2-default-rtdb.firebaseio.com/GPSSystem_1",
}
firebase = pyrebase.initialize_app(firebaseConfig)
database = firebase.database()


def measure_distance():
    # Send a pulse to the trigger pin
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)

    # Measure the pulse duration on the echo pin
    while GPIO.input(ECHO_PIN) == 0:
        pulse_start = time.time()
    while GPIO.input(ECHO_PIN) == 1:
        pulse_end = time.time()

    # Calculate distance based on the pulse duration
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # Speed of sound in cm/s

    return distance
# Belongs to Gyro Sensor
def read_word_2c(address):
    high = bus.read_byte_data(MPU6050_ADDR, address)
    low = bus.read_byte_data(MPU6050_ADDR, address + 1)
    val = (high << 8) + low
    if val >= 0x8000:
        return -((65535 - val) + 1)
    else:
        return val
'''
# Belongs to Gyro Sensor
def read_data():
    gyro_x = read_word_2c(REG_GYRO_XOUT_H)
    gyro_y = read_word_2c(REG_GYRO_XOUT_H + 2)
    gyro_z = read_word_2c(REG_GYRO_XOUT_H + 4)
    
    return gyro_x, gyro_y, gyro_z
def detect_fall(accel_data):
    # Calculate the magnitude of acceleration
    magnitude = (accel_data[0]**2 + accel_data[1]**2 + accel_data[2]**2)**0.5
    
    # Check if magnitude exceeds a threshold
    if magnitude > FALL_THRESHOLD:
        return True
    return False

FALL_THRESHOLD = 9.8  # Adjust this threshold based on your sensor and scenario

'''

GPIO.setmode(GPIO.BOARD)
TRIG_PIN = 11
ECHO_PIN = 13
BUZZER_PIN = 15  # Adjust this pin according to your setup
PIR_PIN = 40
sound_pin = 10
water_level_pin =16
#
# Setup GPIO pins
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(sound_pin, GPIO.IN)
GPIO.setup(water_level_pin, GPIO.IN)

# Disable scientific notation for clarity
np.set_printoptions(suppress=True)
camera = picamera.PiCamera()

# Load the model
model = load_model("EyDJbm.h5")

# Load the labels
class_names = open("labels.txt", "r").readlines()

# Create the array of the right shape to feed into the keras model
# The 'length' or number of images you can put into the array is
# determined by the first position in the shape tuple, in this case 1
data_tf = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)


    
while True:
            # Capture an image every 5 seconds
            image_filename = f'image.jpg'
            camera.capture(image_filename)
            print(f'Captured image: {image_filename}')
            
            # main(image_filename)
            image = Image.open(image_filename).convert("RGB")

            # resizing the image to be at least 224x224 and then cropping from the center
            size = (224, 224)
            image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)

            # turn the image into a numpy array
            image_array = np.asarray(image)

            # Normalize the image
            normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1

            # Load the image into the array
            data_tf[0] = normalized_image_array

            # Predicts the model
            prediction = model.predict(data_tf)
            index = np.argmax(prediction)
            class_name = class_names[index]
            confidence_score = prediction[0][index]
            
            def get_wifi_data():
                    # You might need to install and use appropriate libraries to collect Wi-Fi data.
                    # For example, on Linux, you can use the "iwlist" command.
                    # Modify this function to gather a list of visible Wi-Fi networks.

                     wifi_networks = [
                         {"macAddress": "00:11:22:33:44:55", "signalStrength": -50},
                        # Add more Wi-Fi networks here
                     ] 

                     return wifi_networks
            def get_location(api_key, wifi_networks):
                     url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={api_key}"
                     data = {
                             "wifiAccessPoints": wifi_networks
                         }

                     response = requests.post(url, json=data)
                     result = response.json()

                     if "location" in result:
                         return result["location"]["lat"], result["location"]["lng"]
                     else:
                         return None
            
            google_api_key = "AIzaSyAK7TETMet9cuvffKxH1poisO65mPYtVt8"  # Replace with your actual API key
            wifi_data = get_wifi_data()
            if wifi_data:
                latitude, longitude = get_location(google_api_key, wifi_data)
                if latitude and longitude:
                    print(f"Latitude: {latitude}, Longitude: {longitude}")
                    database.child("location")
                    data= {
                     "latitude" : latitude,
                     "longitude" : longitude
                    }
                    database.set(data)
                    print(f"Latitude: {latitude}, Longitude: {longitude}")
                else:
                    print("Location not found.")
                    database.child("Error")
                    database.set("Erorrr")


            else:
                 print("No Wi-Fi data available.")           
                
            # ultrasonic code
            distance = measure_distance()
            print(f"Distance: {distance:.2f} cm")

            # Check if distance is less than or equal to 5 cm
            if distance <= 5:
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                print("Too close! Buzzer activated.")
            else:
                GPIO.output(BUZZER_PIN, GPIO.LOW)


            #PIR Sensor Code
            is_motion = GPIO.input(PIR_PIN)
            if is_motion == 1:
                print(" Motion Detected")
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(BUZZER_PIN, GPIO.LOW)
            elif is_motion == 0:
                print("NO Motion detected")
                
                
            ## Fall Detection
            '''
            accel_data = sensor.acceleration
            if detect_fall(accel_data):
                print("Fall detected!")
                GPIO.output(ALERT_PIN, GPIO.HIGH)  # Trigger alert
                time.sleep(2)  # Wait for a few seconds before resetting the alert
                GPIO.output(ALERT_PIN, GPIO.LOW) ''' # Reset alert
                
                
            #WATER DETECTION
            water_level = GPIO.input(water_level_pin)  # Read the water level sensor state

            if water_level == GPIO.HIGH:
                print("Water level is HIGH - Water Detected")
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                time.sleep(2)# Turn on the buzzer
                GPIO.output(BUZZER_PIN, GPIO.LOW)  # Turn off the buzzer
            else:
                print("Water level is LOW - No Water Detected")
                

                    
            print("Class:",class_name[2:])
            print( "Confidence Score:",confidence_score)
            print('_'*5)
            
            # variables need to upload on firebase
            print(distance,class_name[2:])
            print('_'*5)
            print('_'*30)
            print(class_name,"is ",str(distance),"far")
            msg=class_name+"is "+str(distance)+"far"
            database.child("message")
            database.set(msg)

            print('Hello world')
            
            
            
            
#except:
 #   camera.close()
  #  GPIO.output(BUZZER_PIN, GPIO.LOW)    
   # print('END')

