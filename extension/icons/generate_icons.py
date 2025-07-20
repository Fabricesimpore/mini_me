#!/usr/bin/env python3
"""
Generate icons for the Chrome extension
Creates simple brain emoji icons in different sizes
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Icon sizes required by Chrome
SIZES = [16, 32, 48, 128]

# Create icons directory if it doesn't exist
icon_dir = os.path.dirname(os.path.abspath(__file__))

def create_icon(size):
    """Create a simple icon with brain emoji"""
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a purple circle background
    margin = size // 8
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(99, 102, 241, 255)  # Purple color
    )
    
    # Add a simple "DT" text (Digital Twin)
    try:
        # Try to use a system font
        font_size = size // 3
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw the text
    text = "DT"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    # Save the icon
    filename = f"icon-{size}.png"
    filepath = os.path.join(icon_dir, filename)
    img.save(filepath, 'PNG')
    print(f"Created {filename}")

# Generate all icon sizes
for size in SIZES:
    create_icon(size)

print("\nAll icons generated successfully!")
print("You can now load the extension in Chrome:")
print("1. Open chrome://extensions/")
print("2. Enable 'Developer mode'")
print("3. Click 'Load unpacked'")
print("4. Select the 'extension' directory")