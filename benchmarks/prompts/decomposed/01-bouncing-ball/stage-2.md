Here is a working HTML file showing a rotating square:

```html
{{PREVIOUS_OUTPUT}}
```

Now add a ball that bounces off the interior walls of this rotating square. Do NOT rewrite the existing code from scratch — modify the file above.

Requirements:
- Ball radius 10px, drawn as a filled red circle
- Ball starts at the canvas center with velocity (200, 150) pixels/sec
- NO gravity (ball bounces forever at constant speed)
- Collision detection MUST work in the square's local (rotated) coordinate space:
  1. Transform ball position into local space (subtract center, rotate by -angle)
  2. Check if the ball (accounting for radius) exceeds the half-size boundary in local X or local Y
  3. Reflect the velocity component in LOCAL space (not world space)
  4. Transform the corrected position and velocity back to world space
- The ball must never escape the square
- Use delta-time for ball movement (consistent with the rotation)
