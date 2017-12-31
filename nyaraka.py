#!/usr/bin/env python

import os
import json
import time
import logging
import argparse
import requests

from tqdm import tqdm
from os.path import join
from urllib.parse import urlparse

class OmekaDownloader:

    def __init__(self, base_url, key=None, archive_dir=None, sleep=None):
        self.base_url = base_url.strip("/")
        self.api_url = base_url + "/api/"
        self.check_api()
        self.key = key
        self.sleep = sleep
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

    def download(self, sleep=None):
        self.save_file(self.api_url + "site", join(self.archive_dir, "site.json"))
        total_items = self.get_total_items()
        item_count = 0
        found = False
        progress = tqdm(total=total_items, unit='items')

        for collection in self.paginator('collections'):
            found = True
            self.save_json(collection, 'collections', collection['id'], "collection.json")
            self.download_items(collection=collection['id'], progress=progress)

        if not found:
            self.download_items(progress=progress)

        # download extra resources
        self.download_other_resources()

        progress.close()
        logging.info("finished archiving %s", self.base_url)

    def download_other_resources(self):
        # download resources other than collections and items
        resp = requests.get(join(self.api_url, 'resources')).json()
        for name, resource in resp.items():
            # these are either not browsable or have already been downloaded 
            if name in ('users', 'collections', 'items', 'files'):
                continue
            if name in ('site', 'resources'):
                r = requests.get(resource['url']).json()
                self.save_json(r, '%s.json' % name)
            else:
                for r in self.paginator(resource['url']):
                    self.save_json(r, name, '%s.json' % r['id'])

    def download_items(self, collection=None, progress=None):
        if collection:
            paginator = self.paginator('items', {'collection': collection})
            prefix = os.path.join('collections', str(collection))
        else:
            paginator = self.paginator('items')
            prefix = ''

        for item in paginator:

            if progress:
                progress.update(1)

            self.save_json(item, prefix, 'items', item['id'], 'item.json')

            for file in self.paginator('files', {'item': item['id']}):

                self.save_json(file, prefix, 'items', item['id'], 
                    'files', file['id'], 'file.json')

                for name, url in file['file_urls'].items():
                    if url:
                        filename, ext = os.path.splitext(url)
                        path = os.path.join(
                            self.archive_dir,
                            prefix,
                            'items',
                            str(item['id']),
                            'files',
                            str(file['id']),
                            name + ext
                        )
                        self.save_file(url, path)

    def save_json(self, obj, *path_parts):
        path_parts = map(str, path_parts)
        path = join(self.archive_dir, *path_parts)
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        logging.info("writing %s", path)
        open(path, "w").write(json.dumps(obj, indent=2))
        return path

    def paginator(self, url, params={}):
        if self.key:
            params['key'] = self.key

        if not url.startswith('http'):
            url = self.api_url + url

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

            self.do_sleep()

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

        self.do_sleep()

    def get_total_items(self):
        count = 0
        found = False
        for collection in self.paginator('collections'):
            found = True
            count += collection['items']['count']
        if not found:
            count = len(list(self.paginator('items')))
        return count

    def do_sleep(self):
        if self.sleep:
            time.sleep(self.sleep)

def main(url, key=None, sleep=None):
    logging.basicConfig(
        filename='nyaraka.log',
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    omeka = OmekaDownloader(url, key=key, sleep=sleep)
    omeka.download()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Omeka base url")
    parser.add_argument("--key", "-k", help="Your Omeka API key")
    parser.add_argument("--sleep", "-s", type=float,
        help="Seconds to sleep between requests to the Omeka API")
    args = parser.parse_args()
    try:
        main(args.url, key=args.key, sleep=args.sleep)
    except KeyboardInterrupt:
        print("\nstopped!\n")
