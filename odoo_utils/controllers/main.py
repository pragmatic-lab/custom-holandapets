
from odoo import http, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.auth_signup.models.res_users import SignupError


class AuthSignupHomeExt(AuthSignupHome):
    
    def do_signup(self, qcontext):
        User = request.env["res.users"].sudo().with_context(active_test=False)
        if not qcontext.get("token") and qcontext.get("login") and User.search(User._get_login_domain(qcontext.get("login")), limit=1):
            raise SignupError(_('Authentication Failed.')) 
        return super(AuthSignupHomeExt, self).do_signup(qcontext)