import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# get inputs from user
print("=== Projectile Motion Animator ===")
angle = float(input("Launch angle (degrees): "))
velocity = float(input("Initial velocity (m/s): "))
gravity = float(input("Gravity (m/s², default 9.8): ") or 9.8)

# convert angle to radians
angle_rad = angle * math.pi / 180

# split velocity into components
vx = velocity * math.cos(angle_rad)
vy = velocity * math.sin(angle_rad)

# calculate key values
total_time = (2 * vy) / gravity
max_range  = vx * total_time
max_height = (vy ** 2) / (2 * gravity)

print()
print(f"Max Range:   {max_range:.2f} m")
print(f"Max Height:  {max_height:.2f} m")
print(f"Flight Time: {total_time:.2f} s")

# pre-compute all the points so we can index into them each frame
x_points = []
y_points = []

t  = 0
dt = 0.05

while t <= total_time + dt:
    x = vx * t
    y = vy * t - 0.5 * gravity * t ** 2
    if y < 0:
        y = 0
    x_points.append(x)
    y_points.append(y)
    t = round(t + dt, 4)

# --- set up the figure ---
fig, ax = plt.subplots(figsize=(10, 5))

ax.set_xlim(0, max_range * 1.05)
ax.set_ylim(0, max_height * 1.3)
ax.set_xlabel("Horizontal Distance (m)")
ax.set_ylabel("Height (m)")
ax.set_title(f"Projectile Motion  |  angle={angle}°  v₀={velocity} m/s  g={gravity} m/s²")
ax.grid(True, alpha=0.3)

# draw a faint "ghost" of the full path so you can see where it's going
ax.plot(x_points, y_points, color="royalblue", linewidth=1, alpha=0.2, linestyle="--")

# these are the things that will actually animate
trail_line, = ax.plot([], [], color="royalblue", linewidth=2, label="trajectory")
dot,        = ax.plot([], [], "o", color="royalblue", markersize=8)

# mark peak and landing (drawn upfront, they'll appear the whole time)
ax.plot(max_range / 2, max_height, "ro", markersize=7, label=f"peak ({max_height:.1f} m)")
ax.plot(max_range,     0,          "gs", markersize=7, label=f"landing ({max_range:.1f} m)")
ax.axvline(x=max_range / 2, color="red",   linestyle="--", linewidth=0.7, alpha=0.4)
ax.axhline(y=max_height,    color="red",   linestyle="--", linewidth=0.7, alpha=0.4)

ax.legend()
plt.tight_layout()

# --- animation functions ---

def init():
    trail_line.set_data([], [])
    dot.set_data([], [])
    return trail_line, dot

def update(frame):
    # frame is just the index into our pre-computed points list
    # show all points up to the current frame as the trail
    trail_line.set_data(x_points[:frame+1], y_points[:frame+1])

    # move the dot to the current position
    dot.set_data([x_points[frame]], [y_points[frame]])

    return trail_line, dot

# interval = time between frames in milliseconds
# lower = faster animation
ani = animation.FuncAnimation(
    fig,
    update,
    frames=len(x_points),
    init_func=init,
    interval=30,
    blit=True,
    repeat=False   # stop after one full flight
)

plt.show()
print("done!")