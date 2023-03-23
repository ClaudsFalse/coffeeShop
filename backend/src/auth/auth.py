import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'fullstackclaud.eu.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'http://localhost:5000'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

def get_token_auth_header():
    '''
    This method attempts to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    returns the token part of the header
    '''
    if 'Authorization' not in request.headers:
       print("Authorisation header not found")
       raise AuthError({
           'code': 'auth_header_missing',
           'description': 'Authorization header not found.'
       }, 401)
    auth_header = request.headers['Authorization']
    header_parts = auth_header.split(' ')
    # checking that we are using a bearer keyword
    # and that our header has 2 parts (bearer keyword and token)
    if len(header_parts) != 2:
        print("Authorisation header is malformed")
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header is malformed.'
            }, 401)
    elif header_parts[0].lower() != 'bearer':
        print("Authorisation header is missing the bearer keyword")
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must have bearer keyword'
            }, 401)
    return header_parts[1]

def check_permissions(permission, payload):
    '''
    This method checks the token for the required permissions. 
    '''

    # check if the user has a role attached (permission is in the payload)
    if payload.get('permissions'):
        user_permissions = payload.get('permissions')
        # check if the user has the right permissions for this request
        if permission not in user_permissions:
            raise AuthError({
                'code': 'invalid_permissions',
                'descriptions': 'the user does not have permission for this request'
            }, 403)
        else:
            return True
    else:
        # if the user doesn't have a role at all: permission not in the payload
        raise AuthError({
            'code': 'invalid_permissions',
            'descriptions': 'iser does not have a role'
        }, 401)

def verify_decode_jwt(token):
    '''
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload
    '''
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        print("Authorisation is malformed - kid not in header")
        raise AuthError(
            {
                'code': 'invalid_header',
                'description': 'Authorization malformed.'
            }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(token,
                                 rsa_key,
                                 algorithms=ALGORITHMS,
                                 audience=API_AUDIENCE,
                                 issuer='https://' + AUTH0_DOMAIN + '/')

            return payload

        except jwt.ExpiredSignatureError:
            print("Your token has expired")
            raise AuthError(
                {
                    'code': 'token_expired',
                    'description': 'Token expired.'
                }, 401)

        except jwt.JWTClaimsError:
            print("Incorrect claims. Please, check the audience and issuer.")
            raise AuthError(
                {
                    'code':
                    'invalid_claims',
                    'description':
                    'Incorrect claims. Please, check the audience and issuer.'
                }, 401)
        except Exception as e:
            print(e)
            
            raise AuthError(
                {
                    'code': 'invalid_header',
                    'description': 'Unable to parse authentication token.'
                }, 400)
    raise AuthError(
        {
            'code': 'invalid_header',
            'description': 'Unable to find the appropriate key.'
        }, 400)


def requires_auth(permission=''):
    '''
     @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
    
    '''
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator