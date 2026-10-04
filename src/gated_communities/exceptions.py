"""Exceptions module."""


class MemberNotFoundError(Exception):
    """Raised when a member is not found."""
    pass


class DuplicateMemberError(Exception):
    """Raised when a duplicate member is found."""
    pass


class InvalidMemberDataError(Exception):
    """Raised when member data is invalid."""
    pass


class CommunityNotFoundError(Exception):
    """Raised when a community is not found."""
    pass
