import matplotlib
matplotlib.use('MacOSX')

import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.collections import LineCollection
from matplotlib.widgets import Button

COLORS = [
    "#4C9BE8", "#E8604C", "#4CE8A0", "#E8D44C",
    "#C44CE8", "#E8974C", "#4CE8E8", "#E84C9B",
]

# ═════════════════════════════════════════════════════════════════════════════
#  PHYSICS
# ═════════════════════════════════════════════════════════════════════════════

def compute_trajectory(angle_deg, vel, grav, dt=0.03):
    rad       = math.radians(angle_deg)
    vx        = vel * math.cos(rad)
    vy        = vel * math.sin(rad)
    t_end     = (2 * vy) / grav

    t_arr     = np.arange(0, t_end + dt, dt)
    x_arr     = vx * t_arr
    y_arr     = np.maximum(0.0, vy * t_arr - 0.5 * grav * t_arr**2)
    vy_arr    = vy - grav * t_arr
    speed_arr = np.hypot(vx, vy_arr)

    weights   = 1.0 / np.maximum(speed_arr, 0.5)
    weights  /= weights.sum()
    cumw      = np.cumsum(weights)
    n_frames  = max(80, len(t_arr) * 2)
    fidx      = np.searchsorted(cumw, np.linspace(0, 1, n_frames))
    fidx      = fidx.clip(0, len(t_arr) - 1)

    peak_idx  = int(np.argmax(y_arr))

    return {
        "x":       x_arr,
        "y":       y_arr,
        "t":       t_arr,
        "speed":   speed_arr,
        "fidx":    fidx,
        "range":   float(x_arr[-1]),
        "max_h":   float(y_arr.max()),
        "t_total": float(t_end),
        "vx":      vx,
        "vy":      vy,
        "grav":    grav,
        "peak_x":  float(x_arr[peak_idx]),
        "peak_y":  float(y_arr[peak_idx]),
        "angle":   angle_deg,
        "vel":     vel,
    }


def make_segments(x, y):
    pts = np.array([x, y]).T.reshape(-1, 1, 2)
    return np.concatenate([pts[:-1], pts[1:]], axis=1)


# ═════════════════════════════════════════════════════════════════════════════
#  INPUT
# ═════════════════════════════════════════════════════════════════════════════

print("╔══════════════════════════════════════════╗")
print("║   Projectile Motion — Multi-Trajectory  ║")
print("╚══════════════════════════════════════════╝")
print("Enter each shot. Leave angle blank when done.\n")

shots = []
while True:
    idx   = len(shots) + 1
    raw_a = input(f"  Shot {idx}  angle     (°)             : ").strip()
    if not raw_a:
        break
    raw_v = input(f"  Shot {idx}  velocity  (m/s)           : ").strip()
    raw_g = input(f"  Shot {idx}  gravity   (m/s², def 9.8) : ").strip()

    angle   = float(raw_a)
    vel     = float(raw_v)
    gravity = float(raw_g) if raw_g else 9.8

    traj          = compute_trajectory(angle, vel, gravity)
    traj["color"] = COLORS[(idx - 1) % len(COLORS)]
    shots.append(traj)
    print(f"         range={traj['range']:.1f}m  height={traj['max_h']:.1f}m  time={traj['t_total']:.2f}s\n")

if not shots:
    print("No shots entered. Exiting.")
    exit()

global_range = max(s["range"] for s in shots)
global_maxH  = max(s["max_h"] for s in shots)
n_frames     = max(len(s["fidx"]) for s in shots)

# ═════════════════════════════════════════════════════════════════════════════
#  FIGURE
# ═════════════════════════════════════════════════════════════════════════════

fig = plt.figure(figsize=(14, 7.5), facecolor="#0D1117")

ax = fig.add_axes([0.06, 0.18, 0.64, 0.73], facecolor="#0D1117")

for sp in ax.spines.values():
    sp.set_edgecolor("#30363D")
ax.tick_params(colors="#8B949E", labelsize=8)
ax.xaxis.label.set_color("#8B949E")
ax.yaxis.label.set_color("#8B949E")
ax.grid(True, color="#161B22", linewidth=0.9, zorder=0)
ax.set_xlabel("Horizontal distance (m)", fontsize=9, labelpad=6)
ax.set_ylabel("Height (m)", fontsize=9, labelpad=6)
ax.set_xlim(-global_range * 0.02, global_range * 1.08)
ax.set_ylim(-global_maxH  * 0.05, global_maxH  * 1.35)

