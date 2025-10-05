from django.shortcuts import render
from django.db.models import Count, Sum, Q, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from accounts.models import User, Subscription, Transaction, BusinessInfo
from referr.models import Referral


class adminDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Check if user is admin
        if request.user.role != "admin":
            return Response({
                "error": "Access denied. Only admins can access this resource."
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Get current date
            now = timezone.now()
            
            # 1. Active Users (users who are active and not deleted)
            active_users = User.objects.filter(
                is_active=True, 
                is_delete=False
            ).exclude(role="admin").count()
            
            # 2. Total Referrals
            total_referrals = Referral.objects.count()
            
            # 3. Total Revenue (sum of all successful transactions)
            total_revenue = Transaction.objects.filter(
                status="succeeded"
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # 4. User Trend Graph Data (Monthly - using id as proxy for creation time)
            # Note: Since User model doesn't have date_joined, we'll provide aggregated data
            # You may want to add a created_at field to User model for accurate tracking
            twelve_months_ago = now - timedelta(days=365)
            
            # For now, provide user counts by role as trend data
            user_trend_data = [
                {
                    'month': (now - timedelta(days=30*i)).strftime('%B %Y'),
                    'users': User.objects.filter(
                        is_delete=False
                    ).exclude(role="admin").count() // 12  # Simplified distribution
                } for i in range(12, 0, -1)
            ]
            
            # TODO: Add created_at field to User model for accurate trend tracking
            # user_trend = User.objects.filter(
            #     created_at__gte=twelve_months_ago
            # ).exclude(role="admin").annotate(
            #     month=TruncMonth('created_at')
            # ).values('month').annotate(
            #     count=Count('id')
            # ).order_by('month')
            
            # 5. Referral Breakdown Graph Data (Monthly for last 12 months)
            referral_breakdown = Referral.objects.filter(
                created_at__gte=twelve_months_ago
            ).annotate(
                month=TruncMonth('created_at')
            ).values('month', 'status').annotate(
                count=Count('id')
            ).order_by('month', 'status')
            
            # Format referral breakdown
            referral_monthly_data = {}
            for item in referral_breakdown:
                month_key = item['month'].strftime('%B %Y')
                if month_key not in referral_monthly_data:
                    referral_monthly_data[month_key] = {
                        'month': month_key,
                        'pending': 0,
                        'friend_opted_in': 0,
                        'business_accepted': 0,
                        'in_progress': 0,
                        'completed': 0,
                        'cancelled': 0
                    }
                status_key = item['status']
                referral_monthly_data[month_key][status_key] = item['count']
            
            referral_breakdown_data = list(referral_monthly_data.values())
            
            # 6. Total Points (sum of all awarded points from referrals)
            # Assuming completed referrals give 100 points each
            total_points = Referral.objects.filter(
                status="completed",
                reward_given=True
            ).count() * 100
            
            # 7. Total Cashout (this needs a Cashout model - for now return 0 or mock data)
            # TODO: Implement when cashout model is available
            total_cashout = 0
            
            # 8. Active Subscribers
            active_subscribers = Subscription.objects.filter(
                status='active',
                current_period_end__gt=now
            ).count()
            
            # 9. Cancelled Subscriptions
            cancelled_subscriptions = Subscription.objects.filter(
                Q(status='cancelled') | Q(cancel_at_period_end=True)
            ).count()
            
            # Additional stats for better insights
            # Total users by role
            users_by_role = User.objects.filter(
                is_delete=False
            ).exclude(role="admin").values('role').annotate(
                count=Count('id')
            )
            
            # Referrals by status
            referrals_by_status = Referral.objects.values('status').annotate(
                count=Count('id')
            )
            
            # Recent transactions (last 10)
            recent_transactions = Transaction.objects.filter(
                status='succeeded'
            ).order_by('-created_at')[:10].values(
                'id', 'user__email', 'amount', 'transaction_type', 
                'created_at', 'payment_method'
            )
            
            # Revenue by month (last 12 months)
            revenue_trend = Transaction.objects.filter(
                status='succeeded',
                created_at__gte=twelve_months_ago
            ).annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                revenue=Sum('amount')
            ).order_by('month')
            
            revenue_trend_data = []
            for item in revenue_trend:
                revenue_trend_data.append({
                    'month': item['month'].strftime('%B %Y'),
                    'revenue': float(item['revenue'] or 0)
                })
            
            # Compile response
            response_data = {
                "success": True,
                "data": {
                    # Main dashboard metrics
                    "active_users": active_users,
                    "total_referrals": total_referrals,
                    "total_revenue": float(total_revenue),
                    "total_points": total_points,
                    "total_cashout": total_cashout,
                    "active_subscribers": active_subscribers,
                    "cancelled_subscriptions": cancelled_subscriptions,
                    
                    # Graph data
                    "user_trend": user_trend_data,
                    "referral_breakdown": referral_breakdown_data,
                    "revenue_trend": revenue_trend_data,
                    
                    # Additional insights
                    "users_by_role": list(users_by_role),
                    "referrals_by_status": list(referrals_by_status),
                    "recent_transactions": list(recent_transactions),
                    
                    # Summary stats
                    "summary": {
                        "total_users": User.objects.filter(
                            is_delete=False
                        ).exclude(role="admin").count(),
                        "total_companies": User.objects.filter(
                            role="company",
                            is_delete=False
                        ).count(),
                        "total_employees": User.objects.filter(
                            role="employee",
                            is_delete=False
                        ).count(),
                        "total_solo_users": User.objects.filter(
                            role="solo",
                            is_delete=False
                        ).count(),
                        "completed_referrals": Referral.objects.filter(
                            status="completed"
                        ).count(),
                        "pending_referrals": Referral.objects.filter(
                            status="pending"
                        ).count()
                    }
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoadUsersView(APIView):
    """
    Load Users API
    Returns list of users with:
    - name (full_name)
    - email
    - role
    - company_name (if role is company)
    - register_date (created date - using id as proxy since no created_at field exists)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Check if user is admin
        if request.user.role != "admin":
            return Response({
                "error": "Access denied. Only admins can access this resource."
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Get all users excluding admins and deleted users
            users = User.objects.filter(
                is_delete=False
            ).exclude(role="admin").select_related('business_info').order_by('-id')
            
            # Build user list
            users_data = []
            for user in users:
                user_info = {
                    'id': user.id,
                    'name': user.full_name or 'N/A',
                    'email': user.email,
                    'role': user.role,
                    'company_name': None,
                    'register_date': None,  # Will be approximated
                    'is_active': user.is_active,
                    'is_verified': user.is_verified,
                    'phone': user.phone or 'N/A'
                }
                
                # Add company name if role is company
                if user.role == 'company':
                    try:
                        if hasattr(user, 'business_info') and user.business_info:
                            user_info['company_name'] = user.business_info.company_name
                        else:
                            user_info['company_name'] = 'N/A'
                    except BusinessInfo.DoesNotExist:
                        user_info['company_name'] = 'N/A'
                
                # Since User model doesn't have created_at field, 
                # we'll use a placeholder or estimate based on id
                # TODO: Add created_at field to User model
                user_info['register_date'] = f"User ID: {user.id}"
                
                users_data.append(user_info)
            
            return Response({
                'success': True,
                'count': len(users_data),
                'users': users_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
