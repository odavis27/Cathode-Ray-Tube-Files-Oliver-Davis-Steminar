"""
Play video edge detection through matplotlib animation,

Runs same algo to convert to dots as is used in CRT code.

Tests graphics by seeing why they will look like (with the edges extracted 
and turned to dots and drawn) Before running on CRT so I can bugfix and
tell whether poor quality graphics are the fault of the CRT circuit or the
software simply converting the video into usable grpahics poorly.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

VIDEO_FILE = "act.mp4"  # Video file
FRAME_STRIDE = 2      # Process every Nth frame
DETAIL_LEVEL = 5      # Keep every Nth edge pixel (lower = more detail)
CANNY_LOW = 50        
CANNY_HIGH = 150      

# ═══════════════════════════════════════════════════════════════
# EDGE EXTRACTION
# ═══════════════════════════════════════════════════════════════

def extract_frame_edges(frame, detail_level=5):
    """Extract edge points from a frame and normalize to -1 to 1 range."""
    
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply Canny edge detection
    edges = cv2.Canny(gray, CANNY_LOW, CANNY_HIGH)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    height, width = frame.shape[:2]
    
    all_points = []
    
    for contour in contours:
        # Skip tiny contours
        if len(contour) < 5:
            continue
            
        # Subsample by detail level
        contour = contour[::detail_level]
        
        # Normalize coordinates to -1 to 1
        for point in contour:
            x, y = point[0]
            norm_x = (x / width) * 2.0 - 1.0
            norm_y = 1.0 - (y / height) * 2.0  # Flip Y axis
            all_points.append((norm_x, norm_y))
    
    return all_points


def load_video_frames(video_path, frame_stride=2, detail_level=5):
    """Load and process all video frames."""
    
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Video: {total_frames} frames @ {fps} FPS")
    print(f"Processing every {frame_stride} frame(s) with detail level {detail_level}")
    print()
    
    all_frames = []
    frame_idx = 0
    processed = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Only process frames according to stride
        if frame_idx % frame_stride == 0:
            points = extract_frame_edges(frame, detail_level)
            all_frames.append(points)
            processed += 1
            
            if processed % 50 == 0:
                print(f"Processed {processed} frames ({frame_idx}/{total_frames}) - "
                      f"Last frame: {len(points)} points")
        
        frame_idx += 1
    
    cap.release()
    
    print(f"\nDone! Processed {processed} frames")
    print(f"Average points per frame: {sum(len(f) for f in all_frames) / len(all_frames):.0f}")
    
    playback_fps = fps / frame_stride
    
    return all_frames, playback_fps

# ═══════════════════════════════════════════════════════════════
# ANIMATION
# ═══════════════════════════════════════════════════════════════

video_path = Path(VIDEO_FILE)

if not video_path.exists():
    print(f"ERROR: Video file not found: {video_path}")
    exit(1)

print("=" * 60)
print("LOADING VIDEO...")
print("=" * 60)
print()

frames, fps = load_video_frames(video_path, FRAME_STRIDE, DETAIL_LEVEL)

print()
print("=" * 60)
print("STARTING PLAYBACK")
print("=" * 60)
print(f"FPS: {fps:.1f}")
print(f"Total frames: {len(frames)}")
print()

# Set up the plot
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
ax.set_aspect('equal')
ax.set_facecolor('white')
ax.grid(False)
ax.set_xticks([])
ax.set_yticks([])

# Initialize scatter plot
scatter = ax.scatter([], [], s=1, c='black')

frame_text = ax.text(0.02, 0.98, '', transform=ax.transAxes, 
                     verticalalignment='top', fontsize=10)

def init():
    """Initialize animation."""
    scatter.set_offsets(np.empty((0, 2)))
    frame_text.set_text('')
    return scatter, frame_text

def update(frame_idx):
    """Update function for animation."""
    points = frames[frame_idx]
    print(len(points))

    if points:
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        scatter.set_offsets(np.c_[x_coords, y_coords])
    else:
        scatter.set_offsets(np.empty((0, 2)))
    
    frame_text.set_text(f'Frame {frame_idx}/{len(frames)} | Points: {len(points)}')
    
    return scatter, frame_text

# Create animation
interval = 1000 / fps  # milliseconds per frame

anim = FuncAnimation(fig, update, frames=len(frames), 
                    init_func=init, blit=True, 
                    interval=interval, repeat=True)

plt.tight_layout()
plt.show()

print("Playback finished!")