from pathlib import PurePath

# Static URI Variables
auth_uri = 'https://id.sophos.com/api/v2/oauth2/token'
whoami_uri = 'https://api.central.sophos.com/whoami/v1'
users_uri = '/common/v1/directory/users'
endpoints_uri = '/endpoint/v1/endpoints'
migrations_uri = '/endpoint/v1/migrations'

# Path locations
credentials_path = PurePath("/config/credentials.ini")
