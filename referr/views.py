# rest framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

# Django
from django.db import models
from django.db.models import Count, Sum
from django.utils.timezone import now, timedelta
from django.db.models import Sum


# models
from accounts.models import BusinessInfo
from .models import Referral, ReferralAssignment, ReferralReward
from accounts.models import User, BusinessInfo, FavoriteCompany

# utils
from utils.email_service import send_app_download_email, send_referral_email
from utils.twilio_service import TwilioService
from utils.storage_backends import generate_presigned_url
from utils.notify import notify_users
from utils.activity import log_activity


def IMAGEURL(image_path):
    image_url = None
    if hasattr(image_path, 'url'):
        # Check if it's a URL (from social login) or a file
        if str(image_path).startswith(('http://', 'https://')):
            # It's a URL from social login
            image_url = str(image_path)
        else:
            # It's a file stored in storage
            image_url = generate_presigned_url(f"media/{image_path}", expires_in=3600)
    return image_url



class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # Referrals created by this user
            referrals_created = Referral.objects.filter(company=user).count()

            # Referrals accepted by companies
            referrals_accepted = Referral.objects.filter(
                company=user, status="in_progress"
            ).count()

            # ✅ Referrals completed (count)
            referrals_completed_count = Referral.objects.filter(
                company=user, status="completed"
            ).count()

            # ✅ Completed referral IDs for reward sum
            completed_referrals = Referral.objects.filter(
                company=user, status="completed"
            ).values_list("id", flat=True)

            # ✅ Total points earned (from ReferralReward)
            total_awards = ReferralReward.objects.filter(
                referral_id__in=completed_referrals
            ).aggregate(
                total_points=Sum("points_awarded")
            )["total_points"] or 0

            # Conversion rate for cash value (example: 1 point = $1)
            points_cashed_value = float(total_awards) / 10.0

            # Missed opportunities (cancelled or rejected)
            missed_opportunity = Referral.objects.filter(
                company=user, status="cancelled"
            ).count()

            # ----------------------
            # Graph data (last 7 days)
            # ----------------------
            today = now().date()
            start_date = today - timedelta(days=6)

            referrals_per_day = (
                Referral.objects.filter(company=user, created_at__date__gte=start_date)
                .extra(select={"day": "date(created_at)"})
                .values("day")
                .annotate(count=Count("id"))
                .order_by("day")
            )

            daily_counts = {str(item["day"]): item["count"] for item in referrals_per_day}

            graph_data = []
            for i in range(7):
                day = start_date + timedelta(days=i)
                graph_data.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "day": day.strftime("%a"),
                    "count": daily_counts.get(str(day), 0)
                })

            return Response(
                {
                    "referrals_created": referrals_created,
                    "referrals_accepted": referrals_accepted,
                    "referrals_completed": referrals_completed_count,
                    "total_points_allocated": total_awards,
                    "points_cashed_value": points_cashed_value,
                    "missed_opportunity": missed_opportunity,
                    "graph_data": graph_data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(f"Error fetching dashboard stats: {str(e)}")
            return Response(
                {"error": f"Error fetching dashboard stats: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )




class ListCompaniesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all companies with favorite status for current user"""
        companies = User.objects.filter(role='company').exclude(id=request.user.id).select_related('business_info')
        
        # Get user's favorite company IDs
        favorite_company_ids = set(
            FavoriteCompany.objects.filter(user=request.user).values_list('company_id', flat=True)
        )

        
        
        companies_list = []
        for company in companies:
            image_url = None
            if company.image:
                image_url = generate_presigned_url(f"media/{company.image}", expires_in=3600)

            company_data = {
                "id": company.id,
                "email": company.email,
                "full_name": company.full_name,
                "phone": company.phone,
                "image": image_url,
                "is_favorite": company.id in favorite_company_ids
            }
            if hasattr(company, 'business_info'):
                business_info = company.business_info
                company_data.update({
                    "company_name": business_info.company_name,
                    "industry": business_info.industry,
                    "employees": business_info.employees,
                    "business_type": business_info.biz_type,
                    "address1": business_info.address1,
                    "address2": business_info.address2,
                    "city": business_info.city,
                    "post_code": business_info.post_code,
                    "website": business_info.website,
                    "us_state": business_info.us_state,
                })
            
            companies_list.append(company_data)

        
        return Response({
            "message": "Companies retrieved successfully",
            "companies": companies_list,
            "total": len(companies_list)
        }, status=status.HTTP_200_OK)


class FavoriteCompanyView(APIView):
    permission_classes = [IsAuthenticated]


    def post(self, request):
        """Add a company to favorites"""
        company_id = request.data.get('company_id')
        
        if not company_id:
            return Response({"error": "Company ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            company = User.objects.get(id=company_id, role='company')
        except User.DoesNotExist:
            return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
        


        # Don't allow users to favorite themselves
        if request.user == company:
            return Response({"error": "You cannot add yourself to favorites"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already favorited
        favorite_exists = FavoriteCompany.objects.filter(user=request.user, company=company)
        if favorite_exists.exists():
            favorite_exists.delete()
            return Response({"message": "Company removed from favorites"}, status=status.HTTP_200_OK)
        
        
        # Create favorite
        favorite = FavoriteCompany.objects.create(
            user=request.user,
            company=company,
        )
        
        
        return Response({
            "message": "Company added to favorites successfully",
        }, status=status.HTTP_201_CREATED)


    def delete(self, request):
        """Remove a company from favorites"""
        company_id = request.data.get('company_id')
        
        if not company_id:
            return Response({"error": "Company ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            favorite = FavoriteCompany.objects.get(user=request.user, company_id=company_id)
            favorite.delete()
            return Response({"message": "Company removed from favorites successfully"}, status=status.HTTP_200_OK)
        except FavoriteCompany.DoesNotExist:
            return Response({"error": "Favorite not found"}, status=status.HTTP_404_NOT_FOUND)




 

class SendReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data
            company_id = data.get("company_id")
            referred_to_email = data.get("referred_to_email")
            referred_to_phone = data.get("referred_to_phone")
            referred_to_name = data.get("referred_to_name")
            reason = data.get("reason")
            privacy = data.get("privacy", False)
            urgency_level = data.get("urgency_level")
            request_description = data.get("request_description")
            permission_consent = data.get("permission_consent", False)

            if not company_id or not referred_to_email or not referred_to_name:
                return Response(
                    {"error": "company_id, email, and name are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if request.user.email == referred_to_email:
                return Response(
                    {"error": "You cannot refer yourself"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                company = BusinessInfo.objects.get(user_id=company_id)
                COMPANY = User.objects.get(id=company_id)
            except Exception as e:
                return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
            

            # If referred_to user exists, use it. Otherwise, create a placeholder.
            referred_to_user, _ = User.objects.get_or_create(
                email=referred_to_email,
                
                defaults={"full_name": referred_to_name, "phone": referred_to_phone, "role": "solo", 'is_to_be_registered': True},
            )

            referral = Referral.objects.create(
                referred_by=request.user,
                referred_to=referred_to_user,
                company=COMPANY,
                service_type=reason,
                urgency=urgency_level,
                notes=request_description,
                privacy_opted=privacy,
                permission_consent=permission_consent,
            )

            log_activity(
                event="send_referral",
                actor=request.user,
                referral=referral,
                title="Referral sent",
                body=f"{request.user.full_name} referred {referred_to_user.full_name or referred_to_email} to {COMPANY.full_name or company.company_name}",
                meta={
                    "referred_to_email": referred_to_email,
                    "urgency": urgency_level,
                    "service_type": reason,
                    "permission_consent": bool(permission_consent),
                    "privacy_opted": bool(privacy),
                },
            )

            send_referral_email(
                referred_to_email=referred_to_email,
                referred_to_name=referred_to_name,
                company_name=company.company_name if company.company_name else COMPANY.full_name,  
                referred_by_name=request.user.full_name,
                reason=reason,
                request_description=request_description,
                referral_code=referral.referred_by.referral_code
            )

            if referred_to_phone:
                TwilioService.send_referral_sms(
                    phone_number=referred_to_phone,
                    referred_to_name=referred_to_name,
                    company_name=company.company_name if company.company_name else COMPANY.full_name,
                    referred_by_name=request.user.full_name,
                    reason=reason,
                    request_description=request_description,
                )


            payload = {
                "event": "referral.sent",
                "referral_id": referral.id,
                "reference_id": referral.reference_id,
                "title": "New referral",
                "message": f"{request.user.full_name} referred {referred_to_user.full_name} to {company.company_name if company.company_name else COMPANY.full_name}",
                "actors": {
                    "referred_by_id": request.user.id,
                    "referred_to_id": referred_to_user.id,
                    "company_id": COMPANY.id,
                    "rep_id": None
                },
                "meta": {
                    "company_name": COMPANY.full_name,
                    "referred_by_name": request.user.full_name,
                    "referred_to_name": referred_to_user.full_name,
                    "status": referral.status,
                }
            }

            notify_users([referred_to_user.id, COMPANY.id], payload)


            return Response(
                {
                    "message": "Referral sent successfully",
                    "referral_details": {
                        "reference_id": referral.reference_id,
                        "date": referral.created_at.strftime("%d %b %Y") if referral.created_at else None,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            print(f"Error sending referral: {str(e)}")
            return Response(
                {"error": f"Error sending referral: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    

 
class AssignRepView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        referral_id = data.get("referral_id")
        employee_id = data.get("employee_id")
        note = data.get("notes", "")
        referral_status = data.get("status", "in_progress")  # default to in_progress

        # Validate referral
        try:
            referral_obj = Referral.objects.get(id=referral_id)
        except Referral.DoesNotExist:
            return Response({"error": "Referral not found"}, status=status.HTTP_404_NOT_FOUND)

        # Validate employee
        employee = None
        if employee_id is not None:
            try:
                employee = User.objects.get(id=employee_id)
            except User.DoesNotExist:
                return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if assignment already exists for this referral
        assignment = ReferralAssignment.objects.filter(referral=referral_obj).last()

        if assignment:
            # Update existing assignment
            assignment.assigned_to = employee
            assignment.notes = note or assignment.notes
            assignment.status = "in_progress"
            assignment.save()
            message = "Referral assignment updated successfully"
        else:
            # Create new assignment
            assignment = ReferralAssignment.objects.create(
                referral=referral_obj,
                assigned_to=employee,
                notes=note,
            )
            message = "Referral assigned successfully"

        # Update referral status
        referral_obj.status = "cancelled" if referral_status == "reject" else "in_progress"
        referral_obj.company_approval = True if referral_status == "accept" else False
        referral_obj.save()

        log_activity(
            event="rep_assigned",
            actor=request.user,                 # whoever triggered the assign (company admin etc.)
            referral=referral_obj,
            subject_user=employee,              # the rep being assigned
            title="Rep assigned",
            body=f"{employee.full_name if employee else '—'} assigned to referral {referral_obj.reference_id}",
            meta={
                "assignment_id": assignment.id,
                "status": referral_obj.status,
                "company_approval": referral_obj.company_approval,
                "note": note,
            },
        )


        if referral_status == "accept":
            payload = {
                "event": "referral.company_accepted",
                "unread": True,
                "referral_id": referral_obj.id,
                "reference_id": referral_obj.reference_id,
                "title": "Company accepted your referral",
                "message": f"{referral_obj.company.full_name} accepted the referral",
                "actors": {
                    "referred_by_id": referral_obj.referred_by.id,
                    "referred_to_id": referral_obj.referred_to.id,
                    "company_id": referral_obj.company.id,
                    "rep_id": employee.id if employee else None
                },
                "meta": {
                    "company_name": referral_obj.company.full_name,
                    "referred_by_name": referral_obj.referred_by.full_name,
                    "referred_to_name": referral_obj.referred_to.full_name,
                    "status": referral_obj.status,
                }
            }
            notify_users([referral_obj.referred_to.id, referral_obj.referred_by.id], payload)


        payload = {
            "event": "referral.rep_assigned",
            "unread": True,
            "referral_id": referral_obj.id,
            "reference_id": referral_obj.reference_id,
            "title": "You were assigned a referral",
            "message": f"You were assigned to {referral_obj.referred_to.full_name} @ {referral_obj.company.full_name}",
            "actors": {
                "referred_by_id": referral_obj.referred_by.id,
                "referred_to_id": referral_obj.referred_to.id,
                "company_id": referral_obj.company.id,
                "rep_id": employee.id if employee else None
            },
            "meta": {
                "company_name": referral_obj.company.full_name,
                "referred_to_name": referral_obj.referred_to.full_name,
                "status": referral_obj.status,
            }
        }

        if employee:
            notify_users([employee.id], payload)

        return Response(
            {
                "message": message,
                "assignment_id": assignment.id,
                "referral_status": referral_obj.status,
                "assigned_to": assignment.assigned_to.full_name if assignment.assigned_to else None,
            },
            status=status.HTTP_200_OK if message.endswith("updated successfully") else status.HTTP_201_CREATED,
        )




 
class ListSoloReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        referrals = None
        if request.data.get("referral_type") == "referred_by":
            referrals = Referral.objects.filter(referred_by=request.user.id).select_related(
                'referred_to', 'company', 'company__business_info'
            )
        elif request.data.get("referral_type") == "referred_to":
            referrals = Referral.objects.filter(referred_to=request.user.id).select_related(
                'referred_to', 'company', 'company__business_info'
            )
        referral_list = []
        for referral in referrals:  
            # Get company information
            company_name = ""
            company_type = ""
            company_image = None
            industry = ""
            
            try:
                if hasattr(referral.company, 'business_info'):
                    business_info = referral.company.business_info
                    company_name = business_info.company_name
                    company_type = business_info.biz_type
                    industry = business_info.industry
                elif hasattr(referral.company, 'company_name'):
                    # If company is directly a BusinessInfo object
                    company_name = referral.company.company_name
                    company_type = referral.company.biz_type if hasattr(referral.company, 'biz_type') else ""
                
                # Get company image from user profile
                if referral.company.image:
                    company_image = generate_presigned_url(f"media/{referral.company.image}", expires_in=3600)
            except AttributeError:
                # Handle cases where company relationships might not exist
                company_name = "Unknown Company"
                company_type = "Unknown"
            display_name = company_name
            if not display_name:
                display_name = business_info.user.full_name 

            
            
            referral_list.append({
                "id": referral.id,
                "reference_id": referral.reference_id,
                "referred_to_email": referral.referred_to.email,
                "referred_to_name": referral.referred_to.full_name,
                "referred_to_image": IMAGEURL(referral.referred_to.image) if referral.referred_to.image else None,
                "referred_by_email": referral.referred_by.email,
                "referred_by_name": referral.referred_by.full_name,
                "referred_by_image":  IMAGEURL(referral.referred_by.image) if referral.referred_by.image else None,
                "industry": industry,
                "company_name": display_name,
                "company_image": company_image,
                "company_type": company_type,
                "status": referral.status,
                "date": referral.created_at.strftime("%d %b %Y") if referral.created_at else None,
                "company_image": company_image,
                "reason": referral.service_type,
                "urgency": referral.urgency,
                "notes": referral.notes,
                "privacy": referral.privacy_opted,
                "referred_by_approval": referral.referred_by_approval,
                "referral_type": request.data.get("referral_type"),
            })


        return Response(
            {
                "message": "Referral list retrieved successfully",
                "referrals": referral_list,
            },
            status=status.HTTP_200_OK,
        )
    




class UpdateReferralPrivacyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        referral_id = request.data.get("referral_id")
        privacy_status = request.data.get("privacy")
        
        # Validate required fields
        if referral_id is None:
            print("Referral ID is missing")
            return Response(
                {"error": "referral_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if privacy_status is None:
            print("Privacy status is missing")
            return Response(
                {"error": "privacy status is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Validate privacy status is boolean
        if not isinstance(privacy_status, bool):
            return Response(
                {"error": "privacy must be a boolean value (true/false)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get the referral and ensure it belongs to the authenticated user
            referral = Referral.objects.filter(
                id=referral_id
            ).filter(
                models.Q(referred_by=request.user) | models.Q(referred_to=request.user)
            ).first()
            
            if not referral:
                raise Referral.DoesNotExist
        except Referral.DoesNotExist:
            return Response(
                {"error": "Referral not found or you don't have permission to update it"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Update the privacy status
        referral.privacy_opted = privacy_status
        referral.save()

        return Response(
            {
                "message": "Privacy status updated successfully",
            },
            status=status.HTTP_200_OK,
        )




class ListReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'solo':
            referrals = Referral.objects.all().exclude(company_id=request.user.id)
        else:
            referrals = Referral.objects.all()
        referral_list = []
        for referral in referrals:  
            # Get company information
            company_name = ""
            company_type = ""
            company_image = None
            industry = ""
            
            try:
                if hasattr(referral.company, 'business_info'):
                    business_info = referral.company.business_info
                    company_name = business_info.company_name
                    company_type = business_info.biz_type
                    industry = business_info.industry
                elif hasattr(referral.company, 'company_name'):
                    # If company is directly a BusinessInfo object
                    company_name = referral.company.company_name
                    company_type = referral.company.biz_type if hasattr(referral.company, 'biz_type') else ""
                
                # Get company image from user profile
                if referral.company.image:
                    company_image = referral.company.image.url
            except AttributeError:
                # Handle cases where company relationships might not exist
                company_name = "Unknown Company"
                company_type = "Unknown"
            display_name = company_name
            if not display_name:
                display_name = business_info.user.full_name 
            
            referral_list.append({
                "id": referral.id,
                "reference_id": referral.reference_id,
                "referred_to_email": referral.referred_to.email,
                "referred_to_name": referral.referred_to.full_name,
                "industry": industry,
                "company_name": display_name,
                "company_type": company_type,
                "status": referral.status,
                "date": referral.created_at.strftime("%d %b %Y") if referral.created_at else None,
                "company_image": company_image,
                "reason": referral.service_type,
                "urgency": referral.urgency,
                "notes": referral.notes,
                "privacy": referral.privacy_opted,
            })

        return Response(
            {
                "message": "Referral list retrieved successfully",
                "referrals": referral_list,
            },
            status=status.HTTP_200_OK,
        )
    



class ListCompanyReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.data.get("referral_id"):
            referrals = Referral.objects.filter(reference_id=request.data.get("referral_id"), company=request.user)
        else:
            referrals = Referral.objects.filter(company=request.user)

        referral_list = []  # Initialize referral_list
        
        for referral in referrals:
            # Get company information
            company_name = ""
            company_type = ""
            company_image = None
            industry = ""
            business_info = None  # Initialize business_info

            try:
                if hasattr(referral.company, 'business_info'):
                    business_info = referral.company.business_info
                    company_name = business_info.company_name
                    company_type = business_info.biz_type
                    industry = business_info.industry
                elif hasattr(referral.company, 'company_name'):
                    company_name = referral.company.company_name
                    company_type = getattr(referral.company, 'biz_type', "")
                if getattr(referral.company, 'image', None):
                    company_image = generate_presigned_url(f"media/{referral.company.image}", expires_in=3600)
            except AttributeError:
                company_name = "Unknown Company"
                company_type = "Unknown"

            # Fix the display_name logic
            display_name = company_name
            if not display_name and business_info:
                display_name = getattr(business_info.user, 'full_name', "Unknown")
            elif not display_name:
                display_name = "Unknown"

            # Build assigned employee details with error handling
            try:
                assignment = ReferralAssignment.objects.get(referral=referral)
                assigned_to_id = assignment.id
                assigned_to_name = assignment.assigned_to.full_name if assignment.assigned_to else None
                assigned_at = assignment.assigned_at.strftime("%d %b %Y") if assignment.assigned_at else None
                assigned_notes = assignment.notes if assignment.notes else None
            except ReferralAssignment.DoesNotExist:
                assigned_to_id = None
                assigned_to_name = None
                assigned_at = None
                assigned_notes = None

            referral_list.append({
                "id": referral.id,
                "reference_id": referral.reference_id,
                "referred_to_email": referral.referred_to.email,
                "referred_to_name": referral.referred_to.full_name,
                "referred_to_image": IMAGEURL(referral.referred_to.image) if referral.referred_to.image else None,
                "referred_to_phone": referral.referred_to.phone,
                 "referred_by_email": referral.referred_by.email,
                "referred_by_name": referral.referred_by.full_name,
                "referred_by_image": IMAGEURL(referral.referred_by.image) if referral.referred_by.image else None,
                "industry": industry,
                "company_name": display_name,
                "company_type": company_type,
                "company_approval": referral.company_approval,
                "referred_by_approval": referral.referred_by_approval,
                "status": referral.status,
                "date": referral.created_at.strftime("%d %b %Y") if referral.created_at else None,
                "company_image": company_image,
                "reason": referral.service_type,
                "urgency": referral.urgency,
                "notes": referral.notes,
                "privacy": referral.privacy_opted,
                "assigned_to_id": assigned_to_id,  
                "assigned_to_name": assigned_to_name,  
                "assigned_at": assigned_at,
                "assigned_notes": assigned_notes,
            })

        return Response(
            {
                "message": "Referral list retrieved successfully",
                "referrals": referral_list,
            },
            status=status.HTTP_200_OK,
        )



class ListAssignedReferralView(APIView):
    permission_classes = [IsAuthenticated]


    def post(self, request):
        referrals = ReferralAssignment.objects.filter(user=request.user)
        referral_list = []
        for referral in referrals:  
            # Get company information
            
            
            referral_list.append({
                "id": referral.id,
                "reference_id": referral.reference_id,
                "referred_to_name": referral.referred_to.full_name,
                "referred_by_name": referral.referred_to.full_name,
                "date": referral.created_at.strftime("%d %b %Y") if referral.created_at else None,
                "status": referral.status,
                "reason": referral.service_type,
                "urgency": referral.urgency,
                "notes": referral.notes,
                "privacy": referral.privacy_opted,
            })

        return Response(
            {
                "message": "Referral list retrieved successfully",
                "referrals": referral_list,
            },
            status=status.HTTP_200_OK,
        )



class ListRepReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        # Handle case where no assignments exist for the user
        try:
            assignments = ReferralAssignment.objects.filter(assigned_to=request.user)
            if not assignments.exists():
                return Response(
                    {
                        "message": "No referrals assigned to you",
                        "referrals": [],
                    },
                    status=status.HTTP_200_OK,
                )
            
            # Get all referral IDs for this user's assignments
            referral_ids = assignments.values_list('referral_id', flat=True)
            referrals = Referral.objects.filter(id__in=referral_ids).select_related(
                'referred_to', 'company', 'company__business_info'
            )
            
        except Exception as e:
            return Response(
                {"error": f"Error fetching referrals: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        referral_list = []
        for referral in referrals:  
            # Get company information
            company_name = ""
            company_type = ""
            company_image = None
            industry = ""
            business_info = None
            
            try:
                if hasattr(referral.company, 'business_info'):
                    business_info = referral.company.business_info
                    company_name = business_info.company_name
                    company_type = business_info.biz_type
                    industry = business_info.industry
                elif hasattr(referral.company, 'company_name'):
                    # If company is directly a BusinessInfo object
                    company_name = referral.company.company_name
                    company_type = referral.company.biz_type if hasattr(referral.company, 'biz_type') else ""
                
                # Get company image from user profile
                if referral.company.image:
                    company_image = generate_presigned_url(f"media/{referral.company.image}", expires_in=3600)
            except AttributeError:
                # Handle cases where company relationships might not exist
                company_name = "Unknown Company"
                company_type = "Unknown"
            
            display_name = company_name
            if not display_name and business_info:
                display_name = business_info.user.full_name 
            elif not display_name:
                display_name = "Unknown Company"
            
            referral_list.append({
                "id": referral.id,
                "reference_id": referral.reference_id,
                "referred_to_id": referral.referred_to.id,
                "referred_to_email": referral.referred_to.email,
                "referred_to_name": referral.referred_to.full_name,
                "referred_to_image": IMAGEURL(referral.referred_to.image) if referral.referred_to.image else None,
                "referred_by_id": referral.referred_by.id,
                "referred_by_email": referral.referred_by.email,
                "referred_by_name": referral.referred_by.full_name,
                "referred_by_image": IMAGEURL(referral.referred_by.image) if referral.referred_by.image else None,
                "industry": industry,
                "company_name": display_name,
                "company_type": company_type,
                "status": referral.status,
                "date": referral.created_at.strftime("%d %b %Y") if referral.created_at else None,
                "company_image": company_image,
                "reason": referral.service_type,
                "urgency": referral.urgency,
                "notes": referral.notes,
                "privacy": referral.privacy_opted,
            })

        return Response(
            {
                "message": "Referral list retrieved successfully",
                "referrals": referral_list,
            },
            status=status.HTTP_200_OK,
        )


class SendAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data)
        referral_id = request.data.get("referral_id")
        approval = request.data.get("approval")
        if not referral_id:
            return Response(
                {"error": "referral_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            referral = Referral.objects.get(id=referral_id)
        except Referral.DoesNotExist:
            return Response({"error": "Referral not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if approval not in [True, False]:
            return Response(
                {"error": "approval must be true or false"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        referral.referred_by_approval = approval
        referral.status = "Friend opted in" if approval else "cancelled"
        referral.save()

        log_activity(
            event="friend_optin" if approval else "friend_optin",  # keep single event; you can split if you like
            actor=referral.referred_to,   # friend is the actor
            referral=referral,
            title="Friend opted in" if approval else "Friend rejected",
            body=f"{referral.referred_to.full_name} {'accepted' if approval else 'rejected'} the referral",
            meta={"approval": bool(approval)},
        )

        payload = {
            "event": "referral.friend_accepted",
            "unread": True,
            "referral_id": referral.id,
            "reference_id": referral.reference_id,
            "title": "Friend accepted",
            "message": f"{referral.referred_to.full_name} accepted the referral",
            "actors": {
                "referred_by_id": referral.referred_by.id,
                "referred_to_id": referral.referred_to.id,
                "company_id": referral.company.id,
                "rep_id": None
            },
            "meta": {
                "company_name": referral.company.full_name,
                "referred_by_name": referral.referred_by.full_name,
                "referred_to_name": referral.referred_to.full_name,
                "status": referral.status,
            }
        }

        notify_users([referral.referred_by.id, referral.company.id], payload)



        return Response({"message": "Referral Accepted"}, status=status.HTTP_200_OK)



class CompleteReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            print(request.data)
            referral_id = request.data.get("referral_id")
            status_value = request.data.get("status", "completed")
            if not referral_id:
                return Response(
                    {"error": "referral_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                referral = Referral.objects.get(id=referral_id)
            except Referral.DoesNotExist:
                return Response({"error": "Referral not found"}, status=status.HTTP_404_NOT_FOUND)

            # Check assignment exists
            assignment = referral.assignments.last()
            if not assignment:
                return Response({"error": "Referral not assigned"}, status=status.HTTP_400_BAD_REQUEST)

            # Check that the logged-in user is the assigned employee
            if assignment.assigned_to != request.user:
                return Response({"error": "You are not assigned to this referral"}, status=status.HTTP_403_FORBIDDEN)

            # Update both referral and assignment statuses
            referral.status = status_value
            referral.save()
            assignment.status = status_value
            assignment.save()

            log_activity(
                event="completed" if status_value == "completed" else "cancelled",
                actor=request.user,
                referral=referral,
                title="Referral completed" if status_value == "completed" else "Referral cancelled",
                body=f"{request.user.full_name} marked referral {referral.reference_id} as {status_value}",
                meta={
                    "assignment_id": getattr(assignment, "id", None),
                    "status": status_value,
                },
            )

            return Response({"message": "Referral marked as completed"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error completing referral: {str(e)}")
            return Response(
                {"error": f"Failed to complete referral: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )




class SendAppInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        
        # Get data from request
        email = data.get("email")
        phone = data.get("phone")
        name = data.get("name")
        
        # Validate required fields
        if not email or not name:
            return Response(
                {"error": "Email and name are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Validate email format
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {"error": "Invalid email format"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            # Get sender's name from the authenticated user
            sender_name = request.user.full_name or request.user.email
            
            # Send the app download invitation email
            send_app_download_email(
                email=email,
                name=name,
                sender_name=sender_name
            )

            if phone:
                sms_result = TwilioService.send_app_download_sms(
                    phone_number=phone,
                    name=name,
                    sender_name=sender_name
                )
            
            return Response(
                {
                    "message": "Invitation sent successfully",
                },
                status=status.HTTP_200_OK,
            )
            

            
        except Exception as e:
            return Response(
                {"error": f"Failed to send invitation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        









