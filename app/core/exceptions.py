class MeetingNotesError(Exception):
    """Base exception for meeting notes processing"""
    pass

class AuthenticationError(MeetingNotesError):
    """Raised when authentication with Google Workspace fails"""
    pass

class WorkspaceAPIError(MeetingNotesError):
    """Raised when Google Workspace API call fails"""
    pass

class AudioProcessingError(MeetingNotesError):
    """Raised when ffmpeg audio extraction or transcoding fails"""
    pass

class StorageError(MeetingNotesError):
    """Raised when GCS upload or deletion fails"""
    pass

class GeminiInferenceError(MeetingNotesError):
    """Raised when Vertex AI Gemini inference or schema parsing fails"""
    pass

class SafetyBlockedError(MeetingNotesError):
    """Raised when Vertex AI Gemini model blocks content due to safety guardrails"""
    pass

