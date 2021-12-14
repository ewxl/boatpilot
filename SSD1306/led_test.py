#!/usr/bin/python3

import time
import SSD1306


from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

d = SSD1306.SSD1306_128_64(rst=None)

d.begin()
d.clear()
d.display()

image = Image.new('1', (d.width, d.height))
# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,d.width,d.height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = 2
shape_width = 20
top = padding
bottom = 32-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = padding
# Draw an ellipse.
draw.ellipse((x, top , x+shape_width, bottom), outline=255, fill=0)
x += shape_width+padding
# Draw a rectangle.
draw.rectangle((x, top, x+shape_width, bottom), outline=255, fill=0)
x += shape_width+padding
# Draw a triangle.
draw.polygon([(x, bottom), (x+shape_width/2, top), (x+shape_width, bottom)], outline=255, fill=0)
x += shape_width+padding
# Draw an X.
draw.line((x, bottom, x+shape_width, top), fill=255)
draw.line((x, top, x+shape_width, bottom), fill=255)
x += shape_width+padding

d.image(image)
d.display()

#for c in [0xae,0xd5,0x80,0xa8,0x3f,0xd3,0x0,0x4,0x8d,0x10,0x20,0x0,0xa1,0xc8,0xda,0x12,0x81,0x9f,0xd9,0x22,0xdb,0x40,0xa4,0xa6]:
#    cmd(c)
#    print(c)

#for x in range(64,92):
#    print(hex(x),hex(read(x)))
#time.sleep(0.1)



