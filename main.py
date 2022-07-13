#!/usr/bin/python3

import os
import sys
import json
import time
import asyncio
import logging
import requests
import argparse
from mwt import mwt
from os import listdir
from tokenize import endpats
from os.path import isfile, join
from asyncio.windows_events import NULL

from vendors.sophos_central.sophos_auth import Auth
from vendors.sophos_central.sophos_migrate import Migration
from vendors.sophos_central.sophos_endpoints import Endpoint
from config import sophos_central_api_config as api_conf

auth = Auth()
endpoint = Endpoint()
migration = Migration()
users_uri = api_conf.users_uri
endpoints_uri = api_conf.endpoints_uri
migrations_uri = api_conf.migrations_uri

def main(args = None):
    answer = input("\n[*] - You really want to continue? [Yes / No]: ")
    if any(answer.lower() == f for f in ['no', 'n', '0']):
        print('[*] - Aborting execution!')
        exit()
    print("[*] - User confirmed. Continuing to create a new Migration Job.")

    global endpoints_ids
    global endpoints_list
    
    source_headers, source_central_dataregion = auth.get_headers("source_sophos_central")
    dst_header, dst_central_dataregion = auth.get_headers("destination_sophos_central")
    
    Endpoints_URL = "{DATA_REGION}/{ENDPOINTS_URI}".format(DATA_REGION=source_central_dataregion, ENDPOINTS_URI=endpoints_uri)

    endpoints_list, endpoints_ids = endpoint.get_all( source_headers, Endpoints_URL)
    print("[*] - Getting all endpoints from Source tenant")
    migration_job = migration.create_job(endpoints_ids, endpoints_list, source_headers['X-Tenant-ID'], dst_header, dst_central_dataregion)

    if migration_job:
        start_migration_job = migration.start_job(source_headers, source_central_dataregion, migration_job['id'], endpoints_ids, migration_job['token'])
        print("[*] - File with Job information created at: ./jobs/%s.json" % (start_migration_job['id']) )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script for migrating Sophos Central endpoints between sub-estates.')
    parser.add_argument('--list-jobs', '-l', help='List all the job IDs created by this tool.', action="store_true" )
    parser.add_argument('--status', '-s', help='Status of a specific migration ID.\nYou should specify the migration id along with --status/-s.\n\nIf you don\'t know which migration ID, you can run --list-jobs/-l for getting them all',  type=str)

    args = parser.parse_args()

    if args.status:
        dst_headers, dst_centralregion = auth.get_headers("destination_sophos_central")
        migration.status(dst_headers, dst_centralregion, args.status)
    elif args.list_jobs:
        migration.list_jobs()
    else:
        print("[*] - No arguments passed. Starting main function.")
        main()
   