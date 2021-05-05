from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractUser, Group, PermissionsMixin
from django.db import models
from django.db.models import Q, Count
from django.db.models.signals import post_save
from django.urls import reverse
from rest_framework.authtoken.models import Token

from blogapp import settings
from datetime import datetime, timedelta

# PENDING = 0
# APPROVED = 1
# REJECTED = 2
# STATUS_CHOICES = (
#     (PENDING, 'Pending'),
#     (APPROVED, 'Approved'),
#     (REJECTED, 'Rejected')
# )
PENDING = 'Pending'
APPROVED = 'Approved'
REJECTED = 'Rejected'
STATUS_CHOICES = (
    ('Pending', 'Pending'),
    ('Approved', 'Approved'),
    ('Rejected', 'Rejected')
)

APPROVAL_STATUS_CHOICES = (
    ('Approved', 'Approved'),
    ('Rejected', 'Rejected')
)


# Create your models here.

class WriterManager(BaseUserManager):

    def create_user(self, email, username, name, password=None):
        print('#' * 100)
        if not email:
            raise ValueError("Writers must have an email address")
        if not username:
            raise ValueError("Writers must have an username")
        if not name:
            raise ValueError("Writers must have an username")
        #
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            name=name,
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, username, name, password=None):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            name=name,
            password=password
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user

    def get_writers_with_total_article_numbers_and_total_article_numbers_last_30_days(self):
        #
        writers = Writer.objects.annotate(
            num_all=Count('written_by'),
            num_lte30=Count(
                'written_by',
                filter=Q(
                    written_by__created_at__gte=datetime.now() - timedelta(days=30)
                )
            )
        ).order_by('id')
        return writers


class Writer(AbstractBaseUser, PermissionsMixin):
    # required fields for custom user model
    email = models.EmailField(verbose_name="email", max_length=50)
    username = models.CharField(max_length=50)
    date_joined = models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    date_login = models.DateTimeField(verbose_name='date login', auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    # fields for our (user) model
    name = models.CharField(max_length=50, unique=True)
    is_editor = models.BooleanField(default=False)

    USERNAME_FIELD = 'name'
    # REQUIRED_FIELDS = ['username', 'email']

    objects = WriterManager()

    def __str__(self):
        return f"{self.name}"

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True


def writer_post_save_receiver(sender, instance, **kwargs):
    if instance.is_editor:
        new_group, created = Group.objects.get_or_create(name='Editor')
        group = Group.objects.get(name='Editor')
        instance.groups.add(group)
    #
    # token = Token.objects.create(user_id=instance.id)
    # print(token)


post_save.connect(writer_post_save_receiver, sender=Writer)


class Article(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    status = models.CharField(max_length=10, default=PENDING, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    written_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='written_by'
    )
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='edited_by',
        null=True,
        blank=True
    )

    # approval_by = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.CASCADE,
    #     related_name='approval_by',
    #     null=True,
    #     blank=True
    # )

    def __str__(self):
        return f"{self.title}"

    # def get_absolute_url(self):
    #     return reverse('article_detail', args=[self.id])
