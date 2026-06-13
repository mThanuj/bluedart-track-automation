import os
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUTPUT_DIR = "output/visuals"

CITY_COORDS = {
    "delhi": (28.6139, 77.2090),
    "new delhi": (28.6139, 77.2090),
    "delhi offsite hub": (28.6139, 77.2090),
    "safdarjung enclave": (28.5800, 77.2000),
    "hyderabad": (17.3850, 78.4867),
    "hyderabad hub": (17.3850, 78.4867),
    "mumbai": (19.0760, 72.8777),
    "mumbai hub": (19.0760, 72.8777),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "bangalore hub": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707),
    "chennai hub": (13.0827, 80.2707),
    "pune": (18.5204, 73.8567),
    "pune hub": (18.5204, 73.8567),
    "kolkata": (22.5726, 88.3639),
    "kolkata hub": (22.5726, 88.3639),
    "ahmedabad": (23.0225, 72.5714),
    "ahmedabad hub": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "jaipur hub": (26.9124, 75.7873),
    "chandigarh": (30.7333, 76.7794),
    "chandigarh hub": (30.7333, 76.7794),
    "lucknow": (26.8467, 80.9462),
    "lucknow hub": (26.8467, 80.9462),
    "gurgaon": (28.4595, 77.0266),
    "gurugram": (28.4595, 77.0266),
    "navi mumbai": (19.0330, 73.0297),
    "thane": (19.2183, 72.9781),
}

STATUS_COLORS = {
    "arrived": "#2196F3",
    "connected": "#4CAF50",
    "delay": "#FF9800",
    "delivered": "#9C27B0",
    "picked": "#00BCD4",
    "out for delivery": "#E91E63",
    "default": "#607D8B",
}


def _get_coords(name):
    n = name.lower().strip()
    if n in CITY_COORDS:
        return CITY_COORDS[n]
    for city, coords in CITY_COORDS.items():
        if city in n or n in city:
            return coords
    return None


def _status_color(details):
    d = details.lower()
    for key, color in STATUS_COLORS.items():
        if key in d:
            return color
    return STATUS_COLORS["default"]


def _parse_events(results):
    events = []
    for item in results:
        if item.get("type") == "row":
            data = item.get("data", [])
            events.append(
                {
                    "location": data[0] if len(data) > 0 else "",
                    "details": data[1] if len(data) > 1 else "",
                    "date": data[2] if len(data) > 2 else "",
                    "time": data[3] if len(data) > 3 else "",
                }
            )
    return events


