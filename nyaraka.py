#!/usr/bin/env python

import os
import json
import logging
import argparse
import requests

from tqdm import tqdm
from os.path import join
from urllib.parse import urlparse

class OmekaDownloader:

    def __init__(self, base_url, key=None, archive_dir=None):
        self.base_url = base_url.strip("/")
        self.api_url = base_url + "/api/"
        self.check_api()
        self.key = key
        if archive_dir == None:
            uri = urlparse(self.base_url)
            archive_dir = (uri.netloc + uri.path).replace("/", "-")
        self.archive_dir = archive_dir
        if not os.path.isdir(archive_dir):
            os.makedirs(archive_dir)

    def check_api(self):
        resp = requests.get(self.api_url + 'resources')
        if resp.status_code == 403:
            raise Exception("Omeka API is not enabled for %s" % self.api_url)
        elif resp.status_code != 200:
            raise Exception("Missing Omeka at %s" % self.api_url)
        else:
            return True

    def download(self):
        self.save_file(self.api_url + "site", join(self.archive_dir, "site.json"))
        total_items = self.get_total_items()
        item_count = 0
        pbar = tqdm(total=total_items)
        for collection in self.paginator('collections'):
            self.save_json(collection, 'collections', collection['id'], "collection.json")
            for item in self.paginator('items', {'collection': collection['id']}):
                pbar.update(1)
                self.save_json(item, 'collections', collection['id'],
                               'items', item['id'], 'item.json')

                for file in self.paginator('files', {'item': item['id']}):
                    self.save_json(file, 'collections', collection['id'], 
                                   'items', item['id'], 'files', file['id'], 
                                   'file.json')

                    for name, url in file['file_urls'].items():
                        if url:
                            filename, ext = os.path.splitext(url)
                            path = os.path.join(
                                self.archive_dir,
                                'collections', 
                                str(collection['id']),
                                'items',
                                str(item['id']),
                                'files',
                                str(file['id']),
                                name + ext
                            )
                            self.save_file(url, path)
        pbar.close()
        logging.info("finished archiving %s", self.base_url)

    def save_json(self, obj, *path_parts):
        path_parts = map(str, path_parts)
        path = join(self.archive_dir, *path_parts)
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        logging.info("writing %s", path)
        open(path, "w").write(json.dumps(obj, indent=2))
        return path

    def paginator(self, url_path, params={}):
        if self.key:
            params['key'] = self.key

        url = self.api_url + url_path
        params['page'] = 1

        while True:
            resp = requests.get(url, params=params)

            # This is a work around for when there is nothing in the 
            # paginator, and Omeka returns an empty string instead of an 
            # empty array. This can happen when a collection is added
            # but it contains no items, or when an item has no files.

            if (resp.text == ""):
                results = []
            else:
                results = resp.json()

            if len(results) == 0:
                break

            yield from results
            params['page'] += 1

    def save_file(self, url, path):
        logging.info("saving %s to %s", url, path)
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory)

        resp = requests.get(url, stream=True)

        if (resp.status_code != 200):
            logging.error("got %s when fetching %s", resp.status_code, url)
            raise Exception("unable to fetch %s" % url)

        with open(path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=16384):
                if chunk:
                    fh.write(chunk)

    def get_total_items(self):
        count = 0
        for collection in self.paginator('collections'):
            count += collection['items']['count']
        return count

def main(url, key=None):
    logging.basicConfig(
        filename='nyaraka.log',
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    omeka = OmekaDownloader(url, key=key)
    omeka.download()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Omeka base url")
    parser.add_argument("--key", "-k", help="Your Omeka API key")
    args = parser.parse_args()
    main(args.url, key=args.key)