Here is a working HTML file showing one ball bouncing inside a rotating heptagon:

```html
{{PREVIOUS_OUTPUT}}
```

Now replace the single ball with 20 balls. Do NOT rewrite from scratch — modify the file above.

Requirements:
- 20 balls, all radius 12px, start clustered near the heptagon center (random offset ±20px)
- Each ball displays its number (1-20) as centered text
- Ball colors in order: #f8b862, #f6ad49, #f39800, #f08300, #ec6d51, #ee7948, #ed6d3d, #ec6800, #ec6800, #ee7800, #eb6238, #ea5506, #ea5506, #eb6101, #e49e61, #e45e32, #e17b34, #dd7a56, #db8449, #d66a35
- Each ball has random initial velocity (±100 px/s in each axis)
- All balls use the same wall collision logic from the existing code
- Add ball-to-ball collision: for each pair, if distance < 2*radius, apply elastic collision:
  ```
  // Vector from ball1 to ball2:
  dx = b2.x - b1.x; dy = b2.y - b1.y
  dist = sqrt(dx*dx + dy*dy)
  if (dist < 2 * radius && dist > 0) {
    nx = dx/dist; ny = dy/dist
    // Relative velocity along collision normal:
    dvx = b1.vx - b2.vx; dvy = b1.vy - b2.vy
    dvn = dvx*nx + dvy*ny
    if (dvn > 0) {  // Only if approaching
      b1.vx -= dvn * nx; b1.vy -= dvn * ny
      b2.vx += dvn * nx; b2.vy += dvn * ny
      // Separate balls:
      overlap = 2*radius - dist
      b1.x -= overlap/2 * nx; b1.y -= overlap/2 * ny
      b2.x += overlap/2 * nx; b2.y += overlap/2 * ny
    }
  }
  ```
- Draw each ball as a colored circle with its number in black text, centered
