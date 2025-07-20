#!/bin/bash

# Create simple SVG icons and convert to PNG using base64
# This creates placeholder icons for the Chrome extension

# Function to create SVG
create_svg() {
    local size=$1
    cat > "icon-${size}.svg" << EOF
<svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
  <rect width="${size}" height="${size}" rx="4" fill="#6366f1"/>
  <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" 
        fill="white" font-family="Arial, sans-serif" font-size="$((size/3))px" font-weight="bold">
    DT
  </text>
</svg>
EOF
}

# Create SVG files
for size in 16 32 48 128; do
    create_svg $size
    echo "Created icon-${size}.svg"
done

echo ""
echo "SVG icons created!"
echo "Note: For production, convert these to PNG format."
echo ""
echo "To use the extension:"
echo "1. Open chrome://extensions/"
echo "2. Enable 'Developer mode'"
echo "3. Click 'Load unpacked'"
echo "4. Select the 'extension' directory"