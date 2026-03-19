"""Generate daily signal snapshot images for SNS sharing."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .models import SignalOutput

W, H = 1200, 630
BG = "#0d1117"
ACCENT = "#58a6ff"
TEXT_BRIGHT = "#f0f6fc"
TEXT = "#c9d1d9"
TEXT_DIM = "#8b949e"
COLOR_LONG = "#3fb950"
COLOR_SHORT = "#f85149"
COLOR_NEUTRAL = "#6e7681"

# Try system monospace fonts
FONT_PATHS = [
    "/System/Library/Fonts/Menlo.ttc",  # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",  # Linux/Ubuntu
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",  # Linux alt
]


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def generate_snapshot(signal: SignalOutput, output_dir: Path) -> Path:
    """Generate a PNG snapshot image for a signal."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    font_title = _get_font(28)
    font_large = _get_font(36)
    font_med = _get_font(16)
    font_sm = _get_font(13)
    font_xs = _get_font(11)

    # Top accent bar
    draw.rectangle([0, 0, W, 3], fill=ACCENT)

    # Header
    pair_name = signal.market_pair_id.replace("us_", "US → ").title()
    draw.text((40, 20), "GLOBAL MARKET PROPAGATION", fill=TEXT_BRIGHT, font=font_title)
    draw.text((40, 55), f"{pair_name}  |  {signal.signal_date}", fill=TEXT_DIM, font=font_med)

    # Shock magnitude
    draw.text((40, 100), "US SHOCK INDEX", fill=ACCENT, font=font_xs)
    magnitude = signal.shock_magnitude
    mag_color = COLOR_SHORT if magnitude > 1.5 else ("#d29922" if magnitude > 0.8 else COLOR_LONG)
    sign = "+" if magnitude >= 0 else ""
    draw.text((40, 118), f"{sign}{magnitude:.4f}", fill=mag_color, font=font_large)

    # Factor scores
    draw.text((350, 100), "FACTOR SCORES", fill=ACCENT, font=font_xs)
    y = 120
    factor_labels = {"global": "Global", "country_spread": "Country Spread", "cyclical_defensive": "Cyclical/Defensive"}
    for key, value in signal.factor_scores.items():
        label = factor_labels.get(key, key)
        color = COLOR_LONG if value >= 0 else COLOR_SHORT
        sign = "+" if value >= 0 else ""
        draw.text((350, y), f"{label}", fill=TEXT_DIM, font=font_sm)
        draw.text((560, y), f"{sign}{value:.4f}", fill=color, font=font_sm)
        y += 22

    # Divider
    draw.rectangle([40, 195, W - 40, 196], fill="#30363d")

    # Sector signals - split into two columns
    draw.text((40, 210), "SECTOR SIGNALS", fill=ACCENT, font=font_xs)

    sectors = signal.sector_signals
    col_width = (W - 80) // 2
    y_start = 235

    for i, s in enumerate(sectors):
        col = 0 if i < (len(sectors) + 1) // 2 else 1
        row = i if col == 0 else i - (len(sectors) + 1) // 2
        x = 40 + col * col_width
        y = y_start + row * 26

        if y > H - 60:
            break

        # Position badge
        if s.position == "long":
            badge_color = COLOR_LONG
        elif s.position == "short":
            badge_color = COLOR_SHORT
        else:
            badge_color = COLOR_NEUTRAL

        # Rank
        draw.text((x, y), f"{s.rank:2d}", fill=TEXT_DIM, font=font_sm)

        # Signal bar
        bar_width = min(int(abs(s.signal_score) * 300), 120)
        bar_x = x + 30
        draw.rectangle([bar_x, y + 2, bar_x + bar_width, y + 16], fill=badge_color)

        # Name and score
        draw.text((bar_x + bar_width + 8, y), s.name, fill=TEXT, font=font_sm)
        sign = "+" if s.signal_score >= 0 else ""
        score_text = f"{sign}{s.signal_score:.4f}"
        # Right-align score
        score_x = x + col_width - 80
        draw.text((score_x, y), score_text, fill=badge_color, font=font_sm)

    # Footer
    draw.rectangle([0, H - 35, W, H], fill="#161b22")
    draw.text((40, H - 28), "leadlag.dev", fill=ACCENT, font=font_sm)
    draw.text((160, H - 28), "Daily signals based on subspace-regularized PCA", fill=TEXT_DIM, font=font_xs)

    # Save
    pair_dir = output_dir / signal.market_pair_id
    pair_dir.mkdir(parents=True, exist_ok=True)
    out_path = pair_dir / "snapshot.png"
    img.save(out_path, "PNG")

    return out_path
