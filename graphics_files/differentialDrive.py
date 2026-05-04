"""
Core differential 
"""
import adafruit_dacx578
import busio
import board
import time

# 1. Initialize I2C and DAC
i2c = board.I2C()
dac = adafruit_dacx578.DACx578(i2c)

# WAKE UP THE INTERNAL REFERENCE
dac.internal_reference = True

# 2. Define Ranges
# because its only a 10 bit DAC the last six bits of data are just removed (65536 is 16 bit)
true_max = 65535 

# Activation range (0% to 80%)
activation_range = (0, 80) 

min_val = (true_max / 100) * activation_range[0]
max_val = (true_max / 100) * activation_range[1]

# 3. The Differential Drive Function
def get_differential_drive(input_val, min_limit, max_limit):
    """
    Maps an input from -1.0 to 1.0 to two differential DAC outputs.
    input_val = 0.0 outputs the exact midpoint voltage on both channels.
    """
    # Clamp the input to ensure we never accidentally blow past our bounds
    input_val = max(min(input_val, 1.0), -1.0)
    
    # Find your "fake 0 volts" (the middle of the range)
    midpoint = (max_limit + min_limit) / 2
    
    # Calculate how far we can swing from the midpoint
    amplitude = (max_limit - min_limit) / 2
    
    # Channel 1 goes UP from the midpoint, Channel 2 goes DOWN symmetrically
    ch1 = midpoint + (amplitude * input_val)
    ch2 = midpoint - (amplitude * input_val)
    
    return int(ch1), int(ch2)

# 4. Main Loop to Test
# We will sweep the input back and forth from -1.0 to 1.0
current_input = -1.0
step_size = 0.05

print("Starting differential drive test...")

while True:
    # 1. Get the values from your function
    pin1_val, pin2_val = get_differential_drive(current_input, min_val, max_val)
    
    # 2. Write them to the DAC channels
    dac.channels[1].value = pin1_val
    dac.channels[2].value = pin2_val
    dac.channels[3].value = pin1_val
    dac.channels[4].value = pin2_val
    
    # 3. Print the status so you can verify the symmetry
    print(f"Input: {current_input:>5.2f} | Ch1: {pin1_val:>5} | Ch2: {pin2_val:>5}")
    
    # 4. Increment the sweep
    current_input += step_size
    
    # Reverse direction if we hit the boundaries (bounce back and forth)
    if current_input >= 1.0 or current_input <= -1.0:
        step_size *= -1 
        
