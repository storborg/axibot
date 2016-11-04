import matplotlib.pyplot as plt
from svg.path import parse_path

from axibot import transform


subdivide = 100


# Make an arc path
base_path = parse_path('A 30 50 0 0 1 100 100')
new_path = parse_path('A 30 50 0 0 1 100 100')

# Make a matrix for a simple operation
# matrix = transform.parse('scale(0.5')
# matrix = transform.parse('translate(1, 1)')
matrix = transform.identity

# Scale the arc path into a new path
transform.apply(new_path, matrix)


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
