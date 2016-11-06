import matplotlib.pyplot as plt
from axibot import planning


dist = 2000

dtarray = planning.interpolate_pair((0, 0), 0, (dist, 0), 0, False)

vdata = [0.0]
xdata = [0.0]
tdata = [0.0]

t = 0
prev_x = 0

for x, duration in dtarray:
    t += duration
    v = (x - prev_x) / duration
    prev_x = x
    vdata.append(v)
    xdata.append(x)
    tdata.append(t)


fig, ax1 = plt.subplots()

ax1.plot(tdata, vdata, 'rs')
ax1.set_xlabel('time (s)')
ax1.set_ylabel('v', color='r')
for t1 in ax1.get_yticklabels():
    t1.set_color('r')

ax2 = ax1.twinx()
ax2.plot(tdata, xdata, 'gs')
ax2.set_ylabel('x', color='g')
for t1 in ax2.get_yticklabels():
    t1.set_color('g')

print("vdata %r\n" % vdata)
print("xdata %r\n" % xdata)
print("tdata %r\n" % tdata)

plt.show()
