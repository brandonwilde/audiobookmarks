import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from audiobookmarks.utils import generate_arg_parser
load_dotenv(override=True)

from audiobookmarks.main_hoopla import main as hoopla_main
from audiobookmarks.main_libby import main as libby_main

# If running in debug mode, first run the following command in the terminal:
# google-chrome --remote-debugging-port=9222


class Args(BaseModel):
    '''
    Args for the main audiobookmarks function.
    '''
    platform: str = Field(..., description="The platform hosting the book and bookmarks.")
    book: str = Field(..., description="The name of the audiobook.")
    debug: bool = Field(False, description="Run browser in debug mode (not headless).")

    class Config:
        description = "Get bookmarks for an audiobook"


def main(args: Args):
    '''
    Get bookmarks for an audiobook.
    '''
    if args.debug:
        os.environ["DEBUG_MODE"] = "true"
    else:
        os.environ["DEBUG_MODE"] = "false"
    
    if args.platform.lower() == "libby":
        libby_main(args.book, args.debug)
    elif args.platform.lower() == "hoopla":
        hoopla_main(args.book, args.debug)

if __name__ == "__main__":
    parser = generate_arg_parser(Args)
    args = parser.parse_args()
    args_obj = Args(**vars(args))
    main(args_obj)