from PIL import Image

def img_to_ansi(img_path, width=40):
    img = Image.open(img_path)
    img = img.convert('RGB')
    
    # Calculate height based on aspect ratio and terminal character aspect ratio (usually ~1:2)
    # Since we use half blocks, one character is 2 vertical pixels.
    w, h = img.size
    aspect = h / float(w)
    height = int(width * aspect)
    
    img = img.resize((width, height), Image.LANCZOS)
    
    out = []
    # Half blocks require stepping by 2 vertically
    for y in range(0, height, 2):
        row = []
        for x in range(width):
            r1, g1, b1 = img.getpixel((x, y))
            # get bottom pixel if it exists, else use top pixel for both
            if y + 1 < height:
                r2, g2, b2 = img.getpixel((x, y+1))
            else:
                r2, g2, b2 = r1, g1, b1
                
            # Foreground (upper half block ▀), Background (lower half block)
            # "\033[38;2;R;G;Bm" for fg, "\033[48;2;R;G;Bm" for bg
            row.append(f"\\x1b[38;2;{r1};{g1};{b1}m\\x1b[48;2;{r2};{g2};{b2}m▀")
        row.append("\\x1b[0m")
        out.append("".join(row))
    return "\n".join(out)

print(img_to_ansi("/home/pujan/Downloads/WhatsApp Image 2026-09-13 at 5.17.58 AM.jpeg", width=30))
