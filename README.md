# BlueDart Waybill Tracker

Automated waybill tracking on [bluedart.com](https://www.bluedart.com/) with OCR captcha solving, route visualization, and CSV export.

## Features

- **Auto captcha solving** — OCR with strikethrough removal (9 preprocessing combos)
- **Manual fallback** — type captcha yourself if OCR fails
- **Route map** — visual map showing shipment journey between cities
- **Timeline chart** — chronological tracking events with color-coded statuses
- **ASCII table** — formatted console output
- **CSV export** — results saved for further analysis
- **Screenshot capture** — full-page screenshots saved automatically

## Project Structure

```bash
bluedart-tracker/
├── main.py              # CLI entry point
├── src/
│   ├── __init__.py
│   ├── browser.py       # Browser/driver setup (Brave, Chrome, Chromium)
│   ├── captcha.py       # OCR captcha solving with line removal
│   ├── tracker.py       # Page interaction, extraction, processing
│   └── visualizer.py    # Route map + timeline chart generation
├── output/
│   ├── results.csv      # Tracking data
│   ├── screenshots/     # Browser screenshots
│   └── visuals/         # Route maps + timeline charts
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

Also install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (for captcha solving).

## Usage

```bash
# Single waybill
python main.py -w 79034111122

# Multiple waybills
python main.py -w 79034111122,79034111041

# From file
python main.py -f waybills.txt

# Interactive mode
python main.py -i

# Manual captcha only
python main.py -w 79034111122 --no-auto-captcha
```

## Output

Results are saved to the `output/` directory:

| File | Description |
| ------ | ------------- |
| `output/results.csv` | Tracking data in CSV format |
| `output/screenshots/` | Browser screenshots of results |
| `output/visuals/route_*.png` | Shipment route map |
| `output/visuals/timeline_*.png` | Tracking timeline chart |

## Dependencies

- Python 3.8+
- Chrome, Brave, or Chromium browser
- Tesseract OCR (for auto captcha solving)
