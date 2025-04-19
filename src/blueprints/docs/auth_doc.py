from flask_restx import Namespace, fields, Resource
from src.services.auth_service import AuthService


api = Namespace("auth", description="Authentication related operations (Logon, user creation, etc)")

    
auth_model = api.model("Auth", {
    "username": fields.String(required=True, description="The username of the user"),
    "password": fields.String(required=True, description="The password of the user")
})

#Separate into two classes
@api.route('/login')
class AuthLoginDoc(Resource):
    #marshal_with will document the api call with the parameters provided as the model
    @api.expect(auth_model)
    @api.doc(security='basic')
    def post(self):
        """Authenticates the user by returning a valid JWT token"""
        return AuthService.login()

@api.route('/register')
class AuthRegisterDoc(Resource):
    @api.marshal_with(auth_model)
    @api.doc(security='jwt')
    def post(self):
        """Creates a new user, given that the authentication has the correct level of access"""
        return AuthService.register_user()