#!/usr/bin/env python3

from flask import request, session, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe


class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            # Check if username and password are provided
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                raise ValueError("Username and password are required.")
                
            new_user = User(
                username=username,
                password=password,  # using get() avoids KeyError
                image_url=data.get('image_url', ''),
                bio=data.get('bio', '')
            )
            db.session.add(new_user)
            db.session.commit()

            session['user_id'] = new_user.id
            return new_user.to_dict(), 201
        
        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 422
        except IntegrityError:
            db.session.rollback()
            return {"error": "Username already taken or invalid data"}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Unauthorized"}, 401
        user = User.query.get(user_id)
        return user.to_dict(), 200

class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(username=data.get('username')).first()
        if not user or not user.check_password(data.get('password')):
            return {"error": "Unauthorized"}, 401
        session['user_id'] = user.id
        return user.to_dict(), 200

class Logout(Resource):
    def delete(self):
        if 'user_id' not in session or session['user_id'] is None:
            return {"error": "Unauthorized"}, 401
        session.pop('user_id', None)
        return '', 204

class RecipeIndex(Resource):
    def get(self):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        recipes = Recipe.query.all()
        recipe_data = [{
            'id': recipe.id,
            'title': recipe.title,
            'instructions': recipe.instructions,
            'minutes_to_complete': recipe.minutes_to_complete,
            'user': {
                'id': recipe.user.id,
                'username': recipe.user.username
            }
        } for recipe in recipes]
        return jsonify(recipes=recipe_data), 200

    def post(self):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        data = request.get_json()
        try:
            new_recipe = Recipe(
                user_id=session['user_id'],
                title=data['title'],
                instructions=data['instructions'],
                minutes_to_complete=data.get('minutes_to_complete')
            )
            db.session.add(new_recipe)
            db.session.commit()
            return new_recipe.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Unprocessable Entity", "message": str(e)}), 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)