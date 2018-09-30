#!/usr/bin/env python

import time
import argparse
import random

from neopixel import *

# LED strip configuration:
LED_COUNT      = 5*5*5   # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

class RGB:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def scale(self, factor):
        return RGB(self.r * factor, self.g * factor, self.b * factor)

    def color(self):
        return Color(int(self.r), int(self.g), int(self.b))

    @staticmethod
    def random():
        return RGB(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def coordinate_to_pixel(x, y, z):
    if z % 2 == 1:
        x, y = y, x
        x = 4 - x
        y = 4 - y
    return x + (y * 5) + (z * 5 * 5)

class Animation:
    def __init__(self):
        pass

class Fade(Animation):
    def __init__(self, strip, pixel, duration, rgb):
        self.started = time.clock()
        self.strip = strip
        self.duration = duration
        self.pixel = pixel
        self.rgb = rgb

class FadeIn(Fade):
    def tick(self, cube):
        cube.set(self.pixel, 1)

        elapsed = (time.clock() - self.started) * 1000.0
        if elapsed > self.duration:
            self.strip.setPixelColor(self.pixel, self.rgb.color())
            return False
        factor = elapsed / self.duration
        self.strip.setPixelColor(self.pixel, self.rgb.scale(factor).color())
        return True

class FadeOut(Fade):
    def tick(self, cube):
        elapsed = (time.clock() - self.started) * 1000.0
        if elapsed > self.duration:
            self.strip.setPixelColor(self.pixel, Color(0, 0, 0))
            cube.set(self.pixel, 0)
            return False
        factor = (self.duration - elapsed) / self.duration
        self.strip.setPixelColor(self.pixel, self.rgb.scale(factor).color())
        return True

class RgbCube:
    def __init__(self, strip):
        self.state = [ 0 ] * 5 * 5 * 5
        self.strip = strip
        self.animations = []

    def has_animations(self):
        return len(self.animations) > 0

    def add(self, a):
        self.animations.append(a)

    def random_that_is(self, value):
        animating = [a.pixel for a in self.animations]
        candidates = [index for index, x in enumerate(self.state) if x == value and index not in animating]
        if len(candidates) == 0:
            return None
        return random.choice(candidates)

    def random(self):
        x = random.randint(0, 4)
        y = random.randint(0, 4)
        z = random.randint(0, 4)
        c = coordinate_to_pixel(x, y, z)
        return c

    def get(self, c):
        return self.state[c]

    def set(self, c, value):
        self.state[c] = value

    def show(self):
        self.strip.show()

    def tick(self):
        self.animations[:] = [a for a in self.animations if a.tick(self)]
        self.strip.show()

    def flush(self):
        while self.has_animations():
            self.tick()

def sparkle(strip):
    cube = RgbCube(strip)
    number_to_fill = 30;
    duration = 3000

    color = RGB.random()
    delay = time.clock()
    loop = 0
    while loop < number_to_fill:
        if time.clock() > delay:
            c = cube.random_that_is(0)
            if c:
                cube.add(FadeIn(strip, c, duration, color))
                delay = time.clock() + random.random() * 0.150
                loop += 1
        cube.tick()

    loop = 0;
    started = time.clock()
    while time.clock() - started < 10:
        c1 = cube.random_that_is(0)
        c2 = cube.random_that_is(1)

        if c1 and c2:
            cube.add(FadeIn(strip, c1, duration, color))
            cube.add(FadeOut(strip, c2, duration, color))

        cube.tick()

    loop = 0;
    while loop < number_to_fill:
        c = cube.random_that_is(1)
        if c:
            cube.add(FadeOut(strip, c, duration, color))
            loop += 1
        cube.tick()

    cube.flush()

def test(strip):
    sparkle(strip)

def fill(strip, color):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()

def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, color)
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i+j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, wheel((i+j) % 255))
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def hazy(strip):
    pass

# Main program logic follows:
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    try:
        while True:
            test(strip)

        if False:
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, Color(255, 255, 255))
                strip.show()
                time.sleep(100 / 1000.0)
                strip.setPixelColor(i, Color(0, 0, 0))

            for v in range(255):
                fill(strip, Color(v, v, v))
                time.sleep(10 / 1000.0)
            for v in range(255):
                fill(strip, Color(v, 0, 0))
                time.sleep(10 / 1000.0)
            for v in range(255):
                fill(strip, Color(v, 0, v))
                time.sleep(10 / 1000.0)
            rainbowCycle(strip)
            fill(strip, Color(0, 0, 0))
            # time.sleep(5)
            # fill(strip, Color(255, 255, 255))
            # time.sleep(5)
    except KeyboardInterrupt:
        fill(strip, Color(0, 0, 0))
