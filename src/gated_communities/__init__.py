"""Gated Communities - Tiered access control for community platforms."""

__version__ = "0.1.0"

# Re-export commonly used names at the package level
from .models import Community, Member, Post, Comment, Event, AuditLog, ModerationItem
from .models.member import Member as MemberModel
from .models.moderation import ModerationItem as ModerationItemModel
from .models.user import User
from .models.post import Post as PostModel
from .models.invitation import Invitation, InvitationCreate, InvitationStatus, InvitationUpdate
from .services.community_service import CommunityService
from .services.member_service import MemberService
from .services.access_service import AccessService
from .services.analytics_service import AnalyticsService
from .services.comment_service import CommentService
from .services.event_service import EventService
from .services.message_service import MessageService
from .services.post_service import PostService
from .services.invitation_service import InvitationService
from .services.moderation_service import ModerationService
from .access_control import AccessLevel, AccessDeniedError, AccessAlreadyGrantedError, AccessNotFoundError
from .access import AccessController, AccessRequest, AccessDecision
from .member import MemberRole, MemberStatus
from .exceptions import (
    MemberNotFoundError,
    DuplicateMemberError,
    InvalidMemberDataError,
    CommunityNotFoundError,
)


class GatedCommunitiesClient:
    """Client for interacting with the Gated Communities API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.communities = _CommunityClient(self)
        self.members = _MemberClient(self)


class _CommunityClient:
    def __init__(self, client: GatedCommunitiesClient):
        self._client = client

    def create(self, **kwargs) -> dict:
        return {"id": "comm-001", **kwargs}

    def get(self, community_id: str) -> dict:
        return {"id": community_id}

    def list(self) -> list[dict]:
        return []

    def update(self, community_id: str, **kwargs) -> dict:
        return {"id": community_id, **kwargs}

    def delete(self, community_id: str) -> dict:
        return {"id": community_id, "deleted": True}


class _MemberClient:
    def __init__(self, client: GatedCommunitiesClient):
        self._client = client

    def add(self, community_id: str, **kwargs) -> dict:
        return {"community_id": community_id, **kwargs}

    def remove(self, community_id: str, member_id: str) -> dict:
        return {"community_id": community_id, "member_id": member_id, "removed": True}
