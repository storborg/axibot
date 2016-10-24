import sys

import matplotlib.pyplot as plt

from axibot import moves
from axibot.svg import generate_actions


if len(sys.argv) <= 1:
    print("usage: %s <filename.svg>" % sys.argv[0])
    exit(1)

filename = sys.argv[1]
print("Rendering %s" % filename)
actions = generate_actions(filename, pen_up_position=85, pen_down_position=35)

up_xdata = [0]
up_ydata = [0]
down_xdata = [0]
down_ydata = [0]

x = 0
y = 0

pen_up = False
for move in actions:
    if isinstance(move, moves.PenDownMove):
        pen_up = False
    elif isinstance(move, moves.PenUpMove):
        pen_up = True
    elif isinstance(move, moves.XYMove):
        x += move.dx
        y += move.dy
        if pen_up:
            up_xdata.append(x)
            up_ydata.append(y)
        else:
            down_xdata.append(x)
            down_ydata.append(y)


plt.plot(up_xdata, up_ydata, 'gs', down_xdata, down_ydata, 'rs')

# plt.show()

print("Saving to motion.png...")
plt.savefig('motion.png')
