import RPi.GPIO as GPIO
import tensorflow as tf
#from keras.models import load_model
from tensorflow.keras.models import load_model
from PIL import Image, ImageOps

from time import sleep
import numpy as np
import subprocess
#import pycamera
import requests
import pyrebase
import json
import time


print('chala chala chala')
#firebase configration
firebaseConfig = {

  'apiKey': "AIzaSyAzKMmas-P88XnMog_tahVlHldUHg-qwIU",
  'authDomain': "mobiltymate.firebaseapp.com",
  'projectId': "mobiltymate",
  'storageBucket': "mobiltymate.appspot.com",
  'messagingSenderId': "689242250199",
  'appId': "1:689242250199:web:678688bf12095abb218992",
  'measurementId': "G-EL1L7F168D",
  'databaseURL' : "https://mobiltymate-default-rtdb.firebaseio.com/"

}
firebase = pyrebase.initialize_app(firebaseConfig)
database = firebase.database()


#GPIO PINS INDICATION
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
TRIG_PIN = 11
ECHO_PIN = 13
BUZZER_PIN = 15
sound_pin = 29
water_level_pin = 19
pir_pin = 40
#capture_image = picamera.PiCamera()

# Setup GPIO pins
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(sound_pin, GPIO.IN)
GPIO.setup(water_level_pin, GPIO.IN)
GPIO.setup(pir_pin,GPIO.IN)

GPIO.output(BUZZER_PIN, GPIO.HIGH)
time.sleep(3)
GPIO.output(BUZZER_PIN, GPIO.LOW)   

#Camera code
# Disable scientific notation for clarity
np.set_printoptions(suppress=True)
# Load the model
# /home/pi/Desktop/EyDJbm.h5

class_names = open("labels.txt", "r").readlines()
print(class_names)

model_path = r"/home/pi/EyDJbm.h5"

model = load_model(model_path)

#model = tf.keras.models.load_model(model_path)

# Load the labels
#class_names = open("labels.txt", "r").readlines()
# Create the array of the right shape to feed into the keras model
# The 'length' or number of images you can put into the array is
# determined by the first position in the shape tuple, in this case 1
data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)


#ultrasonic code
def get_distance():
    # Send a pulse on the trigger pin
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)
    
    # Measure the duration of the echo pulse
    start_time = time.time()
    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()
        
    while GPIO.input(ECHO_PIN) == 1:
        end_time = time.time()

    # Calculate distance using the speed of sound
    duration = end_time - start_time
    distance = (duration * 34300) / 2  # Speed of sound is 343 m/s

    return distance


#camera code
def camera(img_name, data=data, class_names=class_names, model=model):
    image = Image.open(img_name).convert("RGB")
    # resizing the image to be at least 224x224 and then cropping from the center
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    # turn the image into a numpy array
    image_array = np.asarray(image)
    # Normalize the image
    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
    # Load the image into the array
    data[0] = normalized_image_array
    # Predicts the model
    prediction = model.predict(data)
    index = np.argmax(prediction)
    class_name = class_names[index]
    confidence_score = prediction[0][index]
    #print(class_name[2:], confidence_score)
    return class_name[2:]
    


try:
    while True:
                
        # camera code
        #capture = picamera.PiCamera()
        image_filename = 'image.jpg'
        #capture_image.capture(image_filename)
        #image_filename = f'image.jpg'
        # Capture an image using subprocess and raspistill
        subprocess.run(["raspistill", "-o", image_filename])
        print('Captured image:', {image_filename})
        object_class = camera(image_filename)
        print("Class:",object_class)
        


        #GPS code
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
            location = get_location(google_api_key, wifi_data)
    
            if location:
                latitude, longitude = location
                print(f"Latitude: {latitude}, Longitude: {longitude}")
                database.child("location")
                data= {
                        "latitude" : latitude,
                        "longitude" : longitude
                        }
                database.set(data)
            else:
                print("Location not found.")
                database.child("Error")
                database.set("Erorrr")
        else:
             print("No Wi-Fi data available.")


        
        #Ultrasonic & Audio Sensor Code
        distance = get_distance()
        print(f"Distance: {distance:.2f} cm")
        time.sleep(1)
        if distance <= 5:
            GPIO.output(BUZZER_PIN, GPIO.HIGH)
            print("Too close! Buzzer activated.")
            if GPIO.input(sound_pin):
                print("Sound detected!")
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(BUZZER_PIN, GPIO.LOW)            
            else:
                print("No sound")
                time.sleep(0.5)            
        else:
            GPIO.output(BUZZER_PIN, GPIO.LOW)
        
        
        #waterlevel sensor
        water_level = GPIO.input(water_level_pin)  # Read the water level sensor state
        if water_level == GPIO.HIGH:
            print("Water level is HIGH - Water Detected")
            GPIO.output(BUZZER_PIN, GPIO.HIGH) # Turn on the buzzer
        else:
            print("Water level is LOW - No Water Detected")
            GPIO.output(BUZZER_PIN, GPIO.LOW)  # Turn off the buzzer
            
        #pir sensor
        pir_pin = GPIO.input(40)
        if pir_pin == 1:
            print(" Motion Detected")
            GPIO.output(BUZZER_PIN, GPIO.HIGH)
            sleep(0.5)
            GPIO.output(BUZZER_PIN, GPIO.LOW)
        elif pir_pin == 0:
            print("No Motion Detected")
        print("--------------------------------------------------------")
        
        if distance <= 50:
            data_to_firebase = str(object_class)+"is "+str(int(distance))+" centimeter far away."
            #database.child("objects")
            data= {
                    "message" : data_to_firebase, 
                }
            database.set(data)
            
            
            
        
        
except KeyboardInterrupt:
    #camera.close()
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    GPIO.cleanup()
    print('Keyboard interrupt. Exiting...')


    