#!/usr/bin/python
import smbus
import time
import math

bus = smbus.SMBus(1)
address = 0x1e
f = open('mydata.dat', 'w')
results=[]

def read_byte(adr):
    return bus.read_byte_data(address, adr)

def read_word(adr):
    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr+1)
    val = (high << 8) + low
    return val

def read_word_2c(adr):
    val = read_word(adr)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val

def write_byte(adr, value):
    bus.write_byte_data(address, adr, value)

write_byte(0, 0b01110000) # Set to 8 samples @ 15Hz
write_byte(1, 0b00100000) # 1.3 gain LSb / Gauss 1090 (default)
write_byte(2, 0b00000000) # Continuous sampling

scale = 0.92

minx = 0
maxx = 0
miny = 0
maxy = 0

for i in range(0,500):
    x_out = read_word_2c(3)
    y_out = read_word_2c(7)
    z_out = read_word_2c(5)
    results.append([x_out,y_out])
    
    if x_out < minx:
        minx=x_out
    if y_out < miny:
        miny=y_out
    if x_out > maxx:
        maxx=x_out
    if y_out > maxy:
        maxy=y_out
    
    time.sleep(0.1)
    
print "minx: ", minx
print "miny: ", miny
print "maxx: ", maxx
print "maxy: ", maxy
x_offset = (maxx + minx) / 2
y_offset = (maxy + miny) / 2
print "x offset: ", x_offset
print "y offset: ", y_offset

for i in results:
    data = "{} {}\n".format((i[0] - x_offset) * scale, (i[1] - y_offset) * scale)
    f.write(data)

