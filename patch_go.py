from PIL import Image
import re

def img_to_ansi(img_path, width=44):
    img = Image.open(img_path)
    img = img.convert('RGB')
    
    w, h = img.size
    aspect = h / float(w)
    height = int(width * aspect)
    
    img = img.resize((width, height), Image.LANCZOS)
    
    out = [""] # initial newline
    for y in range(0, height, 2):
        row = []
        for x in range(width):
            r1, g1, b1 = img.getpixel((x, y))
            if y + 1 < height:
                r2, g2, b2 = img.getpixel((x, y+1))
            else:
                r2, g2, b2 = 0, 0, 0
                
            # Use actual ESC character (0x1B) so it works natively inside a Go raw string literal
            esc = chr(0x1B)
            row.append(f"{esc}[38;2;{r1};{g1};{b1}m{esc}[48;2;{r2};{g2};{b2}m▀")
        row.append(f"{esc}[0m")
        out.append("".join(row))
    out.append("")
    return "\n".join(out)

ansi_art = img_to_ansi("/home/pujan/Downloads/WhatsApp Image 2026-09-13 at 5.17.58 AM.jpeg")

with open("/home/pujan/berserker/main.go", "r") as f:
    code = f.read()

# Replace avatarAscii
# Find the block starting with avatarAscii = ` and ending with `
pattern = re.compile(r'avatarAscii = `.*?`', re.DOTALL)
new_code = pattern.sub(f'avatarAscii = `{ansi_art}`', code)

with open("/home/pujan/berserker/main.go", "w") as f:
    f.write(new_code)

print("Patched main.go with ANSI image!")
