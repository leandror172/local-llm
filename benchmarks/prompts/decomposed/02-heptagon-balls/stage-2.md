Here is a working HTML file showing a rotating heptagon:

```html
{{PREVIOUS_OUTPUT}}
```

Now add ONE ball that falls under gravity and bounces off the heptagon walls. Do NOT rewrite from scratch — modify the file above.

Requirements:
- Ball radius 12px, filled circle, starts at the heptagon center
- Gravity: vy += 500 * dt each frame (pixels/sec²)
- Friction: multiply velocity by 0.999 each frame

Wall collision algorithm — follow these steps EXACTLY:

Step 1: Each frame, update position: x += vx*dt, y += vy*dt. Then apply gravity to vy.

Step 2: For each of the 7 heptagon edges (from vertex[i] to vertex[(i+1)%7]):
  Compute the edge normal (pointing inward toward center):
  ```
  edgeX = v2.x - v1.x
  edgeY = v2.y - v1.y
  // Inward normal (perpendicular, pointing toward center):
  normalX = -edgeY
  normalY = edgeX
  // Normalize:
  len = sqrt(normalX*normalX + normalY*normalY)
  normalX /= len
  normalY /= len
  ```

Step 3: Compute signed distance from ball center to the edge line:
  ```
  dist = (ball.x - v1.x) * normalX + (ball.y - v1.y) * normalY
  ```
  If dist < ball.radius, the ball has crossed this wall.

Step 4: On collision, push the ball back and reflect velocity:
  ```
  ball.x += normalX * (ball.radius - dist)
  ball.y += normalY * (ball.radius - dist)
  // Reflect velocity along the normal:
  dotVN = ball.vx * normalX + ball.vy * normalY
  ball.vx -= 2 * dotVN * normalX
  ball.vy -= 2 * dotVN * normalY
  // Apply restitution (energy loss):
  ball.vx *= 0.85
  ball.vy *= 0.85
  ```

Step 5: Draw the ball after all collision checks.

IMPORTANT: The heptagon vertices rotate each frame. Recompute vertices using the current angle before collision checks.
