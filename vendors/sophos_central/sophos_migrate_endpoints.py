import os
import json
from time import sleep
from os.path import isfile, join
from config import ignore_policy_settings
from vendors.sophos_central.sophos_api_connector import CentralRequest

central = CentralRequest()

class Migration(object):

    def create_job(self, endpoints_ids, endpoints_list, from_tenant, headers, central_dataregion):
        
        print("[*] - Creating migration job from tenant: %s" % (from_tenant))
        
        migrate_json = {
            "fromTenant": from_tenant,
            "endpoints": endpoints_ids
        }

        migration_url = "{DATA_REGION}/{MIGRATION_URI}".format(DATA_REGION=central_dataregion, MIGRATION_URI="endpoint/v1/migrations")
        
        job_status, res_data = self._exec("POST", migration_url, headers, migrate_json)
        
        # try:
        #     res = requests.post(migration_url, headers=headers, json=migrate_json)
        #     res_code = res.status_code
        #     res_data = res.json()
        #     print("[*] - HTTP Return code: %d" % (res_code))
        
        # except requests.exceptions.HTTPError :
        #   pass

        # if res_code > 201:
        #     res_users_error_code = res_data['error']
        #     print("\n[*] - Error on creating this Job")
        #     print("ERROR_CODE: %d" % (res_code))
        #     print("Error message: %s" % (res_users_error_code))
        #     print("******************************")
        #     return False

        # elif res_code == 201 or res_code == 200:
        if job_status:
            print("[*] - Job created. ID: %s" % (res_data['id']))

            migrate_json["endpoints"]  = endpoints_list
            migrate_json["job_id"]     = res_data['id']
            migrate_json["token"]      = res_data['token']
            migrate_json["createdAt"]  = res_data['createdAt']
            migrate_json["expiresAt"]  = res_data['expiresAt']

            # tenant_path = self.tenant_path(headers['X-Tenant-ID'])
            # migration_file = '%s/%s.json' % (path,res_data['id']) 
            
            # try:
            #     with open(migration_file, 'w') as outfile:
            #         json.dump(migrate_json, outfile, indent=4)

            # except IOError:
            #     print("[*] - Error while creating status file.")

            return migrate_json

    def start_job(self, headers, central_dataregion, migration_id, endpoints_ids, token):
        print("[*] - Starting last created job: %s" % (migration_id))
     
        params_data = {
            "id": migration_id,
            "token": token,
            "endpoints": endpoints_ids
        }
        
        migration_url = "{DATA_REGION}/{MIGRATION_URI}/{MIGRATION_ID}".format(DATA_REGION=central_dataregion, MIGRATION_URI="endpoint/v1/migrations", MIGRATION_ID=migration_id)

        job_status, job_data = self._exec("PUT", migration_url, headers, params_data)
        if job_status:
            return job_data

    def list_jobs(self):
        listdir = ""
        job_files = [f for f in listdir("./jobs/") if isfile(join("./jobs/", f))]

        for job_id in job_files:
            print("[%d] - %s" % (job_files.index(job_id), job_id.split(".")[0]))

    def status(self,headers, central_dataregion, migration_id = ""):

        print("[*] - Function: Get job status")

        if migration_id:
            migration_url = "{DATA_REGION}/{MIGRATION_URI}/{MIGRATION_ID}/endpoints".format(DATA_REGION=central_dataregion, MIGRATION_URI="endpoint/v1/migrations", MIGRATION_ID=migration_id)
        else:
            migration_url = "{DATA_REGION}/{MIGRATION_URI}".format(DATA_REGION=central_dataregion, MIGRATION_URI="endpoint/v1/migrations")

        migration_data = self._exec("GET", migration_url, headers)

        # print(json.dumps(res_data, indent=4))

        #  tenant_path = self.tenant_path(headers['X-Tenant-ID'])

        # policies_json = "%s/%s_policies.json" % (path, headers['X-Tenant-ID'])   

        # with open(policies_json, 'w') as outfile:
        #     json.dump(res_data, outfile, indent=4)
    

        if migration_id:
            tenant_path = self.tenant_path(headers['X-Tenant-ID'])
            migration_file = "%s/%s.json" % (tenant_path, migration_id)

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

    def migrate_exclusions(self, headers, migration_type = None):
        # src_headers, src_central_dataregion, dst_headers, dst_central_dataregion,
        print("[*] - Function: Migrating exclusions")

        if not migration_type:
            migration_type = ["exclusions/scanning", "exclusions/isolation", "exclusions/intrusion-prevention", "web-control/local-sites"] 

        # Getting source Central settings

        for type_url in migration_type:
            type_url = "endpoint/v1/settings/" + type_url
            print("\n\n[*] - Getting settings for " + type_url)
            src_setting_url = "{DATA_REGION}/{SETTING_URI}".format(DATA_REGION=headers['source']['region'], SETTING_URI=type_url)
            dst_setting_url = "{DATA_REGION}/{SETTING_URI}".format(DATA_REGION=headers['destination']['region'], SETTING_URI=type_url)
            print("[*] - URL: " + src_setting_url)
            status, data = central.get(src_setting_url, headers['source']['headers'])

            if status:
                # ignored_types = ['detectedExploit', 'behavioral']

                exclusion_count = 0

                for exclusion in data['items']:
                    exclusion_dict = {
                        "type":        exclusion['type'],
                        "value":       exclusion['value']
                    }
                    if "comment" in exclusion.keys(): exclusion_dict["comment"] = exclusion['comment']
                    if "scanmode" in exclusion.keys(): exclusion_dict["scanMode"] = exclusion['scanMode']
                    if "description" in exclusion.keys(): exclusion_dict["description"] = exclusion['description']

                    send_exclusion_status, send_exclusion_data = central.insert(dst_setting_url, headers['destination']['region'], exclusion_dict)
                    if send_exclusion_status:
                        print("[!] - Creating exclusion for {migration_type} success!".format(migration_type=migration_type))
                    else:
                        print("[-] - Could not create exclusions for {migration_type}".format(migration_type=migration_type))

    def get_policies(self, headers):
        
        print("[*] - Getting All Policies")

        params_data = {}
        params_data["pageTotal"] = True
        # params_data["view"]      = 'basic'

        policies_url = "{DATA_REGION}/{URI}".format(DATA_REGION=headers['region'], URI="endpoint/v1/policies")
        res_status, res_data = central.get(policies_url, headers['headers'], params_data)
        if res_status:
            return res_data

    def migrate_policies(self, headers):

        src_policies = self.get_policies(headers['source'])
        # dst_policies = self.get_policies(headers['destination'])

        policies_url = "{DATA_REGION}/{URI}".format(DATA_REGION=headers['destination']['region'], URI="endpoint/v1/policies")

        for policy in src_policies['items']:

            if policy['name'] != "CRYPTOGUARD-POC":
                continue

            if policy['type'] != "threat-protection":
                continue

            # print(json.dumps(policy['settings'], indent=4))
            # print("\n --------------- \n\n")

            # if policy['type'] == "threat-protection":
            policy_settings = policy['settings']

            if policy['type'] in ["threat-protection", "server-threat-protection"]:

                for remove_setting in ignore_policy_settings[policy['type']]: 
                    print("removing setting: " + remove_setting)
                    policy_settings.pop(remove_setting)

                # print(json.dumps(policy['settings'], indent=4))

                for setting in policy_settings: 
                    # print("removing recommended setting: " + setting)
                    policy_settings[setting].pop("recommendedValue", None)
                
                # print("\n Listing exclusions....")
                # for exclusions in policy['settings']["endpoint.threat-protection.exclusions.scanning"]['value']:
                #     print("\n\n - exclusion type: " + exclusions['type'])
                #     print(" - exclusion name: " + exclusions['value'])
                #     if exclusions['type'] == "detectedExploit":
                #         print(' - Deleting detectedExploit ' + exclusions['value'])
                #         print(type(policy_settings["endpoint.threat-protection.exclusions.scanning"]['value']))
                #         policy_settings["endpoint.threat-protection.exclusions.scanning"]['value'].pop(exclusions)
                #         print("-----------\n")

                scanning_exclusions = [x for x in policy['settings']["endpoint.threat-protection.exclusions.scanning"]['value'] if not ("detectedExploit" == x.get('type'))]
                policy_settings["endpoint.threat-protection.exclusions.scanning"]['value'] = scanning_exclusions
                print(json.dumps(policy_settings, indent=4))

            if policy['name'] == "Base Policy":
                policy_content = {
                    'settings' : policy['settings']
                }

            else:
                policy_content = {
                    'name'     : policy['name'].replace("-"," ").replace("_", " "),
                    'type'     : policy['type'],
                    'appliesTo': {},
                    'priority' : policy['priority'],
                    'settings' : policy_settings
                }

            print(json.dumps(policy_settings, indent=4))

            if policy['name'] == "Base Policy":
                print("[*] - Updating Base Policy for {POLICYTYPE}".format(POLICYTYPE=policy['type']))
                base_policy_url = "/{POLICYTYPE}/base".format(POLICYTYPE=policy['type'])
                url = policies_url + "" + base_policy_url
                status, data = central.update(url, headers['destination']['headers'], policy_content)
            else:
                print("[*] - Creating a new {POLICYTYPE} policy: {POLICYNAME} ".format(POLICYTYPE=policy_content['type'], POLICYNAME=policy_content['name']))
                status, data = central.insert(policies_url, headers['destination']['headers'], policy_content)

            if not status:
                print("[!] - Error while creating policy {POLICYNAME}".format(POLICYNAME=policy_content['name']))


    def migrate_computer_groups(self, headers, source_computers_groups):
        print("[*] - Function: Migrate computer groups")

        endpoints_groups_url = "{DATA_REGION}/{GROUPS_URI}".format(DATA_REGION=headers['destination']['region'], GROUPS_URI="endpoint/v1/endpoint-groups")

        created_groups = list()

        for group in source_computers_groups:

            group_dict = {
                "name": group['name'],
                "type": group['type'],
            }

            if len(group['description']) != 0: group_dict['description'] = group['description']

            groups_status, groups_data = central.insert(endpoints_groups_url, headers['destination']['headers'], group_dict)
            if groups_status:
                print(json.dumps(groups_data, indent=4))
                created_groups.append(groups_data)

        return created_groups