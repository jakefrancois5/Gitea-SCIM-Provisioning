import requests
import json
import settings

TOKEN = settings.TOKEN
BASE_URL = settings.BASE_URL

DEFAULT_TEAM_NEW_ORG_PERMISSIONS = settings.DEFAULT_TEAM_NEW_ORG_PERMISSIONS


class GiteaUser:
    def __init__(self, **kwargs) -> None:
        self.id = kwargs.get('username')
        self.username = kwargs.get('username')
        self.login_name = kwargs.get('login_name')
        self.full_name = kwargs.get('full_name')
        self.email = kwargs.get('email')
        self.avatar_url = kwargs.get('avatar_url')
        self.language = kwargs.get('language')
        self.is_admin = kwargs.get('is_admin')
        self.last_login = kwargs.get('last_login')
        self.created = kwargs.get('created')
        self.restricted = kwargs.get('restricted')
        self.active = kwargs.get('active')
        self.prohibit_login = kwargs.get('prohibit_login')
        self.location = kwargs.get('location')
        self.website = kwargs.get('website')
        self.description = kwargs.get('description')
        self.visibility = kwargs.get('visibility')
        self.source_id = kwargs.get('source_id')

    def serialize(self):
        if self.id:
            return {
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                ],
                "id": self.id,
                "userName": self.username,
                "emails": [
                    {
                        "primary": True,
                        "value": self.email,
                        "type": "work",
                    }
                ],
                "description": self.description,
                "active": self.active,
                "urn:ietf:params:scim:schemas:extension:Gitea:2.0:User": {
                        "full_name": self.full_name,
                        "visibility": self.visibility,
                        "location": self.location,
                        'source_id': self.source_id
                },
                "meta": {"resourceType": "User"},
            }
        return self.not_found()

    def not_found(self):
        return None


class GiteaOrg:
    def __init__(self, **kwargs) -> None:
        self.id = kwargs.get('username')
        self.username = kwargs.get('username')
        self.full_name = kwargs.get('full_name')
        self.avatar_url = kwargs.get('avatar_url')
        self.created = kwargs.get('created')
        self.location = kwargs.get('location')
        self.website = kwargs.get('website')
        self.description = kwargs.get('description')
        self.visibility = kwargs.get('visibility')
        self.members = kwargs.get('members')

    def serialize(self):
        if self.id:
            return {
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:Group",
                ],
                "id": self.id,
                "displayName": self.username,
                "members": self.members,
                "description": self.description,
                "urn:ietf:params:scim:schemas:extension:Gitea:2.0:Group": {
                        "full_name": self.full_name,
                        "visibility": self.visibility,
                        "location": self.location,
                },
                "meta": {"resourceType": "Group"},
            }
        return self.not_found()

    def not_found(self):
        return None


class GiteaAPI:
    def __init__(self, base_url, token) -> None:
        self._HEADERS = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'token {token}'
        }
        self.base_url = base_url

    def get_user(self, username):
        r = requests.get(f'{self.base_url}users/{username}', headers=self._HEADERS)
        return r

    def get_users(self, page=None, limit=None):
        params = {}
        if page:
            params['page'] = page
        if limit:
            params['limit'] = limit
        url = f'{self.base_url}admin/users'
        r = requests.get(url, params=params, headers=self._HEADERS) # limit = Page Size | page = number of results to return (1-based) | uid = ID of the user to search for | no query returns all
        # Page = startindex | limit = count
        return r

    def create_user(self, email: str, full_name: str, username: str, password: str, login_name: str, source_id: int, must_change_password=False, send_notify=False, visibility='limited'):  # Email is mandatory ! FIX
        body = {
            "email": email,
            "full_name": full_name,
            "login_name": login_name,
            "must_change_password": must_change_password,
            "password": password,
            "send_notify": send_notify,
            "source_id": source_id,
            "username": username,
            "visibility": visibility,
        }
        r = requests.post(f'{self.base_url}admin/users', data=json.dumps(body), headers=self._HEADERS)
        return r

    def edit_user(self, username: str, **kwargs):
        body = kwargs
        r = requests.patch(f'{self.base_url}admin/users/{username}', data=json.dumps(body), headers=self._HEADERS)
        return r

    def delete_user(self, username: str):
        r = requests.delete(f'{self.base_url}admin/users/{username}', headers=self._HEADERS)
        return r

    def get_orgs(self, page=None, limit=None):
        params = {}
        if page:
            params['page'] = page
        if limit:
            params['limit'] = limit
        url = f'{self.base_url}orgs'
        r = requests.get(url, params=params, headers=self._HEADERS) # limit = Page Size | page = number of results to return (1-based) | uid = ID of the user to search for | no query returns all
        # Page = startindex | limit = count
        return r
    
    def get_org(self, org: str):
        r = requests.get(f'{self.base_url}orgs/{org}', headers=self._HEADERS)
        return r

    def get_org_members(self, org: str):
        r = requests.get(f'{self.base_url}orgs/{org}/members', headers=self._HEADERS)
        return r

    def get_org_teams(self, org: str):
        r = requests.get(f'{self.base_url}orgs/{org}/teams', headers=self._HEADERS)
        return r

    def create_team(self, org: str, name: str, description: str, can_create_org_repo: bool, includes_all_repositories: bool, permission: str, units: list, units_map=None):
        body = {
            "name": name,
            "description": description,
            "can_create_org_repo": can_create_org_repo,
            "includes_all_repositories": includes_all_repositories,
            "permission": permission,  # read,write,admin
            "units": units,
            "units_map": units_map,
        }
        r = requests.post(f'{self.base_url}orgs/{org}/teams', data=json.dumps(body), headers=self._HEADERS)
        return r

    def add_team_member(self, team_id: int, username: str):
        r = requests.put(f'{self.base_url}teams/{team_id}/members/{username}', headers=self._HEADERS)
        return r

    def remove_team_member(self, team_id: int, username: str):
        r = requests.delete(f'{self.base_url}teams/{team_id}/members/{username}', headers=self._HEADERS)
        return r

    def add_org_member(self, org: str, username: str):
        organization = self.get_org_teams(org)
        if organization.status_code == 200:
            for team in organization.json():
                if team['name'] == 'Default':
                    org_team_id = team['id']
                    return self.add_team_member(org_team_id, username)
            else:
                units = DEFAULT_TEAM_NEW_ORG_PERMISSIONS
                r = g.create_team(org, 'Default', 'Default group for SCIM provisioning', False, True, 'read', units)  # May need to revisit
                if r.status_code == 201:
                    org_team_id = r.json()['id']
                    return self.add_team_member(org_team_id, username)
                else:
                    return None

    def create_org(self, username, visibility, full_name=None, description=None, location=None, website=None):
        body = {
            "username": username,
            "visibility": visibility,
            "full_name": full_name,
            "description": description,
            "location": location,
            "website": website,
        }
        r = requests.post(f'{self.base_url}orgs', data=json.dumps(body), headers=self._HEADERS)
        return r

    def edit_org(self, org: str, **kwargs):
        body = kwargs
        r = requests.patch(f'{self.base_url}orgs/{org}', data=json.dumps(body), headers=self._HEADERS)
        return r



