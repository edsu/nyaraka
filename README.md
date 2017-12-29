## nyaraka

*nyaraka* will collect the data in an [Omeka] instance using its API and persist
it to the file system.  *nyaraka* is Swahili for *archive*.  *omeka* is a
Swahili word that means "to display or layout goods or wares; to speak out; to
spread out; to unpack".<sup>[1]</sup>

## Install

    pip install nyaraka

## Usage

    nyaraka.py http://omeka.astrodomememories.org

If you want to collect private items and user information you'll need an API key:

    nyaraka.py --key sldkjslkjflkjdflkjsdfkljs http://omeka.astrodomememories.org

nyaraka is single threaded, so there will only be one request issued at a time.
But if you want to be extra polite and sleep a little bit between requests you
can use the --sleep option:

    nyaraka.py --sleep .5 http://omeka.astrodomememories.org

## Output

Since Omeka's database schema requires one-to-many relationships between collections and items, and items and files, the metadata and media files are written 
to disk using the following naming scheme:

    {archive-dir}/collections/{collection-id}/items/{item-id}/files/{file-id}/original.jpg

For example:

```
omeka.astrodomememories.org
omeka.astrodomememories.org/site.json
omeka.astrodomememories.org/collections
omeka.astrodomememories.org/collections/1
omeka.astrodomememories.org/collections/1/collection.json
omeka.astrodomememories.org/collections/1/items
omeka.astrodomememories.org/collections/1/items/1
omeka.astrodomememories.org/collections/1/items/1/item.json
omeka.astrodomememories.org/collections/1/items/1/files
omeka.astrodomememories.org/collections/1/items/1/files/1
omeka.astrodomememories.org/collections/1/items/1/files/1/fullsize.jpg
omeka.astrodomememories.org/collections/1/items/1/files/1/original.jpg
omeka.astrodomememories.org/collections/1/items/1/files/1/file.json
omeka.astrodomememories.org/collections/1/items/1/files/1/thumbnail.jpg
omeka.astrodomememories.org/collections/1/items/1/files/1/square_thumbnail.jpg
```

[1]: http://mars.gmu.edu/bitstream/handle/1920/6089/2008-02-20_IntroOmeka.pdf
[application]: http://omeka.org/ 
[Omeka]: http://omeka.org/
