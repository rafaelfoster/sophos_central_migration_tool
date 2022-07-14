import os
import json
import requests
from mwt import mwt

class Endpoint(object):

    headers = ""
    _request_page  = 1
    _endpoints_list = []
    _endpoints_ids  = []

    def setHeaders(self, headers):
        self.headers = headers
    
    def generate_ep_file(self, tenant_headers, endpoints_url):
        print("[*] - Generating a list of endpoints from Central...")
        endpoints_list, endpoints_ids = self.fetch_all_endpoints(tenant_headers, endpoints_url)

        endpoints_file = "./jobs/%s_endpoints.json" % (tenant_headers['X-Tenant-ID'])

        try:
            os.mkdir("./jobs")
        except:
            pass 
        
        try:
            with open(endpoints_file, 'w') as outfile:
                json.dump(endpoints_list, outfile, indent=4)

        except IOError:
            print("[*] - Error while creating endpoints file.")

        print("[*] - List of endpoints generated to file: {EP_FILE}".format(EP_FILE=endpoints_file))

    def get_all(self, tenant_headers, endpoints_url, use_generated_file = True):
        
        endpoints_file = "./jobs/%s_endpoints.json" % (tenant_headers['X-Tenant-ID'])
        if endpoints_file and use_generated_file:
            print("[*] - Using previously generated file: %s" % (endpoints_file))
            with open(endpoints_file) as json_file:
                endpoints_json = json.load(json_file)
                endpoints_ids  = []
                for endpoint in endpoints_json:
                    endpoints_ids.append(endpoint['id'])
            return endpoints_json, endpoints_ids, "from_file"
        
        print("[*] - Fetching endpoints from Sophos Central")
        endpoints_list, endpoints_ids = self.fetch_all_endpoints(tenant_headers, endpoints_url)
        return  endpoints_list, endpoints_ids, "from_central"
        

    def fetch_all_endpoints(self, tenant_headers, endpoints_url):
        params_data = {}
        params_data["pageTotal"] = True
        # params_data["pageSize"]  = 2
        params_data["view"]      = 'basic'

        def append_endpoints(endpoints_url, tenant_headers, pageKey = ""):
            params_data["pageFromKey"] = pageKey

            try:
                
                res_endpoints = requests.get(endpoints_url, headers=tenant_headers, params=params_data)
                res_endpoints_code = res_endpoints.status_code
                endpoints_data = res_endpoints.json()

            except requests.exceptions.RequestException as res_exception:
                res_endpoints_error_code = endpoints_data['error']
                return res_endpoints_error_code

            if res_endpoints_code == 200 or res_endpoints_code == 201 :
                for objEndpoint in endpoints_data['items']:
                    Endpoints_Dict = {}
                    Endpoints_Dict['id'] = objEndpoint['id']
                    Endpoints_Dict['type'] = objEndpoint['type']
                    Endpoints_Dict['hostname'] = objEndpoint['hostname']

                    self._endpoints_list.append(Endpoints_Dict)
                    self._endpoints_ids.append(Endpoints_Dict['id'])
                
                try:
                    if endpoints_data['pages']['nextKey']:
                        self._request_page += 1
                        append_endpoints(endpoints_url, tenant_headers, endpoints_data['pages']['nextKey'])

                except:
                    pass

                return self._endpoints_list, self._endpoints_ids          

        return append_endpoints(endpoints_url, tenant_headers)