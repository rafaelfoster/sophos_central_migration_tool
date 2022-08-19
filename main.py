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
from argparse import RawTextHelpFormatter
from vendors.sophos_central.sophos_auth import Auth
from vendors.sophos_central.sophos_migrate import Migration
from vendors.sophos_central.sophos_endpoints import Endpoint
from config import sophos_central_api_config as api_conf

auth = Auth()
endpoints = Endpoint()
migration = Migration()
users_uri = api_conf.users_uri
endpoints_uri = api_conf.endpoints_uri
migrations_uri = api_conf.migrations_uri

def main(args = None):
    # answer = input("\n[*] - You really want to continue? [Yes / No]: ")
    # if any(answer.lower() == f for f in ['no', 'n', '0']):
    #     print('[*] - Aborting execution!')
    #     exit()
    # print("[*] - User confirmed. Continuing to create a new Migration Job.")
    
    source_headers, source_central_dataregion = auth.get_headers("source_sophos_central")
    
    dst_header, dst_central_dataregion = auth.get_headers("destination_sophos_central")
    
    Endpoints_URL = "{DATA_REGION}/{ENDPOINTS_URI}".format(DATA_REGION=source_central_dataregion, ENDPOINTS_URI=endpoints_uri)

    print("[*] - Getting list of endpoints from Source tenant")
    endpoints_list, endpoints_ids, source_data = endpoints.get_all( source_headers, Endpoints_URL)
    
    if source_data == "from_file":
        print("\n")
        next_ep_id = ""
        current = 0
        for endpoint in endpoints_list:
            if next_ep_id is endpoint['id']: continue
            #current += 1
            next_endpoint = endpoints_list[current]
            next_ep_id = next_endpoint['id']
            print("Hostname: {:<30} Hostname:{:^5}".format(endpoint['hostname'],next_endpoint['hostname']))
            print("{:<40} {:^10}".format(endpoint['id'],next_endpoint['id']))
            current += 1
            print("\n")

        print("\n[*] - This endpoints on the list will be migrated\n")
        print("\t[0] - Yes, continue with this list. ")
        print("\t[1] - Migrate ALL endpoints from Central (ignore this list).")
        print("\t[2] - Abort execution.")
        
        answer = input("\n[*] - Choose an option: ")
        if int(answer) == 2:
            print('\n\n[*] - Aborting execution!')
            exit()
        elif int(answer) == 1: 
            print("[*] - Migrating all endpoints from Central.")
            endpoints_list, endpoints_ids, source_data = endpoints.get_all( source_headers, Endpoints_URL, False)

    migration_job = migration.create_job(endpoints_ids, endpoints_list, source_headers['X-Tenant-ID'], dst_header, dst_central_dataregion)

    if migration_job:
        start_migration_job = migration.start_job(source_headers, source_central_dataregion, migration_job['id'], endpoints_ids, migration_job['token'])
        print("[*] - File with Job information created at: ./jobs/%s.json" % (start_migration_job['id']) )
    else:
        print("\n[*] - Some error occour while creating migration job.")

if __name__ == "__main__":
    print("[*] - Starting Sophos Central Migration Tool!\n")
    parser = argparse.ArgumentParser(description='Script for migrating Sophos Central endpoints between sub-estates.')
    parser.add_argument('--list-jobs', '-l', help='List all the job IDs created by this tool.', action="store_true" )
    parser.add_argument('--status', '-s', help='Status of a specific migration ID.\nYou should specify the migration id along with --status/-s.\n\nIf you don\'t know which migration ID, you can run --list-jobs/-l for getting them all', type=str,)
    parser.add_argument('--endpoint-file', '-e', action="store_true", help='Generate a list of Endpoints existing on the source tenant.\nIt will create a file inside \"./jobs\" folder named TENANT_ID_endpoints.json.')

    args = parser.parse_args()

    if args.status:
        dst_headers, dst_centralregion = auth.get_headers("destination_sophos_central")
        migration.status(dst_headers, dst_centralregion, args.status)
    elif args.endpoint_file:
        src_headers, src_centralregion = auth.get_headers("source_sophos_central")
        Endpoints_URL = "{DATA_REGION}/{ENDPOINTS_URI}".format(DATA_REGION=src_centralregion, ENDPOINTS_URI=endpoints_uri)
        endpoints.generate_ep_file(src_headers, Endpoints_URL)
    elif args.list_jobs:
        migration.list_jobs()
    else:
        print("[*] - No arguments passed. Starting main function.")
        main()
   
