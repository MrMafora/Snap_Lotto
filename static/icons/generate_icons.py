#!/usr/bin/env python3
"""
Generate PWA icons for Snap Lotto app
Creates icons in multiple sizes for mobile shortcuts and PWA installation
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_snap_lotto_icon(size):
    """Create a Snap Lotto icon with the specified size"""
    # Create image with white background
    img = Image.new('RGB', (size, size), '#ffffff')
    draw = ImageDraw.Draw(img)
    
    # Draw green circular background
    margin = size // 10
    circle_size = size - (2 * margin)
    draw.ellipse([margin, margin, margin + circle_size, margin + circle_size], 
                 fill='#1a472a', outline='#0f2c18', width=max(1, size//50))
    
    # Calculate text size and position
    font_size = size // 8
    try:
        # Try to use a system font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("Arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
    
    # Draw "SL" text in center
    text = "SL"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - font_size // 4
    
    # Draw white text with shadow
    shadow_offset = max(1, size // 100)
    draw.text((x + shadow_offset, y + shadow_offset), text, fill='#cccccc', font=font)
    draw.text((x, y), text, fill='#ffffff', font=font)
    
    # Draw small lottery ball icons
    ball_radius = size // 20
    if ball_radius >= 3:
        # Draw 3 small balls at bottom
        ball_y = size - margin - ball_radius - (size // 30)
        for i, ball_x in enumerate([size//3, size//2, 2*size//3]):
            draw.ellipse([ball_x - ball_radius, ball_y - ball_radius, 
                         ball_x + ball_radius, ball_y + ball_radius], 
                        fill='#ffd700', outline='#ccaa00', width=1)
    
    return img

def generate_all_icons():
    """Generate all required PWA icon sizes"""
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    for size in sizes:
        print(f"Generating {size}x{size} icon...")
        icon = create_snap_lotto_icon(size)
        filename = f"icon-{size}x{size}.png"
        icon.save(filename, 'PNG', optimize=True)
        print(f"✅ Created {filename}")

if __name__ == "__main__":
    generate_all_icons()
    print("🎯 All PWA icons generated successfully!")