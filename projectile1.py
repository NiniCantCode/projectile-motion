import math

# projectile motion calculator
# basically just using the kinematic equations lol

print("=== Projectile Motion Calculator ===")
print()

# get inputs from user
angle = float(input("Enter launch angle (degrees): "))
velocity = float(input("Enter initial velocity (m/s): "))
gravity = float(input("Enter gravity (default is 9.8): ") or 9.8)

# convert angle to radians because math.sin wants radians not degrees
angle_rad = angle * math.pi / 180

# break velocity into x and y components
vx = velocity * math.cos(angle_rad)
vy = velocity * math.sin(angle_rad)

# calculate the main stuff
total_time = (2 * vy) / gravity
max_range = vx * total_time
max_height = (vy ** 2) / (2 * gravity)

print()
print("--- Results ---")
print(f"Max Range:   {max_range:.2f} m")
print(f"Max Height:  {max_height:.2f} m")
print(f"Flight Time: {total_time:.2f} s")

# now lets print the trajectory step by step
print()
print("--- Trajectory (every 0.1 seconds) ---")
print(f"{'Time':>6} | {'X':>10} | {'Y':>10}")
print("-" * 32)

t = 0
dt = 0.1  # time step

while t <= total_time:
    x = vx * t
    y = vy * t - 0.5 * gravity * t ** 2

    # stop y from going negative (hits the ground)
    if y < 0:
        y = 0

    print(f"{t:>6.2f} | {x:>10.2f} | {y:>10.2f}")
    t += dt
    t = round(t, 2)  # floating point is annoying without this

print()
print("done!!")