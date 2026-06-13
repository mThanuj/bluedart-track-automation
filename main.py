import argparse

from src.browser import create_driver
from src.tracker import (
    open_tracking_page,
    process_waybills,
    interactive_mode,
    batch_from_file,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="BlueDart Waybill Tracking Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  python main.py -w 79034111122\n"
        "  python main.py -w 79034111122,79034111041\n"
        "  python main.py -f waybills.txt\n"
        "  python main.py -i\n"
        "  python main.py -w 79034111122 --no-auto-captcha",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-w", "--waybill", help="Waybill number(s), comma-separated")
    group.add_argument("-f", "--file", help="File with waybill numbers")
    group.add_argument(
        "-i", "--interactive", action="store_true", help="Interactive mode"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run headless (needs captcha visibility)",
    )
    parser.add_argument(
        "--no-auto-captcha", action="store_true", help="Manual captcha only"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    auto_solve = not args.no_auto_captcha

    print("\n  BlueDart Waybill Tracker v1.0")
    print("  " + "=" * 40)
    print(
        f"  Captcha: {'AUTO (with manual fallback)' if auto_solve else 'MANUAL ONLY'}"
    )

    driver = create_driver(headless=args.headless)
    try:
        open_tracking_page(driver)
        print()

        if args.waybill:
            waybills = [w.strip() for w in args.waybill.split(",") if w.strip()]
            print(f"  Tracking {len(waybills)} waybill(s)...")
            process_waybills(driver, waybills, auto_solve=auto_solve)
        elif args.file:
            batch_from_file(driver, args.file, auto_solve=auto_solve)
        elif args.interactive:
            interactive_mode(driver, auto_solve=auto_solve)

        print("\n  Done! Check output/ for results.\n")
    except KeyboardInterrupt:
        print("\n  Interrupted.")
    except Exception as e:
        print(f"\n  Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
