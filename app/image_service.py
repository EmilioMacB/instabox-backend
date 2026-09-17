import io
from PIL import Image, ImageDraw, ImageFont


def resize_original_image(image_bytes: bytes) -> bytes:
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        resized_img = img.resize((128, 128), Image.Resampling.LANCZOS)

        output = io.BytesIO()
        resized_img.save(output, format="JPEG", quality=90)
        return output.getvalue()


def create_polaroid(image_bytes: bytes, message: str) -> bytes:
    photo_size = (128, 128)
    margin_side = 16
    margin_top = 16
    margin_bottom = 44

    canvas_width = photo_size[0] + (margin_side * 2)  # 160 px
    canvas_height = photo_size[1] + margin_top + margin_bottom  # 188 px

    # Lienzo blanco tipo Polaroid
    canvas = Image.new("RGB", (canvas_width, canvas_height), color=(255, 255, 255))

    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        resized_img = img.resize(photo_size, Image.Resampling.LANCZOS)
        canvas.paste(resized_img, (margin_side, margin_top))

    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    # Truncar texto si excede el ancho visual del marco
    display_text = message if len(message) <= 24 else message[:21] + "..."

    bbox = draw.textbbox((0, 0), display_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    text_x = (canvas_width - text_width) // 2
    text_y = margin_top + photo_size[1] + ((margin_bottom - text_height) // 2)

    draw.text((text_x, text_y), display_text, fill=(30, 30, 30), font=font)

    output = io.BytesIO()
    canvas.save(output, format="PNG")
    return output.getvalue()