def _create_route_map(events, waybill):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    locations = []
    for e in reversed(events):
        loc = e["location"]
        if loc and (not locations or locations[-1] != loc):
            locations.append(loc)

    coords, labels = [], []
    for loc in locations:
        c = _get_coords(loc)
        if c:
            coords.append(c)
            labels.append(loc)

    if len(coords) < 2:
        return None

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]

    for i in range(len(coords) - 1):
        ax.plot(
            [lons[i], lons[i + 1]],
            [lats[i], lats[i + 1]],
            color="#e94560",
            linewidth=2.5,
            alpha=0.8,
            zorder=2,
        )
        ax.annotate(
            "",
            xy=(lons[i + 1], lats[i + 1]),
            xytext=(lons[i], lats[i]),
            arrowprops=dict(
                arrowstyle="->", color="#e94560", lw=2, connectionstyle="arc3,rad=0.1"
            ),
        )

    for i, (lat, lon) in enumerate(zip(lats, lons)):
        if i == 0:
            color, size, marker = "#4CAF50", 120, "^"
        elif i == len(lons) - 1:
            color, size, marker = "#F44336", 120, "s"
        else:
            color, size, marker = "#2196F3", 80, "o"

        ax.scatter(
            lon,
            lat,
            c=color,
            s=size,
            marker=marker,
            zorder=5,
            edgecolors="white",
            linewidth=1.5,
        )
        oy = 10 + (0.3 * 20 if i % 2 == 0 else -0.5 * 20)
        ax.annotate(
            f"{i+1}. {labels[i]}",
            (lon, lat),
            textcoords="offset points",
            xytext=(10, oy),
            fontsize=10,
            color="white",
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.7),
            zorder=6,
        )

    ax.set_title(
        f"Shipment Route -- Waybill: {waybill}",
        fontsize=16,
        color="white",
        fontweight="bold",
        pad=20,
    )

    lat_m = (max(lats) - min(lats)) * 0.3 or 2
    lon_m = (max(lons) - min(lons)) * 0.3 or 2
    ax.set_xlim(min(lons) - lon_m, max(lons) + lon_m)
    ax.set_ylim(min(lats) - lat_m, max(lats) + lat_m)
    ax.set_xlabel("Longitude", color="#aaa", fontsize=10)
    ax.set_ylabel("Latitude", color="#aaa", fontsize=10)
    ax.tick_params(colors="#aaa")
    ax.grid(True, alpha=0.15, color="#444")

    ax.legend(
        handles=[
            mpatches.Patch(facecolor="#4CAF50", label="Origin"),
            mpatches.Patch(facecolor="#2196F3", label="Hub/Transit"),
            mpatches.Patch(facecolor="#F44336", label="Destination"),
            plt.Line2D([0], [0], color="#e94560", linewidth=2, label="Route"),
        ],
        loc="lower left",
        fontsize=9,
        facecolor="#1a1a2e",
        edgecolor="#444",
        labelcolor="white",
    )

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, f"route_{waybill}.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    return path


def _create_timeline(events, waybill):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    parsed = []
    for e in events:
        date_str, time_str = (
            e.get("date", ""),
            e.get("time", "").replace("*", "").strip(),
        )
        if date_str and time_str:
            try:
                dt = datetime.strptime(f"{date_str} {time_str}", "%d %b %Y %H:%M")
                parsed.append(
                    {
                        "datetime": dt,
                        "location": e["location"],
                        "details": e["details"],
                        "color": _status_color(e["details"]),
                    }
                )
            except ValueError:
                pass

    if not parsed:
        return None

    parsed.sort(key=lambda x: x["datetime"])

    fig, ax = plt.subplots(figsize=(14, max(4, len(parsed) * 0.9)))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    times = [e["datetime"] for e in parsed]
    time_nums = [(t - times[0]).total_seconds() / 3600 for t in times]

    ax.plot(
        time_nums,
        list(range(len(parsed))),
        color="#e94560",
        linewidth=2,
        alpha=0.5,
        zorder=1,
    )

    for i, e in enumerate(parsed):
        ax.scatter(
            time_nums[i],
            i,
            c=e["color"],
            s=150,
            zorder=5,
            edgecolors="white",
            linewidth=1.5,
        )
        ax.annotate(
            f"  > {e['location']}\n  {e['details']}\n  @ {e['datetime'].strftime('%d %b, %H:%M')}",
            (time_nums[i], i),
            textcoords="offset points",
            xytext=(15, 0),
            fontsize=9,
            color="white",
            va="center",
        )

    ax.invert_yaxis()
    ax.set_title(
        f"Tracking Timeline -- Waybill: {waybill}",
        fontsize=16,
        color="white",
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Time (hours from first scan)", color="#aaa", fontsize=10)
    ax.set_yticks([])
    ax.tick_params(colors="#aaa", axis="x")
    ax.grid(True, axis="x", alpha=0.15, color="#444")
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#444")

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, f"timeline_{waybill}.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    return path


def generate_visuals(results, waybill):
    events = _parse_events(results)
    if not events:
        return []

    print("\n  Generating visualizations...")
    files = []
    f = _create_route_map(events, waybill)
    if f:
        print(f"  Route map: {f}")
        files.append(f)
    f = _create_timeline(events, waybill)
    if f:
        print(f"  Timeline: {f}")
        files.append(f)
    return files
