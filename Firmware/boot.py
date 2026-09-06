import board
import digitalio
import storage

# 1. Set the Row Pin (GP6) as an Output set to LOW
row = digitalio.DigitalInOut(board.GP6)
row.direction = digitalio.Direction.OUTPUT
row.value = False

# 2. Set the Column Pin (GP10) as an Input with Pull-Up
col = digitalio.DigitalInOut(board.GP10)
col.direction = digitalio.Direction.INPUT
col.pull = digitalio.Pull.UP

# 3. Check button state: 
# When pressed, GP10 connects to GP6 (LOW), so col.value becomes False
if col.value:
    # Button is NOT pressed -> Hide the USB storage drive
    storage.disable_usb_drive()
else:
    # Button IS pressed -> Keep USB drive mounted
    pass

# Clean up GPIOs so code.py can re-initialize them without conflicts
row.deinit()
col.deinit()