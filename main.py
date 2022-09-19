#!/usr/bin/python3

import os
import json
import random
import string
import argparse
from tokenize import endpats
from os.path import isfile, join
from vendors.sophos_central.sophos_api_connector import Auth
from vendors.sophos_central.sophos_migrate_endpoints import Migration
from vendors.sophos_central.sophos_endpoints import Endpoint
from config import Config

auth = Auth()
config = Config()
endpoints = Endpoint()
migration = Migration()
# users_uri = api_conf.users_uri
# endpoints_uri = api_conf.endpoints_uri
# migrations_uri = api_conf.migrations_uri
job_folder = ""

def create_job_folder():
    print("""[*] - We'll ask you to define a customer name. 
    - This name will be used to create a folder for this job with the name defined here.
    - If you leave it empty, we'll create a folder with the name job-{RANDON-CHARS}.
    - If you set a customer name (eg.: XPTO) and this folder already exists, we'll create a folder named XPTO-A7CU12
    """)

    answer = input("[?] - Define a customer name: ")
    folder_prefix = "job"
    if len(answer) != 0:
        folder_prefix = answer

    folder_created = False
    create_random = False
    while not folder_created:
        job_folder = folder_prefix
        if create_random or folder_prefix == "job":
            job_folder = job_folder + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        print("[*] - Checking if folder %s exists..." % (job_folder))
        if not os.path.exists("jobs/%s" % (job_folder)):
            try:
                os.makedirs("jobs/%s" % (job_folder))
                folder_created = True
            except:
                print("[*] - Error while creating Job folder.")
                exit()
        else:
            print("[!] - Job folder {JOBFOLDER} already exists!".format(JOBFOLDER=job_folder))
            answer = input("[?] - Keep defined folder name? [Yes/No] ")
            if any(answer.lower() == f for f in ['no', 'n', '0']):
                create_random = True

    print("[*] - Job folder created at: {JOBFOLDER}".format(JOBFOLDER=job_folder))
    return job_folder

def write_json(data, type, tenant_id = None):
    path = "curdir"
    filename = "%s_%s.json" % (tenant_id, type)
    file = '%s/%s/%s' % (path, job_folder, filename) 
    
    try:
        with open(file, 'w') as outfile:
            json.dump(data, outfile, indent=4)

    except IOError:
        print("[*] - Error while creating %s file." % (filename))
    
    return file

def main(args = None):
    print("[*] - Checking config.ini settings...")

    print("[#] - Migrate Endpoints:\t\t {CONFIG_ENDPOINTS}".format(CONFIG_ENDPOINTS=config.get("migrate_endpoints")))
    print("[#] - Migrate computer groups:\t\t {CONFIG_EP_GROUPS}".format(CONFIG_EP_GROUPS=config.get("migrate_endpoints_groups")))
    print("[#] - Migrate Exclusions:\t\t {CONFIG_EXCLUSIONS}".format(CONFIG_EXCLUSIONS=config.get("migrate_exclusions")))
    print("[#] - Migrate Endpoint/Server Policies:  {CONFIG_POLICIES}".format(CONFIG_POLICIES=config.get("migrate_policies")))
    print("[#] - Migrate Firewall Groups:\t\t {CONFIG_FIREWALLS}".format(CONFIG_FIREWALLS=config.get("migrate_firewall_groups")))

    answer = input("\n[*] - You really want to continue? [Yes / No]: ")
    if any(answer.lower() == f for f in ['no', 'n', '0']):
        print('[*] - Aborting execution!')
        exit()
    print("[*] - User confirmed. Continuing to create a new Migration Job.")

    job_folder = create_job_folder()

    source_headers, source_central_dataregion = auth.get_headers("source_sophos_central")
    dst_header, dst_central_dataregion = auth.get_headers("destination_sophos_central")
    
    headers = {
        "source": {
            "headers": source_headers,
            "region": source_central_dataregion
        },
        "destination": {
            "headers": dst_header,
            "region": dst_central_dataregion
        }
    }

    if config.get("migrate_exclusions"):
        print("[*] - Migrating Exclusions as it has been set on config.ini. \n")
        migration.migrate_exclusions(headers)

    # if config.get("migrate_firewall_groups"):
    #     print("[*] - Migrating Firewall Groups as it has been set on config.ini. \n")
    #     firewalls.migrate_groups(headers)


    if config.get("migrate_endpoints_groups"):
        print("[*] - Migrating computer groups.")
        print("[!] - Note that groups from Active Directory and Azure will not be migrated! You should run Azure/AD Sync for this.")
        endpoints.migrate_groups(headers)


    if config.get("migrate_policies"):
        print("[*] - Migrating Policies... \n")
        migration_policy_status = migration.migrate_policies(headers)
  
    if config.get("migrate_endpoints"):
        print("[*] - Migrating Endpoints... \n")

        print("[*] - Getting list of endpoints from Source tenant")
        endpoints_list, endpoints_ids, source_data = endpoints.get_all_endpoints( headers['source']['headers'], headers['source']['region'])
        
        if source_data == "from_file":
            print("\n")
            next_ep_id = ""
            current = 0
            for endpoint in endpoints_list:
                if next_ep_id is endpoint['id']: continue
                current += 1
                next_endpoint = endpoints_list[current]
                next_ep_id = next_endpoint['id']
                print("Hostname: {:<30} Hostname:{:^5}".format(endpoint['hostname'],next_endpoint['hostname']))
                print("{:<40} {:^10}".format(endpoint['id'],next_endpoint['id']))
                current += 1
                print("\n")

            print("\n[*] - Endpoints in the list will be migrated.\n")
            print("\t[0] - Yes, continue with this list. ")
            print("\t[1] - Migrate ALL endpoints from Central (ignore this list).")
            print("\t[2] - Abort execution.")
            
            answer = input("\n[*] - Choose an option: ")
            if int(answer) == 2:
                print('\n\n[*] - Aborting execution!')
                exit()
            elif int(answer) == 1: 
                print("[*] - Migrating all endpoints from Central.")
                endpoints_list, endpoints_ids, source_data = endpoints.get_all_endpoints( src_headers, Endpoints_URL, False)

        migration_job = migration.create_job(endpoints_ids, endpoints_list, src_headers['X-Tenant-ID'], dst_header, dst_central_dataregion)

        if migration_job:
            start_migration_job = migration.start_job(src_headers, src_central_dataregion, migration_job['id'], endpoints_ids, migration_job['token'])
            if start_migration_job:
                migration_data = dict()
                migration_data['Source_Tenant']      = start_migration_job
                migration_data['Destination_Tenant'] = migration_job
                
                job_file = write_json(migration_data, "job", src_headers['X-Tenant-ID'])
                if job_file: 
                    print("[*] - File with Job information created at: %s" % (job_file) )
                    exit(0)
            else:
                print("\n[*] - Some error occour while start migration job on Source tenant.")
                exit(1)
        else:
            print("\n[*] - Some error occour while creating migration job on Destination Tenant.")
            exit(1)

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
        # Endpoints_URL = "{DATA_REGION}/{ENDPOINTS_URI}".format(DATA_REGION=src_centralregion, ENDPOINTS_URI=endpoints_uri)
        job_folder = create_job_folder()
        endpoints.generate_ep_file(src_headers, job_folder)
    elif args.list_jobs:
        migration.list_jobs()
    else:
        print("[?] - No arguments passed. Starting main function.")
        main()
   