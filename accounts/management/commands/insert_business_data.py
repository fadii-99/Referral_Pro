from django.core.management.base import BaseCommand
from accounts.models import User, BusinessInfo


class Command(BaseCommand):
    help = 'Insert business info data from SQL dump'

    def handle(self, *args, **options):
        # Data from the SQL INSERT statement
        business_data = [
            {
                'id': 1,
                'company_name': '',
                'industry': 'Technology',
                'employees': '51 – 100',
                'biz_type': 'sole',
                'address1': 'House # 20, Street # 25-C',
                'address2': 'House # 20, Street # 25-C',
                'city': 'Wah',
                'post_code': '47010',
                'website': 'www.testCompany1.com',
                'us_state': 'Arkansas',
                'user_id': 1
            },
            {
                'id': 2,
                'company_name': '',
                'industry': 'Education',
                'employees': '100 – 500',
                'biz_type': 'sole',
                'address1': 'teset address',
                'address2': 'test address 1 2 3',
                'city': 'Islamabad',
                'post_code': '8888',
                'website': 'www.independent.com',
                'us_state': 'Colorado',
                'user_id': 3
            },
            {
                'id': 4,
                'company_name': '',
                'industry': 'Healthcare',
                'employees': '1 – 50',
                'biz_type': 'sole',
                'address1': 'testing...1',
                'address2': 'testing...1',
                'city': 'test1',
                'post_code': '00000',
                'website': 'www.test.com',
                'us_state': 'Alaska',
                'user_id': 7
            }
        ]

        self.stdout.write("Starting to insert business info data...")

        for data in business_data:
            user_id = data.pop('user_id')
            business_id = data.pop('id')
            
            try:
                # Check if user exists
                try:
                    user = User.objects.get(id=user_id)
                    self.stdout.write(f"Found user with ID {user_id}: {user.email}")
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f"User with ID {user_id} does not exist. Skipping business info with ID {business_id}")
                    )
                    continue

                # Check if business info already exists for this user
                if BusinessInfo.objects.filter(user=user).exists():
                    self.stdout.write(
                        self.style.WARNING(f"Business info already exists for user {user.email}. Skipping...")
                    )
                    continue

                # Create business info
                business_info = BusinessInfo.objects.create(
                    user=user,
                    company_name=data['company_name'],
                    industry=data['industry'],
                    employees=data['employees'],
                    biz_type=data['biz_type'],
                    address1=data['address1'],
                    address2=data['address2'],
                    city=data['city'],
                    post_code=data['post_code'],
                    website=data['website'],
                    us_state=data['us_state']
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully created business info for user {user.email} (ID: {business_info.id})")
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error creating business info for user ID {user_id}: {str(e)}")
                )

        self.stdout.write(self.style.SUCCESS("Finished processing business info data."))