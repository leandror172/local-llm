Here is a working HTML file showing a rotating square:

```html
{{PREVIOUS_OUTPUT}}
```

Now add a ball that bounces off the interior walls of this rotating square. Do NOT rewrite from scratch — modify the file above.

Requirements:
- Ball radius 10px, filled red circle
- Ball starts at (centerX, centerY) with velocity (200, 150) pixels/sec
- NO gravity
- Use delta-time for ball movement

Collision algorithm — follow these steps EXACTLY using these formulas:

Step 1: Store ball position and velocity in world space as persistent variables (outside the draw function).

Step 2: Each frame, update world position: `wx += vx * dt; wy += vy * dt;`

Step 3: Transform ball position from world to local (square's rotated frame):
```
localX = (wx - cx) * cos(-angle) - (wy - cy) * sin(-angle)
localY = (wx - cx) * sin(-angle) + (wy - cy) * cos(-angle)
```

Step 4: Transform velocity from world to local:
```
localVx = vx * cos(-angle) - vy * sin(-angle)
localVy = vx * sin(-angle) + vy * cos(-angle)
```

Step 5: Check collision against axis-aligned walls in local space (halfSize = squareSize/2):
```
if (localX + radius > halfSize)  { localX = halfSize - radius;  localVx = -localVx; }
if (localX - radius < -halfSize) { localX = -halfSize + radius; localVx = -localVx; }
if (localY + radius > halfSize)  { localY = halfSize - radius;  localVy = -localVy; }
if (localY - radius < -halfSize) { localY = -halfSize + radius; localVy = -localVy; }
```

Step 6: Transform corrected position and velocity BACK to world space:
```
wx = localX * cos(angle) - localY * sin(angle) + cx
wy = localX * sin(angle) + localY * cos(angle) + cy
vx = localVx * cos(angle) - localVy * sin(angle)
vy = localVx * sin(angle) + localVy * cos(angle)
```

Step 7: Draw the ball at (wx, wy).

This ensures collision detection, position clamping, AND velocity reflection all happen in local space before transforming back.
