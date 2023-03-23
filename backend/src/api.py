import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)
db_drop_and_create_all()

# ROUTES
app.app_context().push()

@app.route('/drinks', methods=['GET'])
def get_drinks():
    '''
    This endpoint should be a public endpoitn 
    it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
    '''
    # try to query the db for all drinks
    # and return 200 if successful 
    try:
        return jsonify({
            'success': True,
            'drinks': [drink.short() for drink in Drink.query.all()]
        }), 200
    except Exception as e:
        print(e)
        # if unsuccessful, return server error
        return jsonify({
            'success':False,
            'error': "There was an error retrieving the drinks"
        }), 500



@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    '''
     it should require the 'get:drinks-detail' permission
    it should contain the drink.long() data representation
    returns status code 200 and json 
    {"success": True, 
    "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
    '''
    try:
        return jsonify({
            'success': True,
            'drinks': [drink.long() for drink in Drink.query.all()]
        }), 200
    except Exception as e:
        print(e)
        return jsonify({
            'sucess': False,
            'error': "An error occured"

        }), 500


   
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def drinks(payload):
    """
    This method creates a new row in the drinks table
    It should require the post:drinks permission
    It should contain the drink.long() data representation
    it should return status code 200 and json {
        "success": True, 
        "drinks": drink} where drink an array containing only 
    the newly created drink or appropriate status code indicating reason for failure
    """

    # data = dict(request.form or request.json or request.data)
    data = request.get_json()
    
    try:
        recipe = data['recipe']
        drink = Drink()
        drink.title = data['title']
        drink.recipe = json.dumps(recipe)
        drink.insert()
        return jsonify({
            'success': True, 
            'drink': drink.long()
            }), 200
    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'error': "An error occurred"
        }), 500


@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drinks(payload, id):
    '''
         <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
    '''
    try:
        data = request.get_json()
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        # if we found a drink with the specified if
        if drink:
            title = data.get('title')
            recipe = data.get('recipe')

            if title:
                drink.title = title
            if recipe:
                drink.recipe = recipe
            drink.update()
            return jsonify({
                'success': True,
                'drinks': [drink.long()]
            }), 200
        else:
            # if there isn't a drink in the db with the queried id, 
            # throw a not found error 
            abort(404)
    except Exception as e:
        print(e)
        # if we incur in a server error, throw error
        abort(500)
    
@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if not drink:
        # if we can't find a drink with that id, throw 404 error
        abort(404)

    try:
        # try to delete drink from db
        drink.delete()
    except Exception as e:
        # print exception to debug if it fails
        print(e)
        abort(500)

    return jsonify({'success': True, 'delete': id}), 200



# Error Handling
'''
Example error handling for unprocessable entity
'''

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'Not found'

    }), 404

@app.errorhandler(400)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "could not process request"
    }), 400

@app.errorhandler(400)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "internal server error"
    }), 500


@app.errorhandler(AuthError)
def handle_auth_error(ex):

    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response