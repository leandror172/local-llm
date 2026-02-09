---
id: 02-twenty-balls-heptagon
category: visual
models: my-creative-coder,my-creative-coder-q3
timeout: 300
description: 20 colored balls bouncing inside a spinning heptagon with physics
source: Reddit r/LocalLLaMA (adapted from Python/tkinter to HTML/Canvas)
---

Create a single HTML file with a Canvas-based 2D physics simulation showing 20 balls bouncing inside a spinning heptagon:
- A regular heptagon (7 sides) rotates clockwise, completing a full 360 degrees every 5 seconds
- 20 balls start from the center of the heptagon and drop
- All balls have the same radius and display their number (1 to 20)
- Ball colors in order: #f8b862, #f6ad49, #f39800, #f08300, #ec6d51, #ee7948, #ed6d3d, #ec6800, #ec6800, #ee7800, #eb6238, #ea5506, #ea5506, #eb6101, #e49e61, #e45e32, #e17b34, #dd7a56, #db8449, #d66a35
- Balls are affected by gravity (pulling downward) and friction (slight velocity reduction per frame)
- Balls collide with each other with elastic collisions that conserve momentum
- Balls bounce off the rotating heptagon walls realistically
- Balls rotate with friction — the numbers on each ball should visually indicate the ball's spin
- The bounce height from impacts should not exceed the heptagon radius but should be higher than the ball radius
- The heptagon should be large enough to contain all 20 balls comfortably
- The canvas should be at least 800x800 pixels
- Use requestAnimationFrame for smooth animation
- Implement all collision detection and physics math directly — no external libraries