fig.text(0.06, 0.95,
         f"Projectile Motion  ·  {len(shots)} trajectories",
         color="#F0F6FC", fontsize=12, fontweight="bold", va="top")

# ghost paths
for s in shots:
    ax.plot(s["x"], s["y"],
            color=s["color"], lw=0.7, alpha=0.12,
            linestyle="--", zorder=1)

# peak + landing markers
for s in shots:
    ax.plot(s["peak_x"], s["peak_y"], "^",
            color=s["color"], ms=5, alpha=0.6, zorder=4)
    ax.plot(s["range"], 0, "s",
            color=s["color"], ms=5, alpha=0.6, zorder=4)
    ax.vlines(s["peak_x"], 0, s["peak_y"],
              color=s["color"], lw=0.5, alpha=0.2, linestyle=":", zorder=1)

# animated line collections
live_lcs = []
for s in shots:
    lc = LineCollection([], cmap="plasma", linewidth=2.2,
                        alpha=0.92, capstyle="round", zorder=5)
    lc.set_clim(s["speed"].min(), s["speed"].max())
    ax.add_collection(lc)
    live_lcs.append(lc)

# animated balls
dots  = []
glows = []
for s in shots:
    glow, = ax.plot([], [], "o", color=s["color"], ms=16, alpha=0.15, zorder=6)
    dot,  = ax.plot([], [], "o", color=s["color"], ms=8,  alpha=1.0,  zorder=7,
                    markeredgecolor="#F0F6FC", markeredgewidth=0.8)
    dots.append(dot)
    glows.append(glow)

# HUD per shot
hud_texts = []
for i, s in enumerate(shots):
    txt = ax.text(0.02, 0.97 - i * 0.055, "",
                  transform=ax.transAxes,
                  color=s["color"], fontsize=8, va="top",
                  fontfamily="monospace", zorder=10)
    hud_texts.append(txt)

# progress bar
prog_y = -global_maxH * 0.038
ax.axhline(prog_y, color="#30363D", lw=4, zorder=2, clip_on=False)
prog_line, = ax.plot([], [], color="#6366F1", lw=4, zorder=3, clip_on=False)

# legend
handles = [
    plt.Line2D([0], [0], color=s["color"], lw=2,
               label=f"#{i+1}  θ={s['angle']}°  v={s['vel']}  g={s['grav']}")
    for i, s in enumerate(shots)
]
ax.legend(handles=handles, fontsize=7.5,
          facecolor="#161B22", edgecolor="#30363D",
          labelcolor="#C9D1D9", loc="upper right",
          framealpha=0.9, borderpad=0.8)

# ═════════════════════════════════════════════════════════════════════════════
#  STATS TABLE
# ═════════════════════════════════════════════════════════════════════════════

ax_tbl = fig.add_axes([0.74, 0.18, 0.25, 0.73])
ax_tbl.set_facecolor("#161B22")
ax_tbl.axis("off")

COL_LABELS = ["#", "Angle", "Vel", "Range", "Height", "Time"]
COL_X      = [0.00, 0.10, 0.26, 0.40, 0.60, 0.80]
COL_W      = [0.10, 0.16, 0.14, 0.20, 0.20, 0.20]

def draw_table():
    ax_tbl.cla()
    ax_tbl.set_facecolor("#161B22")
    ax_tbl.axis("off")

    for label, cx, cw in zip(COL_LABELS, COL_X, COL_W):
        ax_tbl.text(cx + cw / 2, 0.97, label,
                    transform=ax_tbl.transAxes,
                    color="#8B949E", fontsize=7.5, fontweight="bold",
                    ha="center", va="top", fontfamily="monospace")

    ax_tbl.plot([0, 1], [0.935, 0.935],
                color="#30363D", lw=0.7,
                transform=ax_tbl.transAxes)

    row_h = 0.78 / max(len(shots), 1)

    for i, s in enumerate(shots):
        y = 0.92 - (i + 1) * row_h
        row_vals = [
            f"#{i+1}",
            f"{s['angle']}°",
            f"{s['vel']}",
            f"{s['range']:.1f}m",
            f"{s['max_h']:.1f}m",
            f"{s['t_total']:.2f}s",
        ]
        ax_tbl.add_patch(plt.Rectangle(
            (0, y - 0.01), 1, row_h * 0.92,
            transform=ax_tbl.transAxes,
            color=s["color"] + "18", zorder=0,
        ))
        for j, (val, cx, cw) in enumerate(zip(row_vals, COL_X, COL_W)):
            ax_tbl.text(cx + cw / 2, y + row_h * 0.35, val,
                        transform=ax_tbl.transAxes,
                        color=s["color"] if j == 0 else "#C9D1D9",
                        fontsize=7.5, ha="center", va="center",
                        fontfamily="monospace")

    if len(shots) > 1:
        ri = max(range(len(shots)), key=lambda i: shots[i]["range"])
        hi = max(range(len(shots)), key=lambda i: shots[i]["max_h"])
        ti = max(range(len(shots)), key=lambda i: shots[i]["t_total"])

        ax_tbl.plot([0, 1], [0.13, 0.13],
                    color="#30363D", lw=0.7,
                    transform=ax_tbl.transAxes)
        ax_tbl.text(0.5, 0.11,
                    f"Furthest → #{ri+1}  {shots[ri]['range']:.1f}m",
                    transform=ax_tbl.transAxes,
                    color=shots[ri]["color"], fontsize=7.5,
                    ha="center", fontfamily="monospace")
        ax_tbl.text(0.5, 0.07,
                    f"Highest  → #{hi+1}  {shots[hi]['max_h']:.1f}m",
                    transform=ax_tbl.transAxes,
                    color=shots[hi]["color"], fontsize=7.5,
                    ha="center", fontfamily="monospace")
        ax_tbl.text(0.5, 0.03,
                    f"Airborne → #{ti+1}  {shots[ti]['t_total']:.2f}s",
                    transform=ax_tbl.transAxes,
                    color=shots[ti]["color"], fontsize=7.5,
                    ha="center", fontfamily="monospace")

    fig.canvas.draw_idle()

