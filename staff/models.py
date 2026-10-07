from django.db import models
from django.contrib.auth.models import User


class StaffProfile(models.Model):

    ROLE_CHOICES = [
        ("manager", "Manager"),
        ("sales", "Sales Staff"),
        ("production", "Production Staff"),
        ("shipping", "Shipping Staff"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    profile_picture = models.ImageField(
        upload_to="staff_profiles/",
        blank=True,
        null=True
    )

    full_name = models.CharField(
        max_length=150,
        blank=True
    )

    phone = models.CharField(
        max_length=30,
        blank=True
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    approved = models.BooleanField(
        default=False
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    last_activity = models.DateTimeField(
        null=True,
        blank=True
    )

    rejection_reason = models.TextField(
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"


class StaffActivityLog(models.Model):

    ACTION_CHOICES = [
        ("login", "Login"),
        ("logout", "Logout"),
        ("page_view", "Page Viewed"),
        ("create", "Created"),
        ("update", "Updated"),
        ("delete", "Deleted"),
        ("approve", "Approved"),
        ("reject", "Rejected"),
        ("failed_login", "Failed Login"),
    ]

    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name="activity_logs"
    )

    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES
    )

    page = models.CharField(
        max_length=255,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    user_agent = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.staff.user.username} - "
            f"{self.get_action_display()} - "
            f"{self.created_at}"
        )