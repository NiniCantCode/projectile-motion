import matplotlib
matplotlib.use('MacOSX')
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection
from matplotlib.widgets import Button

# ── colour palette for multi-shot compare ────────────────────────────────────
SHOT_COLORS = ["royalblue", "tomato", "mediumseagreen", "darkorchid", "darkorange"]

# ═════════════════════════════════════════════════════════════════════════════
#  INPUT
# ═════════════════════════════════════════════════════════════════════════════
print("=== Projectile Motion Animator ===")
angle    = float(input("Launch angle (degrees): "))
velocity = float(input("Initial velocity (m/s): "))
raw      = input("Gravity (m/s², default 9.8): ").strip()
gravity  = float(raw) if raw else 9.8

# ═════════════════════════════════════════════════════════════════════════════
#  PHYSICS HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def compute_trajectory(angle_deg, vel, grav, dt=0.04):
    """Return arrays of x, y, t, and speed for a full flight."""
    rad    = math.radians(angle_deg)
    vx     = vel * math.cos(rad)
    vy     = vel * math.sin(rad)
    t_end  = (2 * vy) / grav

    t_arr  = np.arange(0, t_end + dt, dt)
    x_arr  = vx * t_arr
    y_arr  = np.maximum(0.0, vy * t_arr - 0.5 * grav * t_arr**2)

    # instantaneous speed at each sample
    vy_arr    = vy - grav * t_arr
    speed_arr = np.hypot(vx, vy_arr)

    # ── eased frame schedule: more frames near the apex so the ball "hangs" ──
    # weight ∝ 1/speed  →  slow where the ball is slow
    weights   = 1.0 / np.maximum(speed_arr, 0.5)   # avoid /0 at peak
    weights  /= weights.sum()
    cumw      = np.cumsum(weights)

    n_frames  = max(60, len(t_arr) * 2)
    uniform   = np.linspace(0, 1, n_frames)
    frame_idx = np.searchsorted(cumw, uniform).clip(0, len(t_arr) - 1)

    return {
        "x":       x_arr,
        "y":       y_arr,
        "t":       t_arr,
        "speed":   speed_arr,
        "fidx":    frame_idx,        # eased frame → sample-index mapping
        "range":   float(x_arr[-1]),
        "max_h":   float(y_arr.max()),
        "t_total": float(t_end),
        "vx":      vx,
        "vy":      vy,
    }


# ═════════════════════════════════════════════════════════════════════════════
#  SPEED-COLOURED TRAIL  (LineCollection trick)
# ═════════════════════════════════════════════════════════════════════════════

def make_speed_segments(x, y):
    """Package (x,y) into the segment format LineCollection needs."""
    pts  = np.array([x, y]).T.reshape(-1, 1, 2)
    segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
    return segs


def build_speed_collection(ax, x, y, speed, cmap="plasma", lw=2.5, alpha=0.85):
    segs = make_speed_segments(x, y)
    lc   = LineCollection(segs, cmap=cmap, linewidth=lw, alpha=alpha,
                          capstyle="round")
    lc.set_array(speed)          # colour by speed value
    lc.set_clim(speed.min(), speed.max())
    ax.add_collection(lc)
    return lc


# ═════════════════════════════════════════════════════════════════════════════
#  FIGURE  SETUP
# ═════════════════════════════════════════════════════════════════════════════

traj = compute_trajectory(angle, velocity, gravity)

print()
print(f"  Max Range  : {traj['range']:.2f} m")
print(f"  Max Height : {traj['max_h']:.2f} m")
print(f"  Flight Time: {traj['t_total']:.2f} s")

fig = plt.figure(figsize=(12, 6.5), facecolor="#111827")
ax  = fig.add_axes([0.07, 0.18, 0.88, 0.74], facecolor="#111827")

for spine in ax.spines.values():
    spine.set_edgecolor("#374151")
ax.tick_params(colors="#9CA3AF", labelsize=9)
ax.xaxis.label.set_color("#9CA3AF")
ax.yaxis.label.set_color("#9CA3AF")
ax.grid(True, color="#1F2937", linewidth=0.8, zorder=0)

