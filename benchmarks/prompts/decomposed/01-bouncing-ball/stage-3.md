Here is a working HTML file showing a ball bouncing inside a rotating square:

```html
{{PREVIOUS_OUTPUT}}
```

Now add a visible trail showing the ball's recent path. Do NOT rewrite the existing code from scratch — modify the file above.

Requirements:
- Store the ball's last 60 positions in an array
- Push the current position each frame, shift when array exceeds 60
- Draw the trail as a series of small circles or a polyline
- Trail should fade: oldest positions are nearly transparent, newest are opaque
- Trail color should contrast with the background (e.g., yellow or orange with alpha)
- The trail must rotate with the scene (it shows world-space positions, so it will naturally curve as the square rotates)
