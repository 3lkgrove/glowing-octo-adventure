# main.py for RP2040-ZERO (MicroPython)

import machine
import utime
import dht
import ssd1306

# --- Configuration ---

# Pin Assignments (Modify these to match your wiring)
HEATER_PIN = 7  # GPIO for MOSFET control (Heater PWM)
FAN_PIN = 8     # GPIO for MOSFET control (Fans On/Off)
DHT_PIN = 28     # GPIO for DHT22 Data
I2C_SDA_PIN = 0  # I2C SDA for OLED
I2C_SCL_PIN = 1  # I2C SCL for OLED

# Display Configuration (128x64 or 128x32, adjust as needed)
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_I2C_ADDR = 0x3c

# Control Setpoint
global TARGET_HUMIDITY
TARGET_HUMIDITY = 30.0  # Setpoint in %

# Control Parameters
# Proportional Gain for Humidity Control (adjust this value)
# A higher Kp means faster, but potentially more unstable, control.
HUMIDITY_KP = 5.0
MAX_PWM = 65535  # Max duty cycle for 16-bit PWM

# --- Initialization ---

# Initialize I2C for OLED
try:
    i2c = machine.I2C(0, sda=machine.Pin(I2C_SDA_PIN), scl=machine.Pin(I2C_SCL_PIN), freq=400000)
    oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, addr=OLED_I2C_ADDR)
except Exception as e:
    print(f"OLED Initialization Error: {e}")
    # Fallback/Error handling if OLED fails

# Initialize DHT22 Sensor
d = dht.DHT22(machine.Pin(DHT_PIN))

# Initialize Heater (PWM)
heater_pwm = machine.PWM(machine.Pin(HEATER_PIN))
heater_pwm.freq(1000)  # 1kHz frequency
heater_pwm.duty_u16(0) # Start off

# Initialize Fan (Simple On/Off)
fan_pin = machine.Pin(FAN_PIN, machine.Pin.OUT)
fan_pin.value(1) # Fans ON for circulation

# --- Functions ---

def set_target_humidity(new_humidity):
    """
    Sets a new target humidity setpoint.
    Can be called from the REPL/CLI.
    """
    global TARGET_HUMIDITY
    try:
        # 1. Convert to float and validate range (e.g., 0-100)
        new_humidity = float(new_humidity)
        if 0.0 <= new_humidity <= 100.0:
            TARGET_HUMIDITY = new_humidity
            print(f"Target humidity successfully updated to: {TARGET_HUMIDITY:.1f} %")
            return TARGET_HUMIDITY
        else:
            print(f"Error: Humidity target must be between 0 and 100%. Given: {new_humidity}")
            return TARGET_HUMIDITY
    except ValueError:
        print(f"Error: Invalid input. Must be a number. Given: {new_humidity}")
        return TARGET_HUMIDITY

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
        print("Failed to read DHT22 sensor.")
        return None, None

def update_oled(temp_f, humidity):
    """Updates the OLED display with current readings."""
    oled.fill(0)
    oled.text("Heated Box Control", 0, 0)
    oled.hline(0, 10, OLED_WIDTH, 1)

    # Current Readings
    oled.text(f"Temp: {temp_f:.1f} F", 0, 15)
    oled.text(f"Humi: {humidity:.1f} %", 0, 25)

    # Setpoint
    oled.text(f"Target H: {TARGET_HUMIDITY:.0f} %", 0, 40)
    
    # Heater Status (Duty Cycle)
    current_duty = heater_pwm.duty_u16()
    power_percent = (current_duty / MAX_PWM) * 100
    oled.text(f"Heater: {power_percent:.0f} %", 0, 50)
    
    oled.show()

def humidity_control(current_humidity):
    """
    Simple Proportional (P) control for humidity using the heater.
    - If Humi > Target, turn on heater to raise temp and lower RH.
    - If Humi < Target, turn off heater/reduce power.
    """
    error = current_humidity - TARGET_HUMIDITY
    
    # Calculate required PWM duty cycle
    # P-Control: Duty_ratio = Kp * Error
    # Only heat when humidity is too HIGH (Error > 0)
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
    
# --- Main Loop ---

print("Starting humidity controller...")
fan_pin.value(1) # Ensure fans are running for initial circulation

while True:
    temp_c, humidity = read_dht()
    
    if temp_c is not None and humidity is not None:
        temp_f = celsius_to_fahrenheit(temp_c)
        
        # 1. Apply Control Logic
        humidity_control(humidity)
        
        # 2. Update Display
        update_oled(temp_f, humidity)

        print(f"T: {temp_f:.1f} F, H: {humidity:.1f} %, Heater Duty: {heater_pwm.duty_u16() / MAX_PWM * 100:.0f} %")
        
    # Wait before next measurement/control loop
    utime.sleep(5) # Read and update every 5 seconds