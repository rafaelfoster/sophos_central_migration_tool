import requests
from mwt import mwt

class Endpoint(object):

    headers = ""
    _request_page  = 1
    _endpoints_list = []
    _endpoints_ids  = []

    def setHeaders(self, headers):
        self.headers = headers

    def get_all(self, tenant_headers, endpoints_url):
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