---
id: ex-02-canvas-gradient-bg
category: visual
type: few-shot-example
demonstrates: minimal static render, no CDN, self-contained HTML
---

## Task

Gradient background with centered text on canvas.

## Input

Create a single HTML file that draws a vertical gradient from dark blue to black on a 600x400 canvas, with the text "Hello Canvas" centered in white.

## Output

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Gradient Background</title>
    <style>
        body { margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background: #000; }
    </style>
</head>
<body>
<canvas id="c" width="600" height="400"></canvas>
<script>
    const canvas = document.getElementById('c');
    const ctx = canvas.getContext('2d');

    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, '#003');
    gradient.addColorStop(1, '#000');

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#fff';
    ctx.font = '36px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Hello Canvas', canvas.width / 2, canvas.height / 2);
</script>
</body>
</html>
```
