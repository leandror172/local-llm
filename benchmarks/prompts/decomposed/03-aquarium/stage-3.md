Here is a working HTML file showing an aquarium with background and swimming fish:

```html
{{PREVIOUS_OUTPUT}}
```

Now add bubbles and seaweed. Do NOT rewrite from scratch — modify the file above.

Requirements for bubbles:
- Maintain an array of active bubbles (start empty)
- Each frame, 2% chance to spawn a new bubble at a random x position at the bottom of the water area
- Each bubble has: x, y, radius (start 2-4px), rise speed (20-40 px/s)
- Each frame: y -= riseSpeed * dt, radius += 0.01 (slight growth)
- Draw each bubble as a translucent circle (strokeStyle with alpha 0.5)
- When a bubble's y < 0, remove it from the array
- Maximum 30 active bubbles at once

Requirements for seaweed:
- 5-7 seaweed plants at fixed x positions along the sandy bottom, initialized once
- Each plant is drawn as a series of connected quadratic curves going upward
- Sway animation: offset each control point by sin(time * speed + segmentIndex) * amplitude
- Each plant: 4-6 segments, height 60-120px, green color with slight variation
- Draw seaweed code:
  ```
  for each plant:
    ctx.beginPath()
    ctx.moveTo(plant.x, sandTop)
    for each segment (0 to plant.segments):
      // Each segment goes up by segmentHeight
      targetY = sandTop - (segment+1) * segmentHeight
      // Sway offset increases with height
      swayX = sin(time/1000 * plant.swaySpeed + segment * 0.8) * (segment+1) * 5
      // Control point for the curve
      cpX = plant.x + swayX
      cpY = (targetY + previousY) / 2
      ctx.quadraticCurveTo(cpX, cpY, plant.x + swayX * 0.5, targetY)
    ctx.strokeStyle = plant.color
    ctx.lineWidth = 3
    ctx.stroke()
  ```
- Draw seaweed AFTER sand but BEFORE fish