draw_table()

# ═════════════════════════════════════════════════════════════════════════════
#  ANIMATION
# ═════════════════════════════════════════════════════════════════════════════

all_artists = live_lcs + dots + glows + hud_texts + [prog_line]

def init():
    for lc in live_lcs:
        lc.set_segments([])
    for dot in dots:
        dot.set_data([], [])
    for glow in glows:
        glow.set_data([], [])
    for txt in hud_texts:
        txt.set_text("")
    prog_line.set_data([], [])
    return all_artists


def update(frame_num):
    global_frac = frame_num / max(n_frames - 1, 1)

    for i, (s, lc, dot, glow, txt) in enumerate(
            zip(shots, live_lcs, dots, glows, hud_texts)):
        fi  = min(frame_num, len(s["fidx"]) - 1)
        idx = int(s["fidx"][fi])
        idx = min(idx, len(s["x"]) - 1)

        xd = s["x"][:idx + 1]
        yd = s["y"][:idx + 1]
        sd = s["speed"][:idx + 1]

        if len(xd) >= 2:
            lc.set_segments(make_segments(xd, yd))
            lc.set_array(sd)
        else:
            lc.set_segments([])

        cx, cy = float(s["x"][idx]), float(s["y"][idx])
        dot.set_data([cx], [cy])
        glow.set_data([cx], [cy])

        spd = float(s["speed"][idx])
        t   = float(s["t"][idx])
        txt.set_text(f"#{i+1}  {spd:5.1f} m/s  t={t:.2f}s")

    xl = ax.get_xlim()
    prog_line.set_data(
        [xl[0], xl[0] + global_frac * (xl[1] - xl[0])],
        [prog_y, prog_y]
    )
    return all_artists


ani_holder = [None]

def start_animation(loop=False):
    if ani_holder[0] is not None:
        ani_holder[0].event_source.stop()
    ani_holder[0] = animation.FuncAnimation(
        fig, update,
        frames=n_frames,
        init_func=init,
        interval=18,
        blit=True,
        repeat=loop,
    )
    fig.canvas.draw_idle()

# ═════════════════════════════════════════════════════════════════════════════
#  BUTTONS
# ═════════════════════════════════════════════════════════════════════════════

BTN = dict(color="#161B22", hovercolor="#21262D")
ax_replay = fig.add_axes([0.06, 0.05, 0.10, 0.07])
ax_loop   = fig.add_axes([0.18, 0.05, 0.10, 0.07])
btn_replay = Button(ax_replay, "↺  Replay", **BTN)
btn_loop   = Button(ax_loop,   "⟳  Loop",   **BTN)

for b in (btn_replay, btn_loop):
    b.label.set_color("#C9D1D9")
    b.label.set_fontsize(8.5)

btn_replay.on_clicked(lambda e: start_animation(loop=False))
btn_loop.on_clicked(lambda e: start_animation(loop=True))

# ═════════════════════════════════════════════════════════════════════════════
#  LAUNCH
# ═════════════════════════════════════════════════════════════════════════════

print("\nOpening animation window…  (close it to exit)\n")
start_animation()
plt.show()
print("done!")