from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default admin user for the application'


    def handle(self, *args, **options):
        email = 'admin@thereferralpro.com'
        password = 'admin@referralpro.com'
        try:
            user, created = User.objects.get_or_create(email=email, defaults={
                'full_name': 'Admin User',
                'role': 'superadmin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'is_verified': True,
                'is_passwordSet': True,
            })
            if not created:
                user.set_password(password)
                user.role = 'superadmin'
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.is_verified = True
                user.is_passwordSet = True
                user.full_name = 'Admin User'
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Updated existing admin user: {email}'))
            else:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created admin user: {email}'))
            self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating admin user: {e}'))