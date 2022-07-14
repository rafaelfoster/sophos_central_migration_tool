import os
import json
import requests
from os import listdir
from pathlib import Path
from os.path import isfile, join
from asyncio.windows_events import NULL

class Migration(object):

    def create_job(self, endpoints_ids, endpoints_list, from_tenant, headers, central_dataregion):
        
        print("[*] - Creating migration job from tenant: %s" % (from_tenant))
        migrate_json = {
            "fromTenant": from_tenant,
            "endpoints": endpoints_ids
        }

        migration_url = "{DATA_REGION}/{MIGRATION_URI}".format(DATA_REGION=central_dataregion, MIGRATION_URI="endpoint/v1/migrations")
        
        try:
            res = requests.post(migration_url, headers=headers, json=migrate_json)
            res_code = res.status_code
            res_data = res.json()
            print("[*] - HTTP Return code: %d" % (res_code))
        
        except requests.exceptions.HTTPError :
          pass

        if res_code > 201:
            res_users_error_code = res_data['error']
            print("\n[*] - Error on creating this Job")
            print("ERROR_CODE: %d" % (res_code))
            print("Error message: %s" % (res_users_error_code))
            print("******************************")
            return False

        elif res_code == 201 or res_code == 200:

            print("[*] - Job created. ID: %s" % (res_data['id']))

            migrate_json["endpoints"]  = endpoints_list
            migrate_json["job_id"]     = res_data['id']
            migrate_json["token"]      = res_data['token']
            migrate_json["createdAt"]  = res_data['createdAt']
            migrate_json["expiresAt"]  = res_data['expiresAt']
            
            migration_file = 'jobs/%s.json' % (res_data['id']) 

            try:
                os.mkdir("./jobs")
            except:
                pass 
            
            try:
                with open(migration_file, 'w') as outfile:
                    json.dump(migrate_json, outfile, indent=4)

            except IOError:
                print("[*] - Error while creating status file.")

            return res_data

    def start_job(self, headers, central_dataregion, migration_id, endpoints_ids, token):
        print("[*] - Starting last created job: %s" % (migration_id))
     
        params_data = {
            "id": migration_id,
            "token": token,
            "endpoints": endpoints_ids
        }
        
        migration_url = "{DATA_REGION}/{MIGRATION_URI}/{MIGRATION_ID}".format(DATA_REGION=central_dataregion, MIGRATION_URI="endpoint/v1/migrations", MIGRATION_ID=migration_id)

        try:
            res_migration = requests.put(migration_url, headers=headers, json=params_data)
            res_migration_code = res_migration.status_code
            migration_data = res_migration.json()

        except requests.exceptions.RequestException as res_exception:
            pass

        if res_migration_code > 201:
            res_migration_error_code = migration_data['error']
            print("[*] - Error on starting this Job")
            print("ERROR_CODE: %d" % (res_migration_code))
            print("Error message: %s" % (res_migration_error_code))
            print("******************************\n\n")
            return res_migration_error_code

        elif res_migration_code == 200 or res_migration_code == 201 :
            print("[*] - Start job succeed!")
            return migration_data

    def list_jobs(self):
        job_files = [f for f in listdir("./jobs/") if isfile(join("./jobs/", f))]

        for job_id in job_files:
            print("[%d] - %s" % (job_files.index(job_id), job_id.split(".")[0]))

    def status(self,headers, central_dataregion, migration_id = ""):

        print("[*] - Function: Get job status")

        if migration_id:
            migration_url = "{DATA_REGION}/{MIGRATION_URI}/{MIGRATION_ID}/endpoints".format(DATA_REGION=central_dataregion, MIGRATION_URI="endpoint/v1/migrations", MIGRATION_ID=migration_id)
        else:
            migration_url = "{DATA_REGION}/{MIGRATION_URI}".format(DATA_REGION=central_dataregion, MIGRATION_URI="endpoint/v1/migrations")

        try:
            res_migration = requests.get(migration_url, headers=headers)
            res_migration_code = res_migration.status_code
            migration_data = res_migration.json()
         
        except requests.exceptions.RequestException as res_exception:
            res_migration_error_code = migration_data['error']
            

        if res_migration_code > 201:
            print("[*] - Error on starting this Job")
            print("ERROR_CODE: %d" % (res_migration_code))
            print("Error message: %s" % (res_migration_error_code))
            print("******************************\n\n")
            return res_migration_error_code
        else:
            if migration_id:
                migration_file = "./jobs/%s.json" % (migration_id)

                try:
                    print('[*] - Job file exists... Getting data...')
                    with open(migration_file) as json_file:
                        migration_json = json.load(json_file)

                    job_endpoints = migration_json['endpoints']
                except:
                    pass

                print("[*] - Getting job status of Job ID: %s" % (migration_id) )
                print("\n========================================================================")
                for migration_status in migration_data['items']:
                    try:
                        if job_endpoints:
                            endpoint = next((item for item in job_endpoints if item['id'] == migration_status['id']), "HOSTNAME_NOT_FOUND" )
                            print("Endpoint:\t %s" % ( endpoint['hostname'].title() ) )
                    except:
                        pass 

                    print("Endpoint ID:\t %s" % (migration_status['id']) )
                    print("Status:\t\t %s" % (migration_status['status']) )
                    if migration_status['status'] == "failed": 
                        print("Reason:\t\t %s" % (migration_status['reason']) )
                        print("Failed at:\t %s" % (migration_status['failedAt']) )
                    print("\n")
            else:
                print(migration_data)
            return res_migration_code

