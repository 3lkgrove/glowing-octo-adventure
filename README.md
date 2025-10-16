# RP2040-ZERO Filament Dryer
⚠️ Essential Hardware Considerations
Heater Control: A 150W PTC heater will draw about 12.5A at 12V. You MUST use a logic-level Power MOSFET (or solid-state relay) with a suitable current rating (e.g., 30A or more) and an appropriate heatsink to switch the heater's 12V power. Use Pulse Width Modulation (PWM) from the RP2040 to control the heater's power for temperature regulation.

Fan Control: You'll likely use another MOSFET to switch the fans. The fans are used to circulate the air and help with humidity reduction by heating the air (which lowers the relative humidity).

Power Supply: The 110V to 12V 240W supply is sufficient (20A maximum) for the 150W heater and fans, but you'll need a separate 3.3V regulator (or buck converter) for the RP2040, DHT22, and OLED display, as the 12V supply is too high.

Humidity Control Strategy: Since you are heating a sealed box, the only way to lower relative humidity is to increase the temperature. The program below uses the heater to increase the temperature when the humidity is too high, thereby lowering the relative humidity to the 30% target. The fans aid in air circulation for even heating/sensing.

MicroPython Program (RP2040-ZERO)
This program uses a simple Proportional (P) control for the heater based on the humidity error.

⚙️ Setup and Implementation Steps
1. Wiring (Crucial)
Component	RP2040-ZERO Pin	Notes
DHT22 Data	GPIO 28	Use a pull-up resistor (4.7k Ω)
OLED SDA	GPIO 0	I2C Bus 0
OLED SCL	GPIO 1	I2C Bus 0
Heater MOSFET Gate	GPIO 7	Connect to the gate of the MOSFET
Fan MOSFET Gate	GPIO 8	Connect to the gate of the Fan MOSFET
RP2040 Power	5V / GND	Onboard PS. See attached schematic
Heater Power	12V PS via MOSFET	
Fan Power	12V PS via MOSFET	

Export to Sheets
2. Software Requirements
You must install these MicroPython libraries on your RP2040-ZERO:

dht library: For the DHT22 sensor.

ssd1306 library: For the OLED display.

These can usually be installed using upip or by manually copying the .py files to your board's filesystem (e.g., in a lib folder).

3. Tuning
The key to stable control is the HUMIDITY_KP value.

If the humidity overshoots (goes much lower than 30% and oscillates), the value is likely too high. Reduce it (e.g., from 5.0 to 2.0).

If the humidity takes too long to reach 30%, the value is likely too low. Increase it (e.g., from 5.0 to 7.0).

Start with 5.0 and observe the system's performance.

# Adjust Target Humidity
How to Use It from the CLI/REPL
Upload the modified main.py to your RP2040-ZERO.

Connect to the RP2040-ZERO's serial port using a tool like PuTTY, Tera Term, or the Thonny IDE.

Stop the running script by pressing Ctrl+C (this enters the REPL prompt >>>).

Import the function from your main module:

>>> import main
Call the function to change the target:

>>> main.set_target_humidity(45.0)
Target humidity successfully updated to: 45.0 %
45.0
(The print statement confirms the change, and the returned value is shown by the REPL.)

Run the main program again:

>>> main.while_true()
(If your code is in a while True loop outside a function, you might need to use a soft reset (Ctrl+D) to restart the program using the new global value. The best practice is to put your main loop inside a function, e.g., def run(): and then call main.run()).

# PCB Layout
![PCB](/Images/PCB_ISO_0.png)
![PCB](/Images/PCB_ISO_1.png)
