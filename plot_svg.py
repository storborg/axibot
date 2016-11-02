import sys

import matplotlib.pyplot as plt

from axibot import moves, config
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


def undo_coordinate_transform(move):
    m1 = move.dx
    m2 = move.dy
    x = m1 + m2
    y = m1 - m2
    return x, y


def print_bounds(up_xdata, up_ydata, down_xdata, down_ydata):
    xmin = min(min(up_xdata), min(down_xdata))
    ymin = min(min(up_ydata), min(down_ydata))
    xmax = max(max(up_xdata), max(down_xdata))
    ymax = max(max(up_ydata), max(down_ydata))

    print("X step range:\t%d\t\t%d" % (xmin, xmax))
    print("Y step range:\t%d\t\t%d" % (ymin, ymax))

    print("X size range:\t%0.2f\t\t%0.2f" % (xmin / config.SPEED_SCALE,
                                             xmax / config.SPEED_SCALE))
    print("Y size range:\t%0.2f\t\t%0.2f" % (ymin / config.SPEED_SCALE,
                                             ymax / config.SPEED_SCALE))


pen_up = False
for move in actions:
    if isinstance(move, moves.PenDownMove):
        pen_up = False
    elif isinstance(move, moves.PenUpMove):
        pen_up = True
    elif isinstance(move, moves.XYMove):
        dx, dy = undo_coordinate_transform(move)
        x += dx
        y += dy
        if pen_up:
            up_xdata.append(x)
            up_ydata.append(y)
        else:
            down_xdata.append(x)
            down_ydata.append(y)


print_bounds(up_xdata, up_ydata, down_xdata, down_ydata)

plt.plot(up_xdata, up_ydata, 'gs', down_xdata, down_ydata, 'rs')
plt.show()

#print("Saving to motion.png...")
#plt.savefig('motion.png')
