import argparse
import os
from dotenv import load_dotenv
load_dotenv(override=True)

from audiobookmarks.main_hoopla import main as hoopla_main
from audiobookmarks.main_libby import main as libby_main

book_name = "In Love With The World"
platform = "libby"

# If running in debug mode, first run the following command in the terminal:
# google-chrome --remote-debugging-port=9222

def main():
    parser = argparse.ArgumentParser(description='Get bookmarks for an audiobook.')
    parser.add_argument('platform', type=str, help='The platform hosting the book and bookmarks.')
    parser.add_argument('book', type=str, help='The name of the audiobook.')
    parser.add_argument("--debug", action="store_true", help="Run browser in debug mode (not headless).")
    args = parser.parse_args()

    if args.debug:
        os.environ["DEBUG_MODE"] = "true"
    else:
        os.environ["DEBUG_MODE"] = "false"

    if args.platform == "libby":
        libby_main(args.book)
    elif args.platform == "hoopla":
        hoopla_main(args.book)

if __name__ == "__main__":
    main()