from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    """Additional data for a Django auth User.

    This model is optional for your current views, but provides a place
    to store user-related data without changing the built-in User model.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=150, blank=True)
    # Optional fields added for user profile; migrations required after change
    full_name = models.CharField(max_length=255, blank=True, null=True)
    enrollment = models.CharField(max_length=100, blank=True, null=True)
    semester = models.CharField(max_length=50, blank=True, null=True, help_text="User's semester (e.g., semester1, semester2)")
    avatar_url = models.URLField(blank=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.display_name or self.user.get_username()


# Auto-create a Profile whenever a User is created
from django.db.models.signals import post_save  # noqa: E402
from django.dispatch import receiver  # noqa: E402


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance: User, created: bool, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # Ensure existing profile gets its updated_at touched
        Profile.objects.get_or_create(user=instance)


class UnlockSlot(models.Model):
    """A date (slot) that an admin can create and users can book."""
    date = models.DateField()
    subject = models.CharField(max_length=255, blank=True, null=True, help_text="Subject for this exam slot (optional)")
    start_time = models.TimeField(blank=True, null=True, help_text="Start time for this exam slot")
    end_time = models.TimeField(blank=True, null=True, help_text="End time for this exam slot")
    capacity = models.IntegerField(default=0, help_text="Maximum number of students (0 = unlimited)")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date']

    def __str__(self) -> str:
        return f"Unlock on {self.date}"
    
    def get_available_capacity(self):
        """Get remaining capacity for this slot"""
        if self.capacity == 0:
            return None  # Unlimited
        booked_count = self.bookings.count()
        return max(0, self.capacity - booked_count)


class UnlockBooking(models.Model):
    """A booking made by a user for a given UnlockSlot."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlock_bookings')
    slot = models.ForeignKey(UnlockSlot, on_delete=models.CASCADE, related_name='bookings')
    booked_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        unique_together = ('user', 'slot')

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.slot.date}"


class Attendance(models.Model):
    """Attendance record for a student on an unlock date."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    slot = models.ForeignKey(UnlockSlot, on_delete=models.CASCADE, related_name='attendances')
    subject = models.CharField(max_length=255, blank=True, default='')
    is_present = models.BooleanField(default=False)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marked_attendances')
    marked_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        unique_together = ('user', 'slot', 'subject')
        ordering = ['-slot__date']

    def __str__(self) -> str:
        status = "Present" if self.is_present else "Absent"
        subj = f" [{self.subject}]" if self.subject else ""
        return f"{self.user.username} - {self.slot.date}{subj} ({status})"


class FacultySubjectAssignment(models.Model):
    """Assignment of a subject to a faculty member for grading."""
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_subjects')
    subject = models.CharField(max_length=255)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='subject_assignments_made')
    assigned_at = models.DateTimeField(default=timezone.now, editable=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('faculty', 'subject')
        ordering = ['-assigned_at']

    def __str__(self) -> str:
        return f"{self.faculty.username} - {self.subject}"


class ExamResult(models.Model):
    """Marks/grade assigned by faculty for a saved exam attempt."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_results')
    subject = models.CharField(max_length=255)
    attempt_id = models.CharField(max_length=64, help_text="Identifier from saved exam file (saved_at token).")
    semester = models.CharField(max_length=50, blank=True)
    exam_date = models.DateField(null=True, blank=True)
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    max_marks = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True)
    graded_by = models.CharField(max_length=150, blank=True)
    graded_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'attempt_id')
        ordering = ['-graded_at']

    def __str__(self) -> str:
        return f"{self.user.username} - {self.subject} ({self.attempt_id})"