ax.set_xlabel("Horizontal distance (m)", fontsize=10)
ax.set_ylabel("Height (m)", fontsize=10)

# title lives in figure space so it never gets clipped
fig.text(0.5, 0.96,
         f"Projectile Motion  ·  θ={angle}°  ·  v₀={velocity} m/s  ·  g={gravity} m/s²",
         ha="center", va="top", color="#F9FAFB", fontsize=11, fontweight="bold")

# axes limits with some breathing room
ax.set_xlim(-traj["range"] * 0.02,  traj["range"] * 1.08)
ax.set_ylim(-traj["max_h"] * 0.05,  traj["max_h"] * 1.35)

# ── ghost path (faint dashed preview of full arc) ─────────────────────────
ax.plot(traj["x"], traj["y"],
        color="white", lw=0.8, alpha=0.08, linestyle="--", zorder=1)

# ── static markers: peak & landing ────────────────────────────────────────
peak_x = traj["range"] / 2
peak_y = traj["max_h"]

ax.plot(peak_x, peak_y, "o", color="#F59E0B", ms=7, zorder=5)
ax.annotate(f"peak  {peak_y:.1f} m",
            xy=(peak_x, peak_y), xytext=(peak_x + traj["range"]*0.03, peak_y + traj["max_h"]*0.06),
            color="#F59E0B", fontsize=8,
            arrowprops=dict(arrowstyle="-", color="#F59E0B", lw=0.8))

ax.plot(traj["range"], 0, "s", color="#10B981", ms=7, zorder=5)
ax.annotate(f"landing  {traj['range']:.1f} m",
            xy=(traj["range"], 0), xytext=(traj["range"] - traj["range"]*0.22, traj["max_h"]*0.12),
            color="#10B981", fontsize=8,
            arrowprops=dict(arrowstyle="-", color="#10B981", lw=0.8))

# ── animated objects ───────────────────────────────────────────────────────
# The speed-coloured trail uses a LineCollection that we update each frame.
# We seed it with a single invisible segment so it's in the axes from frame 0.
live_lc = build_speed_collection(
    ax,
    traj["x"][:1], traj["y"][:1],
    traj["speed"][:1],
    cmap="plasma", lw=2.5, alpha=0.9
)
live_lc.set_segments([])    # hide until animation starts

dot,     = ax.plot([], [], "o", color="white", ms=9, zorder=10,
                   markeredgecolor="#E5E7EB", markeredgewidth=1.2)
dot_glow,= ax.plot([], [], "o", color="white", ms=17, zorder=9,
                   alpha=0.15)          # soft bloom around the ball

# ── HUD text elements ──────────────────────────────────────────────────────
hud_speed = ax.text(0.02, 0.96, "", transform=ax.transAxes,
                    color="#E5E7EB", fontsize=9, va="top",
                    fontfamily="monospace", zorder=11)
hud_time  = ax.text(0.02, 0.90, "", transform=ax.transAxes,
                    color="#9CA3AF", fontsize=8, va="top",
                    fontfamily="monospace", zorder=11)

# progress bar across the bottom of the plot area
prog_bg = ax.axhline(-traj["max_h"]*0.04, color="#374151", lw=4,
                     xmin=0, xmax=1, zorder=2, clip_on=False)
prog_line, = ax.plot([], [], color="#6366F1", lw=4, zorder=3, clip_on=False)


# ── compare shots storage ──────────────────────────────────────────────────
ghost_shots = []   # list of finished trajectory dicts


# ═════════════════════════════════════════════════════════════════════════════
#  ANIMATION FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

def init():
    live_lc.set_segments([])
    dot.set_data([], [])
    dot_glow.set_data([], [])
    hud_speed.set_text("")
    hud_time.set_text("")
    prog_line.set_data([], [])
    return live_lc, dot, dot_glow, hud_speed, hud_time, prog_line


