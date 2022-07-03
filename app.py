from flask import Flask, jsonify, abort, make_response, request
from functools import wraps
from gitea import BASE_URL, TOKEN, GiteaSCIMWrapper
import helpers

G = GiteaSCIMWrapper(BASE_URL, TOKEN)

def create_app():
    """
    Instantiate Flask

    Implemented as a factory method to avoid a circular import error.
    """
    app = Flask(__name__)
    # app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/scim"
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # db.init_app(app)
    return app


app = create_app()


def auth_required(func):
    """Flask decorator to require the presence of a valid Authorization header."""

    @wraps(func)
    def check_auth(*args, **kwargs):
        if request.headers["Authorization"].split("Bearer ")[1] == "123456789":
            return func(*args, **kwargs)
        else:
            return make_response(jsonify({"error": "Unauthorized"}), 403)

    return check_auth


@app.route("/scim/v2/Users", methods=["GET"])
@auth_required
def get_users():
    """Get SCIM Users"""
    start_index = 1
    count = None
    users = None

    if "start_index" in request.args:
        start_index = int(request.args["startIndex"])

    if "count" in request.args:
        count = int(request.args["count"])

    if "filter" in request.args:
        single_filter = request.args["filter"].split(" ")
        filter_value = single_filter[2].strip('"')

        users = G.scim_get_user(username=filter_value)

        if not users:
            users = []
        else:
            users = [users]

    else:
        users = G.scim_get_users(page=start_index, limit=count)

    serialized_users = users

    return make_response(
        jsonify(
            {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": len(users),
                "startIndex": start_index,
                "itemsPerPage": len(users),
                "Resources": serialized_users,
            }
        ),
        200,
    )


@app.route("/scim/v2/Users/<string:user_id>", methods=["GET"])
@auth_required
def get_user(user_id):
    """Get SCIM User"""
    user = G.scim_get_user(username=user_id)
    if not user:
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
                    "detail": "User not found",
                    "status": "404",
                }
            ),
            404,
        )
    return jsonify(user)


@app.route("/scim/v2/Users", methods=["POST"])
@auth_required
def create_user():
    """Create SCIM User"""
    active = request.json.get("active")
    description = request.json.get("description")
    custom_Attributes = request.json.get("urn:ietf:params:scim:schemas:extension:Gitea:2.0:User")
    full_name = custom_Attributes.get("full_name")
    password = request.json.get("password", helpers.generate_password())
    userName = request.json.get("userName")
    source_id = custom_Attributes.get("source_id") # HMM
    visibility = custom_Attributes.get("visibility")
    email = request.json.get('emails')[0]['value']
    # location = request.json.get("location")
    print(request.json)

    existing_user = G.get_user(username=userName)

    if existing_user.status_code != 404:  ## Need specific codes & messages
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
                    "detail": "User already exists in the database.",
                    "status": 409,
                }
            ),
            409,
        )
    else:
        create_user = G.scim_create_user(email=email, full_name=full_name, username=userName, login_name=userName, source_id=source_id, visibility=visibility, password=password)
        return make_response(jsonify(create_user), 201)
        # db.session.add(user)

        # if groups:
        #     for group in groups:
        #         existing_group = Group.query.get(group["value"])

        #         if existing_group:
        #             existing_group.users.append(user)
        #         else:
        #             new_group = Group(displayName=group["displayName"])
        #             # db.session.add(new_group)
        #             new_group.users.append(user)

        # db.session.commit()


# @app.route("/scim/v2/Users/<string:user_id>", methods=["PUT"])
# @auth_required
# def update_user(user_id):
#     """Update SCIM User"""
#     user = G.get_user(username=user_id).json()
#     user = GiteaUser(**user)

#     if not user:
#         return make_response(
#             jsonify(
#                 {
#                     "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
#                     "detail": "User not found",
#                     "status": 404,
#                 }
#             ),
#             404,
#         )
#     else:
#         groups = request.json.get("groups")
#         active = request.json.get("active")
#         displayName = request.json.get("displayName")
#         emails = request.json.get("emails")
#         externalId = request.json.get("externalId")
#         locale = request.json.get("locale")
#         name = request.json.get("name")
#         # user.familyName = request.json["name"].get("familyName")
#         # user.middleName = request.json["name"].get("middleName")
#         # user.givenName = request.json["name"].get("givenName")
#         password = request.json.get("password")
#         schemas = request.json.get("schemas")
#         userName = request.json.get("userName")

