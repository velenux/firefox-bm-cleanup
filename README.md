# Firefox bookmarks cleanup

Can't deal with all those old bookmarks sitting in your bookmark list?

This script has been created to take care of that (and something more)!

It will try to contact each bookmark, remove those that reply with an error code, follow redirects and update the URL for outdated bookmarks and it will try to populate and enhance the bookmark tags using both the tags from the bookmark (if any) and from the webpage `keywords` meta tag, as discussed in [Intelligent bookmarking draft](https://robert.accettura.com/blog/2005/08/01/intelligent-bookmarking-draft/).

## Usage

Export your bookmarks in JSON via *Bookmarks > Show all bookmarks > Import and backup > Backup*, then invoke this script as:

```bash
python ff-bm-cleanup.py path/to/your/bookmarks.json
```

This will generate in the working directory a file named `bookmarks-fixed.json`; you can then restore this file to Firefox using the same menu by selecting *Restore > Choose File*.

## Notes

For the best results I recommend creating a new profile (`firefox -p`) and importing the bookmarks there. Otherwise you can try to delete your old `places.sqlite` and reset your Sync profile, but I don't really recommend that.
