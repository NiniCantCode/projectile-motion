import math
import matplotlib.pyplot as plt

# projectile motion calculator - now with graphs!!
print("=== Projectile Motion Calculator ===")
print()

angle = float(input("Enter launch angle (degrees): "))
velocity = float(input("Enter initial velocity (m/s): "))
gravity = float(input("Enter gravity (default is 9.8): ") or 9.8)

angle_rad = angle * math.pi / 180

vx = velocity * math.cos(angle_rad)
vy = velocity * math.sin(angle_rad)

total_time = (2 * vy) / gravity
max_range = vx * total_time
max_height = (vy ** 2) / (2 * gravity)

print()
print("--- Results ---")
print(f"Max Range:   {max_range:.2f} m")
print(f"Max Height:  {max_height:.2f} m")
print(f"Flight Time: {total_time:.2f} s")

# collect x and y points for the graph
x_points = []
y_points = []

t = 0
dt = 0.05  # smaller step = smoother curve

while t <= total_time:
    x = vx * t
    y = vy * t - 0.5 * gravity * t ** 2
    if y < 0:
        y = 0
    x_points.append(x)
    y_points.append(y)
    t += dt
    t = round(t, 4)

# --- plotting ---
plt.figure(figsize=(10, 5))
plt.plot(x_points, y_points, color="royalblue", linewidth=2, label="trajectory")

# mark the peak
plt.plot(max_range / 2, max_height, "ro", markersize=8, label=f"peak ({max_height:.1f} m)")

# mark landing spot
plt.plot(max_range, 0, "gs", markersize=8, label=f"landing ({max_range:.1f} m)")

# dotted lines to peak just so it looks nice
plt.axvline(x=max_range / 2, color="red", linestyle="--", linewidth=0.8, alpha=0.5)
plt.axhline(y=max_height, color="red", linestyle="--", linewidth=0.8, alpha=0.5)

plt.title(f"Projectile Motion  |  angle={angle}°  v₀={velocity} m/s  g={gravity} m/s²")
plt.xlabel("Horizontal Distance (m)")
plt.ylabel("Height (m)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print("graph should've popped up!")