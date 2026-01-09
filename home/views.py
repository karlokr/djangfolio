from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from projects.models import SoftwareProject, MathPhysicsProject, WebProject
from resume.models import Resume, SkillGroup
import logging

logger = logging.getLogger(__name__)

# Create your views here.
def home_page(request):
    software_projects = SoftwareProject.objects.order_by('-pub_date')
    mathphysics_projects = MathPhysicsProject.objects.order_by('-pub_date')
    web_projects = WebProject.objects.order_by('-pub_date')
    resume = Resume.objects.first()  # Use .first() instead of [0] to handle empty queryset
    
    skill_groups = SkillGroup.objects.all()
    context = {
        'software_projects': software_projects,
        'mathphysics_projects': mathphysics_projects,
        'web_projects': web_projects,
        'resume': resume,
        'skill_groups': skill_groups,
    }
    return render(request, 'home/index.html', context)


@csrf_exempt
@require_POST
def send_contact_email(request):
    """Handle contact form submissions"""
    try:
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Validate required fields
        if not name:
            return JsonResponse({
                'status': 'error',
                'message': 'Name is required'
            }, status=400)
        
        if not email:
            return JsonResponse({
                'status': 'error',
                'message': 'Email is required'
            }, status=400)
        
        if not message:
            return JsonResponse({
                'status': 'error',
                'message': 'Message is required'
            }, status=400)
        
        # Create email content
        email_subject = f"Portfolio Contact: {subject}" if subject else "Portfolio Contact Form"
        email_body = f"""
New contact form submission:

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}
"""
        
        # Log email configuration for debugging
        logger.info(f"Attempting to send email with backend: {settings.EMAIL_BACKEND}")
        logger.info(f"Email host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        logger.info(f"From: {settings.DEFAULT_FROM_EMAIL}, To: {settings.CONTACT_EMAIL}")
        
        # Send email
        try:
            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            logger.info(f"Contact email successfully sent from {name} ({email})")
        except Exception as email_error:
            logger.error(f"Failed to send email: {str(email_error)}")
            logger.exception("Full email error traceback:")
            raise
        
        return JsonResponse({
            'status': 'success',
            'message': 'Thank you, your message has been received.'
        })
        
    except Exception as e:
        logger.error(f"Error in contact form handler: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while sending your message. Please try again later.'
        }, status=500)