#         resp = G.edit_user(userName, active=active, full_name=displayName, login_name=userName, email=emails[0]['value'], source_id=2)
#         print(resp.json())
#         updated_user = G.get_user(username=userName).json()
#         updated_user = GiteaUser(**updated_user)

#         # db.session.commit()
#         return make_response(jsonify(updated_user.serialize()), 200)


@app.route("/scim/v2/Users/<string:user_id>", methods=["PATCH"])
@auth_required
def patch_user(user_id):
    """PATCH SCIM User"""
    updates = {}
    for operation in request.json["Operations"]:  # Really need a consistent attribute listing to re-use
        print(operation)
        if operation['path'] == 'urn:ietf:params:scim:schemas:extension:Gitea:2.0:User:full_name':
            updates['full_name'] = operation['value']
        if operation['path'] == 'description':
            updates['description'] = operation['value']
        if operation['path'] == 'urn:ietf:params:scim:schemas:extension:Gitea:2.0:User:visibility':
            updates['visibility'] = operation['value']
        if operation['path'] == 'urn:ietf:params:scim:schemas:extension:Gitea:2.0:User:location':
            updates['location'] = operation['value']
        if operation['path'] == 'active':
            if operation['value'] == 'False':
                updates['active'] = False
            elif operation['value'] == 'True':
                updates['active'] = True
        if operation['path'] == 'emails[type eq "work"].value':
            updates['email'] = operation['value']
    updated_user = G.scim_edit_user(user_id, login_name=user_id, **updates)
    return make_response(jsonify(updated_user), 200)
    # return make_response("", 204)


@app.route("/scim/v2/Users/<string:user_id>", methods=["DELETE"])
@auth_required
def delete_user(user_id):
    """Delete SCIM User"""
    G.delete_user(username=user_id)
    return make_response("", 204)


@app.route("/scim/v2/Groups", methods=["GET"])
@auth_required
def get_groups():
    """Get SCIM Groups"""
    start_index = 1
    count = None
    groups = None

    if "start_index" in request.args:
        start_index = int(request.args["startIndex"])

    if "count" in request.args:
        count = int(request.args["count"])

    if "filter" in request.args:
        single_filter = request.args["filter"].split(" ")
        filter_value = single_filter[2].strip('"')

        groups = G.scim_get_org(org=filter_value)

        if not groups:
            groups = []
        else:
            groups = [groups]

    else:
        groups = G.scim_get_orgs(page=start_index, limit=count)

    serialized_groups = groups


    return make_response(
    jsonify(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": len(groups),
            "startIndex": start_index,
            "itemsPerPage": len(groups),
            "Resources": serialized_groups,
        }
    ),
    200,
)


@app.route("/scim/v2/Groups/<string:group_id>", methods=["GET"])
# @auth_required
def get_group(group_id):
    """Get SCIM Group"""
    group = G.scim_get_org(org=group_id)
    if not group:
        abort(404)
    return jsonify(group)


@app.route("/scim/v2/Groups", methods=["POST"])
@auth_required
def create_group():
    """Create SCIM Group"""
    # username = request.json["urn:ietf:params:scim:schemas:extension:Gitea:2.0:Group:organization_name"]
    username = request.json["displayName"]
    description = request.json.get('description')
    # members = request.json["members"]
    custom_attributes = request.json.get('urn:ietf:params:scim:schemas:extension:Gitea:2.0:Group')
    full_name = custom_attributes.get('full_name')
    visiblity = custom_attributes.get('visibility')
    # print(request.json)

    try:
        group = G.scim_create_org(username=username, full_name=full_name, description=description, visibility=visiblity)
        return make_response(jsonify(group), 201)
    except Exception as e:
        return str(e)


@app.route("/scim/v2/Groups/<string:group_id>", methods=["PATCH", "PUT"])
@auth_required
def update_group(group_id):
    """
    Update SCIM Group

    Accounts for the different requests sent by Okta depending
    on if the group was created via template or app wizard integration.
    """
    print(request.json)
    group = None
    members_to_add = []
    members_to_remove = []
    updates = {}
    for operation in request.json["Operations"]:
        action = operation.get('op')
        if operation["path"] == 'members':
            if action == 'Add':
                members_to_add = operation["value"]
            elif action == 'Remove':
                members_to_remove = operation["value"]
        if operation["path"] == 'description':
            updates['description'] = operation["value"]
        if operation["path"] == 'urn:ietf:params:scim:schemas:extension:Gitea:2.0:Group:visibility':
            updates['visibility'] = operation["value"]
        if operation["path"] == 'urn:ietf:params:scim:schemas:extension:Gitea:2.0:Group:full_name':
            updates['full_name'] = operation["value"]
        if operation["op"] == "replace":
            return make_response("", 204)

    if updates:
        group = G.scim_edit_org(org=group_id, **updates)

    for member in members_to_add:
        existing_user = G.get_user(username=member["value"])
        if existing_user:
            group = G.scim_add_org_member(org=group_id, member=member["value"])
    for member in members_to_remove:
        existing_user = G.get_user(username=member["value"])
        if existing_user:
            group = G.scim_remove_org_member(org=group_id, member=member["value"])

    if not group:
        group = G.scim_get_org(org=group_id)

    return make_response(jsonify(group), 200)


# @app.route("/scim/v2/Groups/<string:group_id>", methods=["DELETE"])
# @auth_required
# def delete_group(group_id):
#     """Delete SCIM Group"""
#     group = Group.query.get(group_id)
#     db.session.delete(group)
#     db.session.commit()
#     return make_response("", 204)


# @app.route("/scim/v2/Schemas", methods=["GET"])
# @auth_required
# def get_schema():
#     user_schema = {
#         "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Schema"],
#         "id" : "urn:ietf:params:scim:schemas:core:2.0:User",
#         "name" : "User",
#         "description" : "User Account",
#         "attributes" : [
#         {
#             "name" : "username",
#             "type" : "string",
#             "multiValued" : False,
#             "description" : """Unique identifier for the User, typically
#     used by the user to directly authenticate to the service provider.
#     Each User MUST include a non-empty userName value.  This identifier
#     MUST be unique across the service provider's entire set of Users.
#     REQUIRED.""",
#             "required" : True,
#             "caseExact" : False,
#             "mutability" : "readWrite",
#             "returned" : "default",
#             "uniqueness" : "server"
#         },
#         {
#             "name" : "email",
#             "type" : "string",
#             "multiValued" : False,
#             "description" : "Email Address",
#             "required" : True,
#             "caseExact" : False,
#             "mutability" : "readWrite",
#             "returned" : "default",
#             "uniqueness" : "None"
#         },
#         {
#             "name" : "full_name",
#             "type" : "string",
#             "multiValued" : False,
#             "description" : "Full Name",
#             "required" : False,
#             "caseExact" : True,
#             "mutability" : "readWrite",
#             "returned" : "default",
#             "uniqueness" : "None"
#         },
#         {
#             "name" : "active",
#             "type" : "boolean",
#             "multiValued" : False,
#             "description" : "Active Status",
#             "required" : False,
#             "caseExact" : False,
#             "mutability" : "readWrite",
#             "returned" : "default",
#             "uniqueness" : "None"
#         },
#         ],
#         "meta" : {
#         "resourceType" : "Schema",
#         "location" :
#             "/v2/Schemas/urn:ietf:params:scim:schemas:core:2.0:User"
#         }
#     }
#     schemas = [user_schema]
#     return make_response(
#         jsonify(
#             {
#                 "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
#                 "totalResults": len(schemas),
#                 "startIndex": 1,
#                 "itemsPerPage": len(schemas),
#                 "Resources": schemas,
#             }
#         ),
#         200,
#     )
#     # return jsonify(user_schema, 200)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
