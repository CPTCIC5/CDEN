"""SQLAdmin-based back-office (Django-admin style) for CDEN.

Mounted at /admin. Login uses the seeded admin account
(admin@cden.demo). Only users with role 'admin' can get in.
"""
from sqladmin import Admin, ModelView, BaseView, expose
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import HTMLResponse

from db.models import SessionLocal, User, FounderProfile, MentorProfile, FundingProgram, MentorInvite, Event
from utils.auth import SECRET_KEY
from utils.constants import ROLE_ADMIN
from utils.invites import create_mentor_invite, invite_link


class AdminAuth(AuthenticationBackend):
    """Gate the admin panel behind the existing admin User accounts."""

    async def login(self, request: Request) -> bool:
        form = await request.form()
        email, password = form.get("username"), form.get("password")
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
        finally:
            db.close()
        if user and user.role == ROLE_ADMIN and user.verify_password(password):
            request.session.update({"admin_email": user.email})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "admin_email" in request.session


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    column_list = [User.id, User.email, User.role, User.is_verified, User.is_active]
    column_searchable_list = [User.email]
    column_sortable_list = [User.id, User.email, User.role]
    # Never expose or edit the password hash through the panel
    column_details_exclude_list = [User.password]
    form_excluded_columns = [User.password, User.profile, User.founder_profile]


class FundingProgramAdmin(ModelView, model=FundingProgram):
    name = "Funding Program"
    name_plural = "Funding Programs"
    column_list = [
        FundingProgram.id, FundingProgram.name, FundingProgram.provider,
        FundingProgram.provider_type, FundingProgram.accessibility_focused,
        FundingProgram.is_active,
    ]
    column_searchable_list = [FundingProgram.name, FundingProgram.provider]
    column_sortable_list = [FundingProgram.id, FundingProgram.name, FundingProgram.is_active]


class MentorProfileAdmin(ModelView, model=MentorProfile):
    name = "Mentor"
    name_plural = "Mentors"
    column_list = [
        MentorProfile.id, MentorProfile.full_name, MentorProfile.availability,
        MentorProfile.is_accepting, MentorProfile.is_onboarded,
    ]
    column_searchable_list = [MentorProfile.full_name]


class FounderProfileAdmin(ModelView, model=FounderProfile):
    name = "Founder"
    name_plural = "Founders"
    column_list = [
        FounderProfile.id, FounderProfile.business_name, FounderProfile.province,
        FounderProfile.business_stage, FounderProfile.is_onboarded,
    ]
    column_searchable_list = [FounderProfile.business_name]


class EventAdmin(ModelView, model=Event):
    name = "Event"
    name_plural = "Events"
    column_list = [
        Event.id, Event.title, Event.city, Event.start_at, Event.is_active,
    ]
    column_searchable_list = [Event.title, Event.city]
    column_sortable_list = [Event.id, Event.title, Event.start_at]


class MentorInviteAdmin(ModelView, model=MentorInvite):
    name = "Mentor Invite"
    name_plural = "Mentor Invites"
    column_list = [
        MentorInvite.id, MentorInvite.email, MentorInvite.status,
        MentorInvite.created_at, MentorInvite.expires_at,
    ]
    column_searchable_list = [MentorInvite.email]


def _invite_page(message_html: str = "") -> HTMLResponse:
    """Minimal standalone page with the invite form (kept template-free for leanness)."""
    return HTMLResponse(f"""
    <html>
    <head><title>Invite a Mentor</title>
    <style>
      body {{ font-family: system-ui, sans-serif; max-width: 560px; margin: 60px auto; padding: 0 20px; }}
      input[type=email] {{ width: 100%; padding: 10px; font-size: 16px; box-sizing: border-box; }}
      button {{ margin-top: 12px; padding: 10px 18px; font-size: 16px; cursor: pointer; }}
      .msg {{ margin: 16px 0; padding: 12px; border-radius: 6px; }}
      .ok {{ background: #e6f4ea; }} .err {{ background: #fce8e6; }}
      a {{ color: #1a73e8; }} code {{ word-break: break-all; }}
    </style></head>
    <body>
      <h2>Invite a Mentor</h2>
      <p>Enter the prospective mentor's email. They'll receive a tokenized link to join and set up their profile.</p>
      {message_html}
      <form method="post" action="/admin/invite-mentor">
        <input type="email" name="email" placeholder="mentor@example.com" required />
        <button type="submit">Send invite</button>
      </form>
      <p style="margin-top:24px;"><a href="/admin">&larr; Back to admin</a></p>
    </body>
    </html>
    """)


class MentorInviteActionView(BaseView):
    name = "Invite a Mentor"
    icon = "fa-solid fa-paper-plane"

    @expose("/invite-mentor", methods=["GET", "POST"])
    async def invite_mentor(self, request: Request):
        if request.method != "POST":
            return _invite_page()

        form = await request.form()
        email = (form.get("email") or "").strip()
        if not email:
            return _invite_page('<div class="msg err">Please enter an email.</div>')

        db = SessionLocal()
        try:
            invite, error = create_mentor_invite(db, email)
        finally:
            db.close()

        if error:
            return _invite_page(f'<div class="msg err">{error}</div>')

        link = invite_link(invite.token)
        return _invite_page(
            f'<div class="msg ok">Invite sent to <b>{invite.email}</b>.<br>'
            f'Invite link:<br><code><a href="{link}">{link}</a></code></div>'
        )


def setup_admin(app, engine):
    """Attach the admin panel to the FastAPI app at /admin."""
    admin = Admin(app, engine, authentication_backend=AdminAuth(SECRET_KEY))
    admin.add_view(UserAdmin)
    admin.add_view(FounderProfileAdmin)
    admin.add_view(MentorProfileAdmin)
    admin.add_view(FundingProgramAdmin)
    admin.add_view(EventAdmin)
    admin.add_view(MentorInviteAdmin)
    admin.add_view(MentorInviteActionView)
    return admin
