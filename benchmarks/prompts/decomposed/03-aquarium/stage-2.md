Here is a working HTML file showing an aquarium background with sand, pebbles, and light rays:

```html
{{PREVIOUS_OUTPUT}}
```

Now add fish. Do NOT rewrite from scratch — modify the file above.

Requirements:
- 8 fish, each stored as an object with: x, y, vx, size, color, direction (1 or -1)
- Initialize fish at random positions, random sizes (30-60px body length), random HSL colors, random speeds (30-80 px/s)
- Each fish is drawn procedurally (no images) as follows:
  ```
  // Fish body: an ellipse
  ctx.beginPath()
  ctx.ellipse(x, y, bodyLength/2, bodyLength/4, 0, 0, 2*Math.PI)
  ctx.fill()

  // Tail fin: a triangle behind the body
  // If facing right (direction=1): tail is to the left of the body
  tailX = x - direction * bodyLength/2
  ctx.beginPath()
  ctx.moveTo(tailX, y)
  ctx.lineTo(tailX - direction * bodyLength/3, y - bodyLength/4)
  ctx.lineTo(tailX - direction * bodyLength/3, y + bodyLength/4)
  ctx.closePath()
  ctx.fill()

  // Eye: small white circle with black pupil
  eyeX = x + direction * bodyLength/4
  ctx.beginPath()
  ctx.arc(eyeX, y - bodyLength/8, bodyLength/10, 0, 2*Math.PI)
  ctx.fillStyle = 'white'; ctx.fill()
  ctx.beginPath()
  ctx.arc(eyeX + direction*2, y - bodyLength/8, bodyLength/20, 0, 2*Math.PI)
  ctx.fillStyle = 'black'; ctx.fill()
  ```
- Fish swim horizontally: x += vx * direction * dt
- When a fish reaches a canvas edge (with 50px margin), smoothly reverse direction:
  set direction *= -1 (this flips the drawing and movement)
- Keep fish within the water area (above the sandy bottom)
- Draw fish AFTER the background but BEFORE any future overlay elements
