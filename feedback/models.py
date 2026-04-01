import uuid
from django.conf import settings
from django.db import models


class FeedbackType(models.TextChoices):
    BUG_REPORT = 'bug_report', 'Bug Report'
    FEATURE_REQUEST = 'feature_request', 'Feature Request'
    GENERAL = 'general', 'General'
    COMPLAINT = 'complaint', 'Complaint'


class Feedback(models.Model):
    """User feedback/contact form submission."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    type = models.CharField(
        max_length=20,
        choices=FeedbackType.choices
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.type} - {self.user.email}'