def update(frame_num):
    idx = traj["fidx"][frame_num]           # eased sample index
    idx = min(idx, len(traj["x"]) - 1)

    # ── update speed-coloured trail ──────────────────────────────────────
    xd = traj["x"][:idx + 1]
    yd = traj["y"][:idx + 1]
    sd = traj["speed"][:idx + 1]

    if len(xd) >= 2:
        segs = make_speed_segments(xd, yd)
        live_lc.set_segments(segs)
        live_lc.set_array(sd)
    else:
        live_lc.set_segments([])

    # ── ball position ─────────────────────────────────────────────────────
    cx, cy = traj["x"][idx], traj["y"][idx]
    dot.set_data([cx], [cy])
    dot_glow.set_data([cx], [cy])

    # ── HUD ──────────────────────────────────────────────────────────────
    spd = traj["speed"][idx]
    t   = traj["t"][idx]
    hud_speed.set_text(f"speed  {spd:6.1f} m/s")
    hud_time.set_text( f"time   {t:6.2f} s")

    # ── progress bar ──────────────────────────────────────────────────────
    frac = idx / max(len(traj["x"]) - 1, 1)
    prog_line.set_data(
        [ax.get_xlim()[0],
         ax.get_xlim()[0] + frac * (ax.get_xlim()[1] - ax.get_xlim()[0])],
        [-traj["max_h"] * 0.04, -traj["max_h"] * 0.04]
    )

    return live_lc, dot, dot_glow, hud_speed, hud_time, prog_line


# ═════════════════════════════════════════════════════════════════════════════
#  BUTTONS  (Replay  &  + Compare)
# ═════════════════════════════════════════════════════════════════════════════

BTN_STYLE = dict(color="#1F2937", hovercolor="#374151")

ax_btn_replay  = fig.add_axes([0.07,  0.04, 0.12, 0.07])
ax_btn_compare = fig.add_axes([0.21,  0.04, 0.14, 0.07])

btn_replay  = Button(ax_btn_replay,  "↺  Replay",  **BTN_STYLE)
btn_compare = Button(ax_btn_compare, "+  Compare", **BTN_STYLE)

for b in (btn_replay, btn_compare):
    b.label.set_color("#E5E7EB")
    b.label.set_fontsize(9)

# hold a reference so it isn't garbage-collected
ani_holder = [None]

def start_animation():
    if ani_holder[0] is not None:
        ani_holder[0].event_source.stop()
    ani_holder[0] = animation.FuncAnimation(
        fig, update,
        frames=len(traj["fidx"]),
        init_func=init,
        interval=20,
        blit=True,
        repeat=False
    )
    fig.canvas.draw_idle()


def on_replay(event):
    start_animation()


def on_compare(event):
    # freeze current shot as a ghost
    color = SHOT_COLORS[len(ghost_shots) % len(SHOT_COLORS)]
    ax.plot(traj["x"], traj["y"],
            color=color, lw=1.5, alpha=0.55, linestyle="--", zorder=2,
            label=f"θ={angle}° v={velocity}")
    ax.plot(traj["x"][-1], 0, "s", color=color, ms=5, zorder=4)
    ghost_shots.append(traj)
    ax.legend(fontsize=7, facecolor="#1F2937", edgecolor="#374151",
              labelcolor="#D1D5DB", loc="upper right")
    fig.canvas.draw_idle()


btn_replay.on_clicked(on_replay)
btn_compare.on_clicked(on_compare)

# ═════════════════════════════════════════════════════════════════════════════
#  COLOURBAR  (speed legend)
# ═════════════════════════════════════════════════════════════════════════════
cbar_ax = fig.add_axes([0.96, 0.18, 0.015, 0.74])
sm = plt.cm.ScalarMappable(cmap="plasma",
                            norm=plt.Normalize(traj["speed"].min(),
                                               traj["speed"].max()))
sm.set_array([])
cb = fig.colorbar(sm, cax=cbar_ax)
cb.set_label("Speed (m/s)", color="#9CA3AF", fontsize=8, labelpad=8)
cb.ax.yaxis.set_tick_params(color="#6B7280", labelsize=7)
plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#9CA3AF")
cb.outline.set_edgecolor("#374151")

# ═════════════════════════════════════════════════════════════════════════════
#  LAUNCH
# ═════════════════════════════════════════════════════════════════════════════
start_animation()
plt.show()
print("done!")
