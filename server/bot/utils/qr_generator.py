"""
Dem1chVPN — QR Code Generator
Generates QR codes for VLESS connection URLs.
"""
import io
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from PIL import Image, ImageDraw, ImageFont


def generate_qr_code(data: str, box_size: int = 10, border: int = 2) -> bytes:
    """
    Generate a styled QR code image.
    Returns PNG bytes.
    """
    qr = qrcode.QRCode(
        version=None,  # Auto-detect
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Create styled QR image
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        fill_color="#1a1a2e",
        back_color="#ffffff",
    )

    # Add padding and branding
    img_pil = img.get_image()
    width, height = img_pil.size

    # Create canvas with extra space for text
    padding = 30
    text_height = 40
    canvas = Image.new(
        "RGB",
        (width + padding * 2, height + padding * 2 + text_height),
        "#ffffff",
    )
    canvas.paste(img_pil, (padding, padding))

    # Add branding text
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except (OSError, IOError):
        font = ImageFont.load_default()

    text = "🛡️ Dem1chVPN"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (canvas.width - text_width) // 2
    y = height + padding * 2 + 5
    draw.text((x, y), text, fill="#1a1a2e", font=font)

    # Convert to bytes
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer.getvalue()
