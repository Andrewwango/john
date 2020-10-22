# john
## Summary
John is a fully automated pavement litter-picking robot, to be used in urban settings at night, guided by ultrasound, IR, compass and GPS. John is a prototype built around the Raspberry Pi and the Lego Mindstorms set, with added homemade sensors, and coded in Python. Read the [source](src/main.py) and below for more details!

This project was submitted to the 2017 National Young Scientists and Engineers Competition. The project was selected as a finalist to be exhibited at the Big Bang Fair and came runner up in the Intermediate age category out of ~300 finalists. View the video submission [here](https://youtu.be/SZ_vZ9dfDFE).

Read below for the project report (taken from my competition submission). [Here](images) are some images taken from the 2017 Big Bang Fair exhibition at the NEC, Birmingham. 

All rights reserved
Andrew Wang 2016

## Project Report
### Introduction
I designed and built John as a 4-wheeled robot to replace, or more realistically, aid the employment of human litter pickers on the street. By utilising ultrasonic and infrared sensor-based navigation, object detection, and an algorithmically controlled grabber, John is able to strategically cover a pavement, detect litter, and clear it up, all without human input.

### Concept
Each year, a staggering average of almost £1bn (telegraph.co.uk) is spent on the manual removal of litter in the UK. Although campaigns to discourage littering have existed, the problem still persists, and existing financially and practically viable solutions (like cumbersome man-driven machines) have evidently not proven particularly effective. As a result of the need to reduce both the clutter on the streets and the money spent towards eliminating it, I felt motivated to create John. The reason for which I selected this topic was because of my belief in the importance of protecting the environment, towards which littering has a clear negative effect; apart from using up taxpayers’ money for the removal of it, litter is also both an eyesore and a contributor to the harm of urban-dwelling animals, thereby urging me to try and make a change in order to benefit society and the environment.

As with all new developments, several years would probably be necessary to perfect the final product; therefore, I strived to instead pave the path to solve the problem, although I tried my best to do so. Subsequently, my target was not a 100% effective machine, but rather, I hoped to create a working, demonstrative model, as if it were an interim proof of concept.

### Process
The project is orientated around a Raspberry Pi (Linux-based single-board computer) paired with a BrickPi (NXT-Pi interfacing shield), a reasonable cost-flexibility compromise. The main ‘John’ program’s code is written in Python. As will be explained below, this framework was expanded using other technologies.

I organised the work concerning John into 3 sections: navigation, detection and picking, and during each process I of course encountered many, many problems. First of all, I was faced with the problem of covering a pavement (or street) effectively, and I created a few algorithms to deal with this, the best of which involved John zigzagging much like the ball does in a game of “Pong”, at an angle of 75 degrees to the path (90 minus half of the ultrasonic sensor measuring angle range, measured using the motor’s encoder to increase precision). It works well, though somewhat inefficiently, as is shown in the video, the motorised wheels supported by 3D-printed marble casters. 

One of the biggest challenges I faced was that of detecting litter. How was I going to differentiate between a piece of litter, a wall or anything in between? Initially, I considered measuring a distance with an ultrasonic sensor, then panning it upwards, taking another reading; then, a wall would be registered if both readings were to suggest that something is close, litter if only the bottom reading were too. The robot would then respond accordingly, activating litter-picking or turning procedures. However, this hands a lot of the measurements’ precision over to the errors in a moving sensor. Therefore, the most viable solution was to install two ultrasonic sensors, which I built and connected to the GPIO (General Purpose Input/Output) pins on the Raspberry Pi. Having built this, I tested the robot for the optimal distance range within which the grabber can pick up litter and implemented it into the code. In order to ensure reliability (and remove anomalies) when the sensor takes measurements, John was programmed to take the median of several readings (although its accuracy isn’t great, not succeeding in detecting everything).

Real-life function of the robot was considered, and thus cliff detection came into play, to make sure that John doesn’t fall off pavements. To do this, I chose an infrared sensor (to minimise the amount of ultrasound interfering with one another), building it myself and again utilising the Pi’s GPIO ports. A similar tuning process was undergone to find the distance at which ground would be detected underneath the robot. I think that this build was reliable and cost efficient.

Finally, the method using which John picks up litter was a big challenge at first. How would it, after having detected litter, put it into some kind of bin? The solution was to design a grabber and arm, which I built after many prototypes, to grab litter and bring it over into a bin. The arm was designed to use minimum energy by placing the grabber motor close to the pivot of the arm, to reduce its turning force. The final design (shown in the video) utilises elastic bands (as opposed to my initial idea, a ratchet, which would’ve been too cumbersome to install) to reduce the energy input needed to bring the arm upwards, and to keep the arm in position when the ultrasonic sensor takes readings. Overall, by solving these problems step by step, an almost fool-proof arm was constructed.