class GiteaSCIMWrapper(GiteaAPI):  # Build in validation
    def __init__(self, base_url, token) -> None:
        super().__init__(base_url, token)

    def scim_create_user(self, email: str, full_name: str, username: str, password: str, login_name: str, source_id: int, must_change_password=False, send_notify=False, visibility='limited'):
        create_response = self.create_user(
            email=email,
            full_name=full_name,
            username=username,
            login_name=login_name,
            source_id=source_id,
            password=password
        ) # review
        if create_response.status_code == 201:
            created_user = self.get_user(username=username).json()
            return GiteaUser(**created_user).serialize()
    
    def scim_edit_user(self, username: str, **kwargs):
        edit_response = self.edit_user(username, **kwargs)
        if edit_response.status_code == 201:
            edited_user = self.G.get_user(username=username).json()
            return GiteaUser(**edited_user).serialize()

    def scim_get_user(self, username: str):
        user_response = self.get_user(username)
        if user_response.status_code == 200:
            user = user_response.json()
            return GiteaUser(**user).serialize()

    def scim_get_users(self, page=None, limit=None):
        get_users_response = self.get_users(page, limit)
        if get_users_response.status_code == 200:
            users = get_users_response.json()
            return [GiteaUser(**g).serialize() for g in users]

    def scim_create_org(self, username, visibility, full_name=None, description=None, location=None, website=None):
        create_response = self.create_org(username=username, visibility=visibility, full_name=full_name, description=description, location=location, website=website)
        if create_response.status_code == 201:
            created_org = create_response.json()
            units =  DEFAULT_TEAM_NEW_ORG_PERMISSIONS
            self.create_team(username, 'Default', 'Default group created by SCIM provisioning', False, True, 'read', units)
            return GiteaOrg(**created_org).serialize()

    def scim_get_org(self, org: str):
        org_response = self.get_org(org=org)
        if org_response.status_code == 200:
            org_json = org_response.json()
            return GiteaOrg(**org_json).serialize()

    def scim_get_orgs(self, page=None, limit=None):
        get_orgs_response = self.get_orgs(page, limit)
        if get_orgs_response.status_code == 200:
            orgs = get_orgs_response.json()
            return [GiteaOrg(**o).serialize() for o in orgs]


    def _get_org_default_team(self, org: str, create=True):
        organization = self.get_org_teams(org)
        if organization.status_code == 200:
            for team in organization.json():
                if team['name'] == 'Default':
                    return team['id']
            else:
                if create:
                    units =  [ "repo.code", "repo.issues", "repo.ext_issues", "repo.wiki", "repo.pulls", "repo.releases", "repo.projects", "repo.ext_wiki" ]
                    r = self.create_team(org, 'Default', 'Default group created by SCIM provisioning', False, True, 'read', units)
                    if r.status_code == 201:
                        return r.json()['id']

    def scim_add_org_member(self, org: str, member: str):
        org_default_team_id = self._get_org_default_team(org, create=True)
        if org_default_team_id:
            add_member_response = self.add_team_member(org_default_team_id, member)
            if add_member_response.status_code == 201:
                return self.scim_get_org(org=org)

    def scim_remove_org_member(self, org: str, member):
        get_org_teams_response = self.get_org_teams(org)
        if get_org_teams_response.status_code == 200:
            for team in get_org_teams_response.json():
                team_id = team['id']
                self.remove_team_member(team_id, member)
        return self.scim_get_org(org=org)


    def scim_edit_org(self, org: str, **kwargs):
        edit_org_response = self.edit_org(org, **kwargs)
        if edit_org_response.status_code == 200:
            org = edit_org_response.json()
            return GiteaOrg(**org).serialize()

    def scim_get_org_members(self, org: str):  # Don't need with MS? - Might need for intial cycle vs delta
        get_members_response = self.get_org_members(org)
        if get_members_response.status_code == 200:
            return get_members_response.json()


# Check what is needed for return values for efficiency


if __name__ == '__main__':
    g = GiteaSCIMWrapper(BASE_URL, TOKEN)
    t = g.scim_get_org('Gitea', members=True)
    print(t)

    # o = g.add_org_member('testorg', 'renovate')
    # print(o.status_code)

    # o = g.get_org_members('testorg')
    # print(o.json())
