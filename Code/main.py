# main.py for RP2040-ZERO (MicroPython)
# A simple proportional (P) humidity controller using a heater and DHT22 sensor,
# with output to an SSD1306 OLED display and NeoPixel status LED.

import machine
import utime
import dht
import ssd1306
import neopixel

# --- System Information ---
VER = "0.2"
VER_BUILD = "11222025"
EMAIL = "3lkgrove@gmail.com"
FIRMWARE_LINK = "https://github.com/3lkgrove/"

# --- Configuration ---

# Pin Assignments (Verify these match your wiring for RP2040-ZERO)
HEATER_PIN = 7       # GPIO for MOSFET control (Heater PWM)
FAN_PIN = 8         # GPIO for MOSFET control (Fans On/Off)
DHT_PIN = 28         # GPIO for DHT22 Data
I2C_SDA_PIN = 0      # I2C SDA for OLED
I2C_SCL_PIN = 1      # I2C SCL for OLED

# NeoPixel assignment (Moved from 16 to 2 to avoid conflict with HEATER_PIN)
NEO_PIN = 16
NUM_PIXELS = 1       # For a single LED

# Display Configuration
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_I2C_ADDR = 0x3c

# Control Setpoint
TARGET_HUMIDITY = 30.0  # Setpoint in %

# Control Parameters
# Proportional Gain (Kp) for Humidity Control
HUMIDITY_KP = 5.0
MAX_PWM = 65535         # Max duty cycle for 16-bit PWM

# --- Initialization & Status ---

print("Created by Anthony Sleck")
print("Email at anthony.sleck@gmail.com")
print(f"Version {VER}")
print(f"Build Code {VER_BUILD}")
print(f"Github: {FIRMWARE_LINK}\n")

# Initialize NeoPixel
try:
    np = neopixel.NeoPixel(machine.Pin(NEO_PIN), NUM_PIXELS)
    np[0] = (0, 100, 0) # Green status light
    np.write()
except Exception as e:
    print(f"NeoPixel Initialization Error on pin {NEO_PIN}: {e}")

# Initialize I2C for OLED
oled = None
try:
    i2c = machine.I2C(0, sda=machine.Pin(I2C_SDA_PIN), scl=machine.Pin(I2C_SCL_PIN), freq=400000)
    oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, addr=OLED_I2C_ADDR)
    print("OLED display initialized successfully.")
except Exception as e:
    print(f"OLED Initialization Error: {e}. Display functionality disabled.")

# Initialize DHT22 Sensor
d = dht.DHT22(machine.Pin(DHT_PIN))

# Initialize Heater (PWM)
heater_pwm = machine.PWM(machine.Pin(HEATER_PIN))
heater_pwm.freq(1000)   # 1kHz frequency
heater_pwm.duty_u16(0)  # Start off

# Initialize Fan (Simple On/Off)
fan_pin = machine.Pin(FAN_PIN, machine.Pin.OUT)
fan_pin.value(1) # Fans ON for circulation

# --- Functions ---

def celsius_to_fahrenheit(c):
    """Converts Celsius to Fahrenheit."""
    return (c * 9/5) + 32

def read_dht():
    """Reads temperature and humidity from the DHT22."""
    try:
        d.measure()
        temp_c = d.temperature()
        humidity = d.humidity()
        return temp_c, humidity
    except OSError as e:
        print(f"Failed to read DHT22 sensor: {e}. Using default values for bench testing.")
        # Defaulting to predefined values for bench testing/development
        temp_c = 10
        humidity = 80
        return temp_c, humidity

def update_oled(temp_f, humidity, heater_duty):
    """Updates the OLED display with current readings."""
    if oled is None:
        return

    oled.fill(0)
    oled.text("Heated Box Control", 0, 0)
    oled.hline(0, 10, OLED_WIDTH, 1)

    # Current Readings
    oled.text(f"Temp: {temp_f:.1f} F", 0, 15)
    oled.text(f"Humi: {humidity:.1f} %", 0, 25)

    # Setpoint
    oled.text(f"Target H: {TARGET_HUMIDITY:.0f} %", 0, 40)
    
    # Heater Status (Duty Cycle)
    power_percent = (heater_duty / MAX_PWM) * 100
    oled.text(f"Heater: {power_percent:.0f} %", 0, 50)
    
    oled.show()

def humidity_control(current_humidity):
    """
    Simple Proportional (P) control for humidity using the heater.
    Heater is activated when current humidity is ABOVE the target setpoint.
    Returns the calculated 16-bit PWM duty cycle.
    """
    error = current_humidity - TARGET_HUMIDITY
    
    # Calculate required PWM duty cycle
    # P-Control: Duty_ratio = Kp * Error
    
    if error > 0:
        # Duty is proportional to the error
        duty_ratio = HUMIDITY_KP * error
        
        # Clamp duty_ratio between 0 and 100
        duty_ratio = max(0, min(100, duty_ratio))
        
        # Convert ratio (0-100) to 16-bit PWM duty (0-65535)
        duty_u16 = int((duty_ratio / 100) * MAX_PWM)
    else:
        # Humidity is at or below target, turn heater off
        duty_u16 = 0
        
    heater_pwm.duty_u16(duty_u16)
    return duty_u16
        
# --- Main Loop ---

print("Starting humidity controller...")
fan_pin.value(1) # Ensure fans are running for initial circulation

while True:
    temp_c, humidity = read_dht()
    
    if temp_c is not None and humidity is not None:
        temp_f = celsius_to_fahrenheit(temp_c)
        
        # 1. Apply Control Logic
        current_duty = humidity_control(humidity)
        
        # 2. Update Display
        update_oled(temp_f, humidity, current_duty)

        # 3. Log Status to Console
        heater_percent = (current_duty / MAX_PWM) * 100
        print(f"T: {temp_f:.1f} F, H: {humidity:.1f} %, Target H: {TARGET_HUMIDITY:.0f} %, Heater Duty: {heater_percent:.0f} %")
        
    # Wait before next measurement/control loop
    utime.sleep(5) # Read and update every 5 seconds
