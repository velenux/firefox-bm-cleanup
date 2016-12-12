# Firefox bookmarks cleanup

Can't deal with all those old bookmarks sitting in your bookmark list?
This script has been created to take care of that (and something more)!

## Usage

Export your bookmarks in json format via *Bookmarks > Show all bookmarks > Import and backup > Backup*, Then invoke this script as:

```bash
# python ff-bm-cleanup.py path/to/your/bookmarks.json
```

This will generate in the working directory a file named `bookmarks-fixed.json`; you can then restore this file to Firefox using the same menu by selecting *Restore > Choose File*.

## Notes

For the best results I recommend creating a new profile (`firefox -p`) and importing the bookmarks there. Otherwise you can try to delete your old places.sqlite and reset your Sync profile, but I don't really recommend that.
