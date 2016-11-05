import matplotlib.pyplot as plt
from svg.path import parse_path

from axibot import transform


subdivide = 100


# Make an arc path
#s = 'A 30 52 37 0 1 100 100'
s = 'A 20 10 0 0 0 40 0'

base_path = parse_path(s)
new_path = parse_path(s)

# Make a matrix for a simple operation
#matrix = transform.parse('scale(0.5)')
#matrix = transform.parse('translate(10, 0)')
#matrix = transform.compose(transform.parse('translate(40, 0)'),
#                           transform.parse('scale(0.5)'))
#matrix = transform.identity

# Scale the arc path into a new path
transform.apply(new_path, transform.parse('scale(0.5)'))
transform.apply(new_path, transform.parse('translate(4, 0)'))

print("base start %r" % base_path[0].start)
print("base end %r" % base_path[0].end)
print("new start %r" % new_path[0].start)
print("new end %r" % new_path[0].end)
print("new dict %r" % new_path[0].__dict__)


def plot_path(path, spec):
    x = []
    y = []
    for n in range(subdivide):
        pt = path.point(n / subdivide)
        x.append(pt.real)
        y.append(pt.imag)
    plt.plot(x, y, spec)

# Plot original path in green
plot_path(base_path, 'g-')

# Plot new path in red
plot_path(new_path, 'r-')

plt.show()
