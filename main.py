################################################
#
# Software: Dream_Control
# Description: 
#   Dream control with acoustically trigger from sensors.
#   Script runs automatically after reboot or "CTRL + D".
#   Input: 
#       -Heartbeat -> Must be attached to the fingertip
#       -Muscle activity -> Must be attachted to the finger
#       -Skin voltage residence -> Must be attached to the arm
#   Output:
#       -Buzzer
# Logger file: 
#   Trace: actualTime(UTC);heartbeat;muscleActivity;skinResistence;wakeUpTrigger
# Target System: Pyboard D (Small)
# Autor: Marco Stucki / Alex Merz
# Date: 08.03.2021
#
################################################

################################################
# Library
################################################
import pyb
import utime
from pyb import Pin, ADC, Timer
import json
import sys
import musictone

################################################
# Script start
################################################
print("---------------------------------")
print("Dream-Control software started...")

################################################
# Constant definition
################################################
TRACE_LOGGER_PATH = "/sd/trace_log.txt"
CONFIG_PATH = "/sd/config.JSON"

MAX_NBR_SWITCH = 5

################################################
# OnBoard definition
################################################
red_led_board = pyb.LED(1)
green_led_board = pyb.LED(2)
blue_led_board = pyb.LED(3)

switch = pyb.Switch()

################################################
# Input definition
################################################
heartbeat = ADC(Pin('X11'))
muscleActivity = ADC(Pin('X12'))
skinResistence = ADC(Pin('Y8'))

################################################
# Output definition
################################################
# Set up pin PWM timer for output to buzzer
p2 = Pin("Y11") # Pin Y11 with timer 8 Channel 2
tim = Timer(8, freq=3000)
ch = tim.channel(2, Timer.PWM, pin=p2)

################################################
# play_music function definition
################################################
def play_music():
    for i in song:
        if i == 0:
            ch.pulse_width_percent(0)
        else:
            tim.freq(i) # change frequency for change tone
            ch.pulse_width_percent(30)

        pyb.delay(150)

################################################
# Turn on led
################################################
red_led_board.on()
green_led_board.on()
blue_led_board.on()

utime.sleep(1)

green_led_board.off()
blue_led_board.off()

################################################
# Load Cfg file
################################################
# Get data from file
try:
    config = open(CONFIG_PATH, "r")
except OSError:
    red_led_board.off()
    blue_led_board.on()
    print("SD card not found -> Abort software")
    sys.exit()

data = json.load(config)
config.close()

heartbeat_min = data['heartbeat_min']
heartbeat_max = data['heartbeat_max']

muscle_min = data['muscle_min']
muscle_max = data['muscle_max']

skinresistence_min = data['skinresistence_min']
skinresistence_max = data['skinresistence_max']

delaySensorUpdate = data['delay_sensor_update']
maxNbrWakeUp = data['max_nbr_wake_up']

# Define song (Switch case)
def select_song(argument):
    switcher = {
        0: musictone.shortbeep,
        1: musictone.longbeep,
        2: musictone.pacman,
        3: musictone.starwars,
        4: musictone.sleep,
        5: musictone.beethoven,
        6: musictone.gameofthrones,
        7: musictone.harrypotter,
        8: musictone.nevergonnagiveyouup,
        9: musictone.pinkpanter,
        10: musictone.mario
    }
    return switcher.get(argument, "Nothing")

song = select_song(data['song_nbr'])

utime.sleep(1)
red_led_board.off() # Loading finished

################################################
# MAIN loop
################################################
counterWakeUp = 0 # Reset counter
counterSwitch = 0 # Reset counter
wakeUpTrigger = 0

while (counterWakeUp < maxNbrWakeUp):
    ### Song test if button is pressed
    if (switch.value()):
        if (counterSwitch > MAX_NBR_SWITCH):
            play_music()
            counterSwitch = 0 # Reset counter
        else:
            counterSwitch = counterSwitch + 1
    else:
        counterSwitch = 0 # Reset counte

    ### Get sensor data
    heartbeatTemp = heartbeat.read()
    #print(heartbeatTemp) # Debugging reason
    muscleActivityTemp = muscleActivity.read()
    #print(muscleActivityTemp) # Debugging reason
    skinResistenceTemp = skinResistence.read()
    #print(skinResistenceTemp) # Debugging reason

    ### Get actual time (UTC)
    actualTime = utime.time()

    ### Check if all sensor data are in defined range
    if ((heartbeatTemp < heartbeat_max) and (heartbeatTemp > heartbeat_min) and 
        (muscleActivityTemp < muscle_min) and (muscleActivityTemp > muscle_max) and 
        (skinResistenceTemp < skinresistence_min) and (skinResistenceTemp > skinresistence_max)):
        # Information for logger
        wakeUpTrigger = 1 
        # Update counter
        counterWakeUp = counterWakeUp + 1
        #Buzzer
        play_music()
        # Delay so that for same situation it wouldn't be triggered again
        utime.sleep(3)

    ### Log data for tracing
    traceLogger = open(TRACE_LOGGER_PATH, "a")
    traceLogger.write(str(actualTime) + ";" + str(heartbeatTemp) + ";" + str(muscleActivityTemp) + ";" + str(skinResistenceTemp) + ";" + str(wakeUpTrigger) + "\n")
    traceLogger.close()

    wakeUpTrigger = 0 # Reset

    ### Delay for next cycle
    utime.sleep_ms(delaySensorUpdate)

################################################
# Script end
################################################
green_led_board.on() # Signalisation, that this script has ended

print("Dream-Control software end")
print("---------------------------------")