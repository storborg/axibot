import math
import matplotlib.pyplot as plt

from axibot import planning


vmax = 1.0
n = 200
amax = math.pi

adata = [(amax / n) * x for x in range(n)]
vdata = [planning.cornering_velocity(angle, vmax) for angle in adata]

plt.plot(adata, vdata, 'r-')
plt.show()
