import matplotlib
matplotlib.use('TkAgg')

import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# -----------------------------
# Link lengths (mm)
# -----------------------------
L1, L2, L3 = 40, 30, 25

# -----------------------------
# Fingers
# -----------------------------
fingers = ["Little", "Ring", "Middle", "Index"]
spacing = 20

# Default angles
default_angles = {f: [0, 20, 15, 10] for f in fingers}
default_angles["Thumb"] = [0, 45, -25, -25]

angles = {k: v[:] for k, v in default_angles.items()}

# -----------------------------
# Joint Limits
# -----------------------------
finger_limits = [
    (-20, 20),   # θ1
    (-20, 90),     # θ2
    (0, 110),    # θ3
    (0, 120)      # θ4
]

thumb_limits = [
    (-25, 25),
    (-35, 90),
    (-60, 0),
    (-90, 0)
]

# -----------------------------
# FK
# -----------------------------
def compute_chain(theta1, theta2, theta3, theta4):
    t1, t2, t3, t4 = map(np.deg2rad, [theta1, theta2, theta3, theta4])

    pts = [(0, 0, 0)]

    R1 = L1*np.cos(t2)
    pts.append((L1*np.sin(t2), R1*np.sin(t1), R1*np.cos(t1)))

    R2 = L1*np.cos(t2) + L2*np.cos(t2+t3)
    pts.append((L1*np.sin(t2)+L2*np.sin(t2+t3),
                R2*np.sin(t1), R2*np.cos(t1)))

    R3 = (L1*np.cos(t2) +
          L2*np.cos(t2+t3) +
          L3*np.cos(t2+t3+t4))

    pts.append((L1*np.sin(t2)+L2*np.sin(t2+t3)+L3*np.sin(t2+t3+t4),
                R3*np.sin(t1), R3*np.cos(t1)))

    return np.array(pts)

# -----------------------------
# Thumb Transformation
# -----------------------------
def transform_thumb(points):
    theta_x = np.deg2rad(30)
    theta_z = np.deg2rad(90)

    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(theta_x), -np.sin(theta_x)],
        [0, np.sin(theta_x), np.cos(theta_x)]
    ])

    Rz = np.array([
        [np.cos(theta_z), -np.sin(theta_z), 0],
        [np.sin(theta_z),  np.cos(theta_z), 0],
        [0,                0,               1]
    ])

    R = Rz @ Rx
    rotated = points @ R.T

    translation = np.array([0, 5, -60])
    return rotated + translation

# -----------------------------
# Plot 
# -----------------------------
def update_plot(val=None):
    ax.cla()

    ax.set_xlim(-50, 100)
    ax.set_ylim(-70, 70)
    ax.set_zlim(-70, 100)

    # Palm
    palm_top = 30
    palm_bottom = 10
    height = 60

    Y = np.array([-palm_top, palm_top, palm_bottom - 5, -palm_bottom - 5, -palm_top])
    Z = np.array([0, 0, -height, -height, 0])
    X = np.zeros_like(Y)

    ax.plot(X, Y, Z)

    # Fingers
    for i, f in enumerate(fingers):
        chain = compute_chain(*angles[f])
        chain[:, 1] += (i - 1.5) * spacing
        ax.plot(chain[:, 0], chain[:, 1], chain[:, 2], marker='o')

    # Thumb
    thumb_chain = compute_chain(*angles["Thumb"])
    thumb_chain = transform_thumb(thumb_chain)

    ax.plot(thumb_chain[:, 0],
            thumb_chain[:, 1],
            thumb_chain[:, 2],
            marker='o')

    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title("Hand FK Simulator")

    ax.grid(True)
    ax.set_box_aspect([1,1,1])

    canvas.draw_idle()

# -----------------------------
# Slider callback
# -----------------------------
def make_callback(finger, idx):
    def callback(val):
        angles[finger][idx] = float(val)
        update_plot()
    return callback

# -----------------------------
# Reset function
# -----------------------------
def reset():
    for f in angles:
        for i in range(4):
            sliders[(f, i)].set(default_angles[f][i])
    update_plot()

# -----------------------------
# UI
# -----------------------------
root = tk.Tk()
root.title("Hand FK Simulator")

# Plot
fig = plt.figure(figsize=(6,6))
ax = fig.add_subplot(111, projection='3d')

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Controls
control_frame = tk.Frame(root)
control_frame.pack(side=tk.RIGHT, fill=tk.Y)

sliders = {}

all_fingers = fingers + ["Thumb"]

for f in all_fingers:
    frame = tk.LabelFrame(control_frame, text=f)
    frame.pack(padx=5, pady=5, fill="x")

    slider_row = tk.Frame(frame)
    slider_row.pack()

    labels = ["θ1", "θ2", "θ3", "θ4"]

    limits = thumb_limits if f == "Thumb" else finger_limits

    for i in range(4):
        min_val, max_val = limits[i]

        s = tk.Scale(slider_row,
                     from_=min_val,
                     to=max_val,
                     resolution=1,
                     orient=tk.HORIZONTAL,
                     label=labels[i],
                     command=make_callback(f, i),
                     length=120)
        s.set(angles[f][i])
        s.pack(side=tk.LEFT)

        sliders[(f, i)] = s

# Reset button
reset_btn = tk.Button(control_frame, text="Reset", command=reset)
reset_btn.pack(pady=10, fill="x")

# Initial plot
update_plot()

root.mainloop()