from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.utils.timezone import now
from django.http import JsonResponse
from django.conf import settings
import os
import json
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout
from django.urls import reverse
from django.views.decorators.http import require_POST
from datetime import datetime, date
from decimal import Decimal
from django.db import IntegrityError
from .models import Profile, UnlockSlot, UnlockBooking, Attendance, ExamResult, FacultySubjectAssignment, User
import csv
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from django.views.decorators.http import require_http_methods


def has_admin_or_staff_access(request):
    """
    Allow either a logged-in Django user (staff/admin) or the lightweight
    site-admin session (set during admin_login) to use protected APIs.
    """
    try:
        if request.user.is_authenticated:
            return True
    except Exception:
        pass
    return bool(request.session.get('is_site_admin'))


def index(request):
    return render(request, 'index.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method=='POST':
        username=request.POST['username']
        email=request.POST['email']
        password=request.POST['password']
        confirm_password=request.POST['confirm_password']
        enrollment=request.POST.get('enrollment', '').strip()
        semester=request.POST.get('semester', '')

        if password != confirm_password:
            messages.error(request,'Password do not match')
        elif User.objects.filter(username=username).exists():
            messages.error(request,'Username already exists')
        elif User.objects.filter(email=email).exists():
            messages.error(request,'Email already exists')
        elif not enrollment:
            messages.error(request,'Enrollment number is required')
        elif Profile.objects.filter(enrollment=enrollment).exists():
            messages.error(request,'Enrollment number already exists')
        elif not semester:
            messages.error(request,'Please select a semester')
        else:
            user=User.objects.create_user(username=username,email=email,password=password)
            # Refresh user to ensure profile is created by signal
            user.refresh_from_db()
            # Save enrollment and semester to user profile
            profile, created = Profile.objects.get_or_create(user=user)
            profile.enrollment = enrollment
            profile.semester = semester
            profile.save()
            messages.success(request,'Registration successful.You can login now')
            return redirect('login')
    
    return render(request,'register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # Redirect to user dashboard
    
    next_url = request.GET.get('next', 'dashboard')  # Get the next URL or default to 'dashboard'

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(next_url)  # Redirect to the next URL after login
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html', {'next': next_url})

def logout_view(request):
    logout(request)
    return redirect('index')


@login_required(login_url='login')
def dashboard(request):
    # Get user's exam records
    data_dir = os.path.join(settings.BASE_DIR, 'data')
    user_records = []
    try:
        if os.path.isdir(data_dir):
            for fname in os.listdir(data_dir):
                if not fname.lower().endswith('.json'):
                    continue
                path = os.path.join(data_dir, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        rec = json.load(f)
                        if rec.get('username') == request.user.username:
                            rec['file'] = rec.get('subject', 'Unknown Subject')  # Replace numerical filename with subject name
                            user_records.append(rec)
                except Exception:
                    continue
    except Exception:
        pass

    # Get user's semester from profile
    user_semester = ''
    if hasattr(request.user, 'profile') and request.user.profile.semester:
        user_semester = request.user.profile.semester

    # Render the enhanced user dashboard page
    return render(request, 'User_dashboard.html', {
        'user_records': user_records,  # Pass user-specific records
        'user_semester': user_semester  # Pass user's semester
    })

def admin_login(request):
    if request.method == 'POST':
        admin_id = request.POST.get('admin_id')
        password = request.POST.get('password')
        if admin_id == 'admin' and password == '123':
            # mark session as site admin (simple site-level admin flag used by Admin dashboard)
            request.session['is_site_admin'] = True
            # Redirect to the admin dashboard
            return redirect('/Admin_dashboard/')  # Redirect to admin dashboard
        else:
            messages.error(request, 'Invalid admin ID or password.')
    return render(request, 'Admin.html')

def is_approved_faculty(username):
    """Check if a username belongs to an approved faculty member."""
    requests_path = os.path.join(settings.BASE_DIR, 'data', 'registration_requests.json')
    if not os.path.exists(requests_path):
        return False
    
    try:
        with open(requests_path, 'r', encoding='utf-8') as f:
            registration_requests = json.load(f)
        
        for req in registration_requests:
            req_username = (req.get('username') or '').strip()
            if req_username == username:
                status = req.get('status', 'pending')
                approved = req.get('approved', False)
                return status == 'approved' or approved is True
    except Exception:
        pass
    
    return False

def faculty_login(request):
    """Authenticate faculty using Django auth for approved faculty members."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Check hardcoded faculty account (backward compatibility)
        if username == 'faculty1' and password == 'faculty123':
            request.session['is_faculty'] = True
            request.session['faculty_username'] = username
            return redirect('faculty_dashboard')
        
        # Try Django authentication for approved faculty
        user = authenticate(request, username=username, password=password)
        if user and is_approved_faculty(username):
            # Login the user using Django's authentication system
            login(request, user)
            # Also set session flags for backward compatibility
            request.session['is_faculty'] = True
            request.session['faculty_username'] = username
            messages.success(request, f'Welcome back, {username}!')
            return redirect('faculty_dashboard')
        else:
            if user and not is_approved_faculty(username):
                messages.error(request, 'Your faculty registration is pending approval.')
            else:
                messages.error(request, 'Invalid faculty username or password.')

    return render(request, 'faculty_login.html')

def faculty_dashboard(request):
    """Simple dashboard that requires the session-based faculty login or Django auth."""
    # Check if user is authenticated as approved faculty OR has session flag
    is_faculty_session = request.session.get('is_faculty', False)
    is_authenticated_faculty = (
        request.user.is_authenticated and 
        is_approved_faculty(request.user.username)
    )
    
    if not (is_faculty_session or is_authenticated_faculty):
        messages.error(request, 'Please sign in as faculty to continue.')
        return redirect('faculty_login')
    
    # Get faculty username from session or authenticated user
    faculty_username = request.session.get('faculty_username') or request.user.username
    
    # Get faculty user object and assigned subjects
    faculty_user = None
    assigned_subjects = []
    if request.user.is_authenticated:
        faculty_user = request.user
    elif faculty_username:
        try:
            faculty_user = User.objects.get(username=faculty_username)
        except User.DoesNotExist:
            pass
    
    if faculty_user:
        assignments = FacultySubjectAssignment.objects.filter(
            faculty=faculty_user, 
            is_active=True
        ).values_list('subject', flat=True)
        assigned_subjects = list(assignments)

    # Provide a quick overview that might interest faculty users
    total_students = User.objects.count()
    recent_users = User.objects.order_by('-date_joined')[:5]

    # Sample of recent exam records from JSON files for quick glance
    data_dir = os.path.join(settings.BASE_DIR, 'data')
    recent_records = []
    try:
        if os.path.isdir(data_dir):
            json_files = sorted(
                [f for f in os.listdir(data_dir) if f.lower().endswith('.json')],
                reverse=True
            )[:5]
            for fname in json_files:
                path = os.path.join(data_dir, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        rec = json.load(f)
                        rec['file'] = fname
                        recent_records.append(rec)
                except Exception:
                    continue
    except Exception:
        recent_records = []

    return render(request, 'Faculty_dashboard.html', {
        'faculty_username': faculty_username,
        'total_students': total_students,
        'recent_users': recent_users,
        'recent_records': recent_records,
        'assigned_subjects': assigned_subjects,
    })

def faculty_logout(request):
    """Clear faculty-specific session state and logout Django user if authenticated."""
    # Logout Django user if authenticated
    if request.user.is_authenticated:
        logout(request)
    
    # Clear session flags
    try:
        request.session.pop('is_faculty', None)
        request.session.pop('faculty_username', None)
    except Exception:
        pass

    return redirect('index')

def faculty_results(request):
    """Allow faculty to review submitted exams and store marks."""
    # Check if user is authenticated as approved faculty OR has session flag
    is_faculty_session = request.session.get('is_faculty', False)
    is_authenticated_faculty = (
        request.user.is_authenticated and 
        is_approved_faculty(request.user.username)
    )
    
    if not (is_faculty_session or is_authenticated_faculty):
        messages.error(request, 'Please sign in as faculty to continue.')
        return redirect('faculty_login')
    
    # Get faculty username from session or authenticated user
    faculty_username = request.session.get('faculty_username') or request.user.username
    
    # Get faculty user object for assignment checking
    faculty_user = None
    if request.user.is_authenticated:
        faculty_user = request.user
    else:
        # Faculty logged in via session
        if faculty_username:
            try:
                faculty_user = User.objects.get(username=faculty_username)
            except User.DoesNotExist:
                pass
    
    # Get assigned subjects for this faculty
    assigned_subjects = []
    if faculty_user:
        assignments = FacultySubjectAssignment.objects.filter(
            faculty=faculty_user, 
            is_active=True
        ).values_list('subject', flat=True)
        assigned_subjects = list(assignments)

    # Handle mark submission
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        attempt_id = request.POST.get('attempt_id', '').strip()
        subject = request.POST.get('subject', '').strip()
        semester = request.POST.get('semester', '').strip()
        exam_date_raw = request.POST.get('exam_date', '').strip()
        marks_val = request.POST.get('marks')
        max_marks_val = request.POST.get('max_marks')
        remarks = request.POST.get('remarks', '').strip()

        if not username or not attempt_id or not subject:
            messages.error(request, 'Missing username, attempt, or subject.')
            return redirect('faculty_results')
        
        # Check if faculty is assigned to this subject
        if faculty_user and assigned_subjects and subject not in assigned_subjects:
            messages.error(request, f'You are not assigned to grade {subject}. Please contact admin.')
            return redirect('faculty_results')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, f'User {username} not found.')
            return redirect('faculty_results')

        # Parse decimal fields gracefully
        def parse_decimal(value):
            if value in (None, '',):
                return None
            try:
                return Decimal(value)
            except Exception:
                return None

        marks = parse_decimal(marks_val)
        max_marks = parse_decimal(max_marks_val)

        exam_date_obj = None
        if exam_date_raw:
            try:
                exam_date_obj = datetime.fromisoformat(exam_date_raw).date()
            except Exception:
                # Attempt to parse YYYY-MM-DD manually
                try:
                    exam_date_obj = datetime.strptime(exam_date_raw, '%Y-%m-%d').date()
                except Exception:
                    exam_date_obj = None

        result, _created = ExamResult.objects.get_or_create(
            user=user,
            attempt_id=attempt_id,
            defaults={'subject': subject}
        )
        result.subject = subject
        result.semester = semester
        result.exam_date = exam_date_obj
        result.marks_obtained = marks
        result.max_marks = max_marks
        result.remarks = remarks
        result.graded_by = faculty_username
        result.save()

        messages.success(request, f'Marks saved for {username} ({subject}).')
        return redirect('faculty_results')

    # Build overview of submitted exams
    data_dir = os.path.join(settings.BASE_DIR, 'data')
    exam_entries = []
    
    if os.path.isdir(data_dir):
        try:
            json_files = sorted(
                [f for f in os.listdir(data_dir) if f.lower().endswith('.json')],
                reverse=True
            )
            for fname in json_files:
                # Skip registration_requests.json - it's not an exam file
                if fname == 'registration_requests.json':
                    continue
                    
                path = os.path.join(data_dir, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        rec = json.load(f)
                except Exception:
                    continue

                username = rec.get('username')
                subject = rec.get('subject') or 'N/A'
                saved_at = rec.get('saved_at') or fname
                attempt_id = str(saved_at)[:64]
                exam_date_display = rec.get('date', '')
                exam_date_iso = ''
                if isinstance(exam_date_display, str) and exam_date_display:
                    try:
                        exam_date_iso = datetime.fromisoformat(exam_date_display).date().isoformat()
                    except Exception:
                        # Attempt to parse formats like '14 November 2025'
                        try:
                            exam_date_iso = datetime.strptime(exam_date_display, '%d %B %Y').date().isoformat()
                        except Exception:
                            try:
                                exam_date_iso = datetime.strptime(exam_date_display, '%d %b %Y').date().isoformat()
                            except Exception:
                                exam_date_iso = ''
                semester = rec.get('semester', '')

                if not username:
                    continue

                user = User.objects.filter(username=username).first()
                if not user:
                    continue
                
                # Filter by assigned subjects if faculty has assignments
                if assigned_subjects and subject not in assigned_subjects:
                    continue

                existing = ExamResult.objects.filter(user=user, attempt_id=attempt_id).first()
                exam_entries.append({
                    'username': username,
                    'subject': subject,
                    'attempt_id': attempt_id,
                    'file': fname,
                    'exam_date': exam_date_display,
                    'exam_date_iso': exam_date_iso,
                    'semester': semester,
                    'saved_at': saved_at,
                    'marks': existing.marks_obtained if existing else '',
                    'max_marks': existing.max_marks if existing else '',
                    'remarks': existing.remarks if existing else '',
                    'graded_by': existing.graded_by if existing else '',
                    'graded_at': existing.graded_at if existing else None,
                })
        except Exception as e:
            # Log the error but continue gracefully
            import traceback
            traceback.print_exc()

    return render(request, 'Faculty_results.html', {
        'faculty_username': faculty_username,
        'exam_entries': exam_entries,
        'assigned_subjects': assigned_subjects,
    })


@csrf_exempt
@require_POST
def api_submit_grade(request):
    """API endpoint for faculty to submit grades for student exams."""
    try:
        # Check if user is authenticated as faculty
        is_faculty_session = request.session.get('is_faculty', False)
        is_authenticated_faculty = (
            request.user.is_authenticated and 
            is_approved_faculty(request.user.username)
        )
        
        if not (is_faculty_session or is_authenticated_faculty):
            return JsonResponse({'success': False, 'message': 'Unauthorized. Please login as faculty.'}, status=403)
        
        # Get faculty username
        faculty_username = request.session.get('faculty_username') or request.user.username
        
        # Get faculty user object
        faculty_user = None
        if request.user.is_authenticated:
            faculty_user = request.user
        elif faculty_username:
            try:
                faculty_user = User.objects.get(username=faculty_username)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Faculty user not found.'}, status=400)
        
        # Parse request data
        username = request.POST.get('username', '').strip()
        attempt_id = request.POST.get('attempt_id', '').strip()
        subject = request.POST.get('subject', '').strip()
        semester = request.POST.get('semester', '').strip()
        exam_date_raw = request.POST.get('exam_date', '').strip()
        marks_val = request.POST.get('marks')
        max_marks_val = request.POST.get('max_marks')
        remarks = request.POST.get('remarks', '').strip()
        
        # Validate required fields
        if not username or not attempt_id or not subject:
            return JsonResponse({'success': False, 'message': 'Missing required fields (username, attempt_id, subject).'}, status=400)
        
        # Check if faculty is assigned to this subject
        if faculty_user:
            assigned_subjects = FacultySubjectAssignment.objects.filter(
                faculty=faculty_user,
                subject=subject,
                is_active=True
            ).exists()
            
            if not assigned_subjects:
                return JsonResponse({
                    'success': False,
                    'message': f'You are not assigned to grade "{subject}". Please contact admin.'
                }, status=403)
        
        # Get student user
        try:
            student_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': f'Student {username} not found.'}, status=400)
        
        # Parse decimal fields
        def parse_decimal(value):
            if value in (None, ''):
                return None
            try:
                return Decimal(value)
            except Exception:
                return None
        
        marks = parse_decimal(marks_val)
        max_marks = parse_decimal(max_marks_val)
        
        # Parse exam date
        exam_date_obj = None
        if exam_date_raw:
            try:
                exam_date_obj = datetime.fromisoformat(exam_date_raw).date()
            except Exception:
                try:
                    exam_date_obj = datetime.strptime(exam_date_raw, '%Y-%m-%d').date()
                except Exception:
                    exam_date_obj = None
        
        # Save grade
        result, created = ExamResult.objects.get_or_create(
            user=student_user,
            attempt_id=attempt_id,
            defaults={'subject': subject}
        )
        result.subject = subject
        result.semester = semester
        result.exam_date = exam_date_obj
        result.marks_obtained = marks
        result.max_marks = max_marks
        result.remarks = remarks
        result.graded_by = faculty_username
        result.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Grade saved for {username} ({subject}).'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)


def admin_dashboard(request):
    # Fetch all active sessions
    sessions = Session.objects.filter(expire_date__gte=now())
    online_user_ids = []

    for session in sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')
        if user_id:
            online_user_ids.append(user_id)

    # Fetch all registered users
    all_users = User.objects.all()

    # Add online status to each user
    users_with_status = [
        {'user': user, 'is_online': str(user.id) in online_user_ids}
        for user in all_users
    ]

    # Load exam records from data directory
    exam_records = []
    try:
        data_dir = os.path.join(settings.BASE_DIR, 'data')
        if os.path.isdir(data_dir):
            for name in os.listdir(data_dir):
                if not name.lower().endswith('.json'):
                    continue
                filepath = os.path.join(data_dir, name)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        record = json.load(f)
                        record['file'] = name
                        # Prepare a human-friendly saved_at display (parse token like '20251004-125200-768943')
                        saved_token = record.get('saved_at')
                        record['saved_at_display'] = ''
                        if isinstance(saved_token, str) and saved_token:
                            try:
                                ymd = saved_token.split('-', 1)[0]
                                if len(ymd) >= 8 and ymd.isdigit():
                                    year = int(ymd[0:4])
                                    month = int(ymd[4:6])
                                    day = int(ymd[6:8])
                                    import calendar
                                    mon_name = calendar.month_name[month] if 1 <= month <= 12 else str(month)
                                    record['saved_at_display'] = f"{str(day).zfill(2)} {mon_name} {year}"
                            except Exception:
                                record['saved_at_display'] = ''
                        if not record.get('saved_at_display') and record.get('saved_at'):
                            record['saved_at_display'] = str(record.get('saved_at'))

                        exam_records.append(record)
                except Exception:
                    # Skip unreadable or malformed files
                    continue
        # Sort newest first by saved_at if available
        exam_records.sort(key=lambda r: r.get('saved_at', ''), reverse=True)
    except Exception:
        exam_records = []

    # Compute additional admin statistics
    total_students = all_users.count()
    active_count = all_users.filter(is_active=True).count()
    inactive_count = total_students - active_count

    # Count applied exams by number of JSON files in data/
    total_applied_exams = 0
    try:
        data_dir = os.path.join(settings.BASE_DIR, 'data')
        if os.path.isdir(data_dir):
            total_applied_exams = len([n for n in os.listdir(data_dir) if n.lower().endswith('.json')])
    except Exception:
        total_applied_exams = 0

    # Example project insights (you can customize or compute more)
    project_insights = {
        'avg_exams_per_user': (total_applied_exams / total_students) if total_students else 0,
        'recent_active_sessions': len(online_user_ids),
        'data_files': total_applied_exams,
    }

    # --- Unlock slot management: allow simple site-admin (session flag) to create slots from dashboard ---
    # If admin created slot via dashboard form
    if request.method == 'POST' and request.session.get('is_site_admin'):
        action = request.POST.get('action')
        if action == 'create_slot':
            date_str = request.POST.get('date')
            try:
                slot_date = datetime.fromisoformat(date_str).date()
                UnlockSlot.objects.create(date=slot_date, created_by=None)
                messages.success(request, f'Created unlock slot for {slot_date}')
            except Exception as e:
                messages.error(request, f'Failed to create slot: {e}')
        elif action == 'assign_subject':
            # Handle subject assignment to faculty
            faculty_username = request.POST.get('faculty_username', '').strip()
            subject = request.POST.get('subject', '').strip()
            assign_action = request.POST.get('assign_action', 'assign').strip()
            
            if not faculty_username or not subject:
                messages.error(request, 'Faculty and subject are required.')
            else:
                try:
                    faculty_user = User.objects.get(username=faculty_username)
                    if assign_action == 'assign':
                        assignment, created = FacultySubjectAssignment.objects.get_or_create(
                            faculty=faculty_user,
                            subject=subject,
                            defaults={
                                'assigned_by': request.user if request.user.is_authenticated else None,
                                'is_active': True
                            }
                        )
                        if not created:
                            assignment.is_active = True
                            assignment.assigned_by = request.user if request.user.is_authenticated else None
                            assignment.save()
                        messages.success(request, f'Assigned {subject} to {faculty_username}')
                    elif assign_action == 'unassign':
                        FacultySubjectAssignment.objects.filter(
                            faculty=faculty_user,
                            subject=subject
                        ).update(is_active=False)
                        messages.success(request, f'Unassigned {subject} from {faculty_username}')
                except User.DoesNotExist:
                    messages.error(request, f'Faculty {faculty_username} not found.')
                except Exception as e:
                    messages.error(request, f'Error assigning subject: {e}')

    # provide unlock slots to the template (deduplicated by date)
    # Only show dates up to and including today (no future dates for attendance)
    try:
        today_date = date.today()
        today_slot = UnlockSlot.objects.filter(date=today_date).order_by('id').first()
        if today_slot is None:
            try:
                today_slot = UnlockSlot.objects.create(
                    date=today_date,
                    created_by=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
                    is_active=True,
                )
            except Exception:
                today_slot = UnlockSlot.objects.filter(date=today_date).order_by('id').first()

        # Only get active slots (include all dates for attendance download)
        all_slots = UnlockSlot.objects.filter(is_active=True).order_by('-date')
        
        # Deduplicate by date - keep only one slot per date
        seen_dates = set()
        unlock_slots = []
        for slot in all_slots:
            if slot.date and slot.date not in seen_dates:
                unlock_slots.append(slot)
                seen_dates.add(slot.date)
        
        # Sort by date descending (most recent dates first)
        unlock_slots.sort(key=lambda s: s.date if s.date else date.min, reverse=True)
    except Exception:
        unlock_slots = []
        today_slot = None

    # Build subject options list from exam results and JSON data files
    subject_options = []
    try:
        subject_set = set(
            s.strip() for s in ExamResult.objects.exclude(subject__isnull=True).exclude(subject__exact='').values_list('subject', flat=True)
        )
        data_dir = os.path.join(settings.BASE_DIR, 'data')
        if os.path.isdir(data_dir):
            for name in os.listdir(data_dir):
                if not name.lower().endswith('.json'):
                    continue
                path = os.path.join(data_dir, name)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        record = json.load(f)
                        subject = str(record.get('subject', '')).strip()
                        if subject:
                            subject_set.add(subject)
                except Exception:
                    continue

        banned_subjects = {'math', 'maths', 'mathematics', 'english', 'science', 'scince', 'meth'}
        curated_subjects = {'DWDM', 'UIUX'}
        cleaned = set()
        for subj in subject_set:
            if not subj:
                continue
            if subj.lower() in banned_subjects:
                continue
            cleaned.add(subj)
        cleaned.update(curated_subjects)

        subject_options = sorted(cleaned, key=lambda x: x.lower())
    except Exception:
        subject_options = ['DWDM', 'UIUX']

    # Collect graded exam results for student marks tab
    try:
        student_marks = ExamResult.objects.select_related('user').order_by('-graded_at')
    except Exception:
        student_marks = []

    # Load registration requests
    requests_dir = os.path.join(settings.BASE_DIR, 'data', 'registration_requests.json')
    registration_requests = []
    try:
        if os.path.exists(requests_dir):
            with open(requests_dir, 'r', encoding='utf-8') as f:
                registration_requests = json.load(f)
                for req in registration_requests:
                    status = req.get('status')
                    if not status:
                        req['status'] = 'approved' if req.get('approved') else 'pending'
                    if not req.get('submitted_at'):
                        req['submitted_at'] = req.get('status_updated_at', '')
                registration_requests.sort(key=lambda r: r.get('submitted_at') or '', reverse=True)
    except Exception as e:
        messages.error(request, f'Error loading registration requests: {e}')

    # Get approved faculty list
    approved_faculty = []
    try:
        for req in registration_requests:
            if req.get('status') == 'approved' or req.get('approved'):
                username = req.get('username', '').strip()
                if username:
                    try:
                        faculty_user = User.objects.get(username=username)
                        approved_faculty.append(faculty_user)
                    except User.DoesNotExist:
                        pass
    except Exception:
        pass

    # Get all subject assignments
    all_assignments = FacultySubjectAssignment.objects.filter(is_active=True).select_related('faculty', 'assigned_by')
    assignments_by_faculty = {}
    for assignment in all_assignments:
        faculty_username = assignment.faculty.username
        if faculty_username not in assignments_by_faculty:
            assignments_by_faculty[faculty_username] = []
        assignments_by_faculty[faculty_username].append(assignment.subject)
    
    # Create a list of faculty with their assignments for easier template rendering
    faculty_with_assignments = []
    for faculty in approved_faculty:
        faculty_with_assignments.append({
            'faculty': faculty,
            'subjects': assignments_by_faculty.get(faculty.username, [])
        })

    return render(request, 'Admin_dashboard.html', {
        'users_with_status': users_with_status,
        'total_users': total_students,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'total_applied_exams': total_applied_exams,
        'exam_records': exam_records,
        'project_insights': project_insights,
        'unlock_slots': unlock_slots,
        'today_slot_id': today_slot.id if today_slot else None,
        'student_marks': student_marks,
        'subject_options': subject_options,
        'registration_requests': registration_requests,
        'approved_faculty': approved_faculty,
        'assignments_by_faculty': assignments_by_faculty,
        'faculty_with_assignments': faculty_with_assignments
    })

def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        new_username = request.POST.get('username')
        if new_username.strip():  # Ensure the username is not empty or whitespace
            user.username = new_username
            user.save()
            # Re-authenticate the user if the logged-in user is being edited
            if request.user.id == user.id:
                password = request.POST.get('password')  # Retrieve the password from the form
                if password:
                    authenticated_user = authenticate(request, username=new_username, password=password)
                    if authenticated_user:
                        login(request, authenticated_user)
                        messages.success(request, 'User updated and re-authenticated successfully.')
                    else:
                        messages.error(request, 'Re-authentication failed. Please log in again.')
                        return redirect('logout')  # Log out the user if re-authentication fails
            else:
                messages.success(request, 'User updated successfully.')
            return redirect('Admin_dashboard')  # Redirect to the user list (admin dashboard)
        else:
            messages.error(request, 'Username cannot be empty or whitespace.')
    return render(request, 'edit_user.html', {'user': user})


@login_required(login_url='login')
def profile_view(request):
    """Render the user's profile page showing all details and avatar."""
    profile = getattr(request.user, 'profile', None)
    return render(request, 'profile.html', {'user': request.user, 'profile': profile})


@login_required(login_url='login')
def edit_profile(request):
    """Handle profile edits and avatar upload.

    Accepts POST fields: display_name, email (optional). Accepts file input 'avatar'.
    """
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        display_name = request.POST.get('display_name', '').strip()
        email = request.POST.get('email', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        enrollment = request.POST.get('enrollment', '').strip()

        # Validate required fields
        if not full_name:
            messages.error(request, 'Full name is required.')
            return render(request, 'profile_edit.html', {'user': request.user, 'profile': profile})
        if not enrollment:
            messages.error(request, 'Enrollment is required.')
            return render(request, 'profile_edit.html', {'user': request.user, 'profile': profile})

        if display_name:
            if profile:
                profile.display_name = display_name
            else:
                # Safety: create profile if missing
                from .models import Profile
                profile = Profile.objects.create(user=request.user, display_name=display_name)

        if email:
            request.user.email = email
            request.user.save()

        # Handle avatar upload
        avatar = request.FILES.get('avatar')
        if avatar and profile is not None:
            # Save under media/avatars/<username>-<timestamp>-originalname
            import time
            safe_name = ''.join(c for c in request.user.username if c.isalnum() or c in ('-', '_')) or 'user'
            ts = int(time.time())
            avatar_subpath = f'avatars/{safe_name}_{ts}_{avatar.name}'
            saved_path = default_storage.save(avatar_subpath, ContentFile(avatar.read()))
            # Normalize path separators to URL-friendly forward slashes (important on Windows)
            saved_path_url = saved_path.replace('\\', '/')
            # store the accessible media URL
            profile.avatar_url = settings.MEDIA_URL.rstrip('/') + '/' + saved_path_url

        # Save the new fields
        if profile:
            profile.full_name = full_name or profile.full_name
            profile.enrollment = enrollment or profile.enrollment

        if profile:
            profile.save()

        # After saving profile edits, redirect the user to their dashboard
        return redirect('dashboard')

    # not POST -> render a simple edit page
    return render(request, 'profile_edit.html', {'user': request.user, 'profile': profile})


@login_required(login_url='login')
def my_exams(request):
    """Show the logged-in user's saved exam records (from data/ JSON files)."""
    data_dir = os.path.join(settings.BASE_DIR, 'data')
    records = []
    try:
        if os.path.isdir(data_dir):
            for fname in os.listdir(data_dir):
                if not fname.lower().endswith('.json'):
                    continue
                path = os.path.join(data_dir, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        rec = json.load(f)
                        rec['file'] = fname
                        # If this record belongs to the current user, prepare display fields
                        if rec.get('username') == request.user.username:
                            # Attempt to parse a saved_at token like '20251004-125200-768943'
                            saved_token = rec.get('saved_at')
                            rec['saved_at_display'] = ''
                            if isinstance(saved_token, str) and saved_token:
                                # Expect token starting with YYYYMMDD
                                try:
                                    # Extract leading 8 digits for date
                                    ymd = saved_token.split('-', 1)[0]
                                    if len(ymd) >= 8 and ymd.isdigit():
                                        year = int(ymd[0:4])
                                        month = int(ymd[4:6])
                                        day = int(ymd[6:8])
                                        # Format like '09 October 2025'
                                        import calendar
                                        mon_name = calendar.month_name[month] if 1 <= month <= 12 else str(month)
                                        rec['saved_at_display'] = f"{str(day).zfill(2)} {mon_name} {year}"
                                except Exception:
                                    # leave display blank on parse failure
                                    rec['saved_at_display'] = ''
                            # If no parsed display, fall back to raw token
                            if not rec.get('saved_at_display') and rec.get('saved_at'):
                                rec['saved_at_display'] = str(rec.get('saved_at'))

                            records.append(rec)
                except Exception:
                    continue
        records.sort(key=lambda r: r.get('saved_at',''), reverse=True)
    except Exception:
        records = []

    # Detect whether server supports PDF generation (reportlab available)
    try:
        import importlib
        importlib.import_module('reportlab.pdfgen.canvas')
        pdf_enabled = True
    except Exception as e:
        pdf_enabled = False
        # Log the error for debugging (optional)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f'PDF generation disabled: reportlab not available - {str(e)}')

    return render(request, 'my_exams.html', {'records': records, 'pdf_enabled': pdf_enabled})


@login_required(login_url='login')
def download_exam(request, filename):
    # sanitize filename to avoid directory traversal
    safe = os.path.basename(filename)
    path = os.path.join(settings.BASE_DIR, 'data', safe)
    if not os.path.isfile(path):
        from django.http import Http404
        raise Http404('File not found')

    # verify ownership
    try:
        with open(path, 'r', encoding='utf-8') as f:
            rec = json.load(f)
            if rec.get('username') != request.user.username:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden('Not allowed')
    except Exception:
        from django.http import Http404
        raise Http404('Invalid file')

    from django.http import FileResponse
    # If user requested PDF, try to render a simple PDF from the JSON
    if request.GET.get('format') == 'pdf':
        try:
            import importlib
            pages_mod = importlib.import_module('reportlab.lib.pagesizes')
            platypus_mod = importlib.import_module('reportlab.platypus')
            styles_mod = importlib.import_module('reportlab.lib.styles')
            colors_mod = importlib.import_module('reportlab.lib.colors')
            units_mod = importlib.import_module('reportlab.lib.units')
            BytesIO_mod = importlib.import_module('io')

            A4 = getattr(pages_mod, 'A4')
            SimpleDocTemplate = getattr(platypus_mod, 'SimpleDocTemplate')
            Paragraph = getattr(platypus_mod, 'Paragraph')
            Spacer = getattr(platypus_mod, 'Spacer')
            Table = getattr(platypus_mod, 'Table')
            TableStyle = getattr(platypus_mod, 'TableStyle')
            getSampleStyleSheet = getattr(styles_mod, 'getSampleStyleSheet')
            colors = colors_mod

            buffer = BytesIO_mod.BytesIO()



            doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            normal = styles['Normal']

            elems = []
            elems.append(Paragraph('Exam Record', title_style))
            elems.append(Spacer(1, 12))

            # build table data: key / value
            data = [['Field', 'Value']]

            # Always prefer profile details over username in the PDF
            prof = getattr(request.user, 'profile', None)
            full_name_val = ''
            enrollment_val = ''
            if prof is not None:
                full_name_val = getattr(prof, 'full_name', '') or getattr(prof, 'display_name', '') or ''
                enrollment_val = getattr(prof, 'enrollment', '') or ''

            if full_name_val:
                data.append(['Full name', str(full_name_val)])
            if enrollment_val:
                data.append(['Enrollment', str(enrollment_val)])

            # Include exam specifics from the saved record
            preferred_keys = ['semester', 'subject', 'date', 'saved_at']
            for k in preferred_keys:
                if k in rec:
                    # Format semester display
                    if k == 'semester':
                        semester_val = str(rec.get(k, ''))
                        # Convert semester1 to Semester 1, etc.
                        if semester_val.startswith('semester'):
                            num = semester_val.replace('semester', '')
                            data.append(['Semester', f'Semester {num}'])
                        else:
                            data.append(['Semester', semester_val])
                    else:
                        data.append([k.capitalize(), str(rec.get(k, ''))])

            # include any other keys except username, approved, and already shown fields
            for k, v in rec.items():
                if k in ('username', 'full_name', 'enrollment', 'approved'):
                    continue
                if k not in preferred_keys:
                    data.append([str(k), str(v)])

            table = Table(data, colWidths=[120, doc.width - 120])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.Color(0.12,0.15,0.2)),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.Color(0.2,0.25,0.3)),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))

            elems.append(table)
            doc.build(elems)
            buffer.seek(0)
            return FileResponse(buffer, as_attachment=True, filename=safe.rsplit('.',1)[0] + '.pdf', content_type='application/pdf')
        except Exception as e:
            # PDF generation failed or reportlab not installed; fall back to JSON download
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'PDF generation failed: {str(e)}')
            # Return JSON file instead
            return FileResponse(open(path, 'rb'), as_attachment=True, filename=safe)

    return FileResponse(open(path, 'rb'), as_attachment=True, filename=safe)


@login_required(login_url='login')
def download_multiple_exams(request):
    """Generate a single PDF containing multiple exam records."""
    if request.method != 'POST':
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest('Invalid method')
    
    filenames = request.POST.getlist('filenames')
    if not filenames:
        from django.http import JsonResponse
        return JsonResponse({'success': False, 'error': 'No files selected'}, status=400)
    
    data_dir = os.path.join(settings.BASE_DIR, 'data')
    records = []
    
    # Load and verify all selected files
    for filename in filenames:
        safe = os.path.basename(filename)
        path = os.path.join(data_dir, safe)
        
        if not os.path.isfile(path):
            continue
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                rec = json.load(f)
                # Verify ownership
                if rec.get('username') == request.user.username:
                    records.append(rec)
        except Exception:
            continue
    
    if not records:
        from django.http import JsonResponse
        return JsonResponse({'success': False, 'error': 'No valid exam records found'}, status=400)
    
    # Generate PDF with all records
    try:
        import importlib
        pages_mod = importlib.import_module('reportlab.lib.pagesizes')
        platypus_mod = importlib.import_module('reportlab.platypus')
        styles_mod = importlib.import_module('reportlab.lib.styles')
        colors_mod = importlib.import_module('reportlab.lib.colors')
        BytesIO_mod = importlib.import_module('io')
        
        A4 = getattr(pages_mod, 'A4')
        SimpleDocTemplate = getattr(platypus_mod, 'SimpleDocTemplate')
        Paragraph = getattr(platypus_mod, 'Paragraph')
        Spacer = getattr(platypus_mod, 'Spacer')
        Table = getattr(platypus_mod, 'Table')
        TableStyle = getattr(platypus_mod, 'TableStyle')
        getSampleStyleSheet = getattr(styles_mod, 'getSampleStyleSheet')
        colors = colors_mod
        
        buffer = BytesIO_mod.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        normal = styles['Normal']
        
        elems = []
        
        # Get user profile info (shown once at the top)
        prof = getattr(request.user, 'profile', None)
        full_name_val = ''
        enrollment_val = ''
        if prof is not None:
            full_name_val = getattr(prof, 'full_name', '') or getattr(prof, 'display_name', '') or ''
            enrollment_val = getattr(prof, 'enrollment', '') or ''
        
        # Main title
        elems.append(Paragraph('Exam Records Receipt', title_style))
        elems.append(Spacer(1, 12))
        
        # User info (if available)
        if full_name_val or enrollment_val:
            user_info = []
            if full_name_val:
                user_info.append(f'<b>Full Name:</b> {full_name_val}')
            if enrollment_val:
                user_info.append(f'<b>Enrollment:</b> {enrollment_val}')
            if user_info:
                elems.append(Paragraph('<br/>'.join(user_info), normal))
                elems.append(Spacer(1, 12))
        
        # Build single table with all exam records
        # Collect all unique keys from all records to determine columns
        all_keys = set()
        for rec in records:
            for k in rec.keys():
                if k not in ('username', 'full_name', 'enrollment', 'approved'):
                    all_keys.add(k)
        
        # Define preferred column order
        preferred_order = ['semester', 'subject', 'date', 'saved_at']
        ordered_keys = []
        for k in preferred_order:
            if k in all_keys:
                ordered_keys.append(k)
                all_keys.remove(k)
        # Add remaining keys
        ordered_keys.extend(sorted(all_keys))
        
        # Build table header with formatted column names
        header_row = []
        for k in ordered_keys:
            if k == 'semester':
                header_row.append('Semester')
            else:
                header_row.append(k.capitalize().replace('_', ' '))
        table_data = [header_row]
        
        # Add rows for each exam record
        for rec in records:
            row = []
            for k in ordered_keys:
                value = rec.get(k, '')
                # Format semester display
                if k == 'semester' and value:
                    if isinstance(value, str) and value.startswith('semester'):
                        num = value.replace('semester', '')
                        value = f'Semester {num}'
                # Format saved_at if it's a timestamp
                elif k == 'saved_at' and isinstance(value, str) and value:
                    try:
                        ymd = value.split('-', 1)[0]
                        if len(ymd) >= 8 and ymd.isdigit():
                            year = int(ymd[0:4])
                            month = int(ymd[4:6])
                            day = int(ymd[6:8])
                            import calendar
                            mon_name = calendar.month_name[month] if 1 <= month <= 12 else str(month)
                            value = f"{str(day).zfill(2)} {mon_name} {year}"
                    except Exception:
                        pass
                row.append(str(value) if value else '')
            table_data.append(row)
        
        # Calculate column widths (distribute evenly)
        num_cols = len(ordered_keys)
        col_width = (doc.width - 40) / num_cols if num_cols > 0 else doc.width
        col_widths = [col_width] * num_cols
        
        # Create table
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.Color(0.12,0.15,0.2)),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.Color(0.2,0.25,0.3)),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        
        elems.append(table)
        
        doc.build(elems)
        buffer.seek(0)
        
        # Generate filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"exams_{request.user.username}_{timestamp}.pdf"
        
        from django.http import FileResponse
        return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'PDF generation failed for multiple exams: {str(e)}')
        from django.http import JsonResponse
        return JsonResponse({'success': False, 'error': 'PDF generation failed'}, status=500)


@login_required(login_url='login')
def unlock_list(request):
    """Show available unlock slots and allow a logged-in user to book one."""
    available = UnlockSlot.objects.filter(is_active=True, date__gte=date.today()).order_by('date')

    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        slot = get_object_or_404(UnlockSlot, pk=slot_id)
        # Prevent duplicate booking by same user
        if UnlockBooking.objects.filter(user=request.user, slot=slot).exists():
            messages.error(request, 'You have already booked this slot.')
            return redirect('unlock_list')
        # Create booking
        UnlockBooking.objects.create(user=request.user, slot=slot)
        messages.success(request, f'Booked unlock for {slot.date}.')
        return redirect('unlock_list')

    user_bookings = UnlockBooking.objects.filter(user=request.user).select_related('slot')
    return render(request, 'unlock_list.html', {'slots': available, 'bookings': user_bookings})


def api_unlock_slots(request):
    """Return JSON array of active future unlock slots."""
    try:
        slots = UnlockSlot.objects.filter(is_active=True, date__gte=date.today()).order_by('date')
        out = []
        for s in slots:
            out.append({
                'id': s.id,
                'date': s.date.isoformat(),
                'booked': s.bookings.count(),
                'is_active': s.is_active,
            })
        # If no slots exist, return empty array (not an error)
        # The frontend will handle this gracefully
        return JsonResponse({'success': True, 'slots': out})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='login')
def api_debug_unlocks(request):
    """Return debug info: slots and bookings (for troubleshooting)."""
    try:
        slots = UnlockSlot.objects.all().order_by('date')
        slot_list = []
        for s in slots:
            slot_list.append({
                'id': s.id,
                'date': s.date.isoformat(),
                'is_active': s.is_active,
                'booked': s.bookings.count(),
                'bookers': [b.user.username for b in s.bookings.all()[:20]],
            })

        bookings = UnlockBooking.objects.select_related('slot', 'user').order_by('-booked_at')[:50]
        booking_list = []
        for b in bookings:
            booking_list.append({
                'user': b.user.username,
                'slot_date': b.slot.date.isoformat(),
                'booked_at': b.booked_at.isoformat(),
            })

        return JsonResponse({'success': True, 'slots': slot_list, 'recent_bookings': booking_list})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@csrf_exempt
def api_admin_create_slots(request):
    """API for admin to create unlock slots by date list.

    Expects JSON body: {"dates": ["YYYY-MM-DD", ...]}
    Requires either request.session['is_site_admin'] == True OR request.user.is_staff
    """
    # simple auth: allow site admin session or staff users
    allowed = False
    try:
        if request.session.get('is_site_admin'):
            allowed = True
    except Exception:
        allowed = False

    if not allowed:
        # try Django user permissions (staff/superuser)
        if request.user.is_authenticated and request.user.is_staff:
            allowed = True

    if not allowed:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

    try:
        body = json.loads(request.body.decode('utf-8') or '{}') if request.body else {}
    except Exception:
        body = {}

    dates = body.get('dates') or []
    if not isinstance(dates, list) or not dates:
        return JsonResponse({'success': False, 'error': 'Missing dates list'}, status=400)

    created = []
    errors = []
    for d in dates:
        try:
            slot_date = datetime.fromisoformat(d).date()
        except Exception:
            errors.append({'date': d, 'error': 'bad_format'})
            continue
        # avoid duplicates
        slot, created_flag = UnlockSlot.objects.get_or_create(date=slot_date, defaults={'is_active': True, 'created_by': request.user if request.user.is_authenticated else None})
        if created_flag:
            created.append(slot_date.isoformat())

    return JsonResponse({'success': True, 'created': created, 'created_count': len(created), 'errors': errors})

def api_delete_unlock_slot(request, slot_id):
    """API to delete an unlock slot"""
    # Check authorization - accept both session-based and user-based auth
    allowed = False
    
    # Check if user is authenticated via Django auth
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        allowed = True
    # Check if user is logged in as site admin via session
    elif request.session.get('is_site_admin'):
        allowed = True
    
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    try:
        slot = UnlockSlot.objects.get(id=slot_id)
        slot_date = str(slot.date)
        # Deactivate the slot instead of deleting it (soft delete)
        slot.is_active = False
        slot.save()
        return JsonResponse({'success': True, 'message': f'Deactivated slot for {slot_date}'})
    except UnlockSlot.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Slot not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def api_deactivate_unlock_slot(request, slot_id):
    """API to deactivate an unlock slot"""
    # Check authorization - accept both session-based and user-based auth
    allowed = False
    
    # Check if user is authenticated via Django auth
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        allowed = True
    # Check if user is logged in as site admin via session
    elif request.session.get('is_site_admin'):
        allowed = True
    
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    try:
        slot = UnlockSlot.objects.get(id=slot_id)
        slot.is_active = not slot.is_active
        slot.save()
        status = 'activated' if slot.is_active else 'deactivated'
        return JsonResponse({'success': True, 'message': f'Slot {status}', 'is_active': slot.is_active})
    except UnlockSlot.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Slot not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def api_update_unlock_slot(request, slot_id):
    """API to update an unlock slot"""
    # Check authorization - accept both session-based and user-based auth
    allowed = False
    
    # Check if user is authenticated via Django auth
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        allowed = True
    # Check if user is logged in as site admin via session
    elif request.session.get('is_site_admin'):
        allowed = True
    
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    try:
        body = json.loads(request.body.decode('utf-8') or '{}') if request.body else {}
    except Exception:
        body = {}
    
    try:
        slot = UnlockSlot.objects.get(id=slot_id)
        
        # Update fields
        if 'subject' in body:
            slot.subject = body['subject'].strip() or None
        if 'start_time' in body and body['start_time']:
            slot.start_time = body['start_time']
        if 'end_time' in body and body['end_time']:
            slot.end_time = body['end_time']
        if 'capacity' in body:
            try:
                slot.capacity = int(body['capacity']) or 0
            except (ValueError, TypeError):
                pass
        
        slot.save()
        return JsonResponse({'success': True, 'message': 'Slot updated', 'slot': {
            'id': slot.id,
            'date': str(slot.date),
            'subject': slot.subject or '',
            'start_time': str(slot.start_time) if slot.start_time else '',
            'end_time': str(slot.end_time) if slot.end_time else '',
            'capacity': slot.capacity,
            'is_active': slot.is_active
        }})
    except UnlockSlot.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Slot not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def api_bulk_delete_unlock_slots(request):
    """API to deactivate multiple unlock slots"""
    # Check authorization - accept both session-based and user-based auth
    allowed = False
    
    # Check if user is authenticated via Django auth
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        allowed = True
    # Check if user is logged in as site admin via session
    elif request.session.get('is_site_admin'):
        allowed = True
    
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    try:
        body = json.loads(request.body.decode('utf-8') or '{}') if request.body else {}
    except Exception:
        body = {}
    
    slot_ids = body.get('slot_ids', [])
    if not isinstance(slot_ids, list) or not slot_ids:
        return JsonResponse({'success': False, 'error': 'Missing or invalid slot_ids'}, status=400)
    
    try:
        # Deactivate slots instead of deleting them (soft delete)
        deactivated_count = UnlockSlot.objects.filter(id__in=slot_ids).update(is_active=False)
        return JsonResponse({'success': True, 'message': f'Deactivated {deactivated_count} slot(s)', 'deleted_count': deactivated_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def delete_user(request, user_id):
   
    user = get_object_or_404(User, id=user_id)

    if request.user.id == user.id:
        user.delete()
        return redirect('Admin_dashboard.html')  
    else:
        user.delete()
        messages.success(request, 'User deleted successfully.')
        # Redirect to admin dashboard and show user list
        from django.urls import reverse
        return redirect(reverse('Admin_dashboard') + '?show=user-list')


@login_required(login_url='login')
def save_exam_selection(request):
    """Persist selected exam date and subject to a new file per save.

    Expects POST with 'date' and 'subject'. Creates a data directory at the
    project root if needed, and writes a JSON file named with username and a
    timestamp to avoid collisions.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    # Accept JSON body (preferred) or form POST
    try:
        body = json.loads(request.body.decode('utf-8') or '{}') if request.body else {}
    except Exception:
        body = {}

    date_str = request.POST.get('date') or body.get('date')
    subject = request.POST.get('subject') or body.get('subject')
    
    # Get semester from user's profile instead of request
    semester = ''
    if hasattr(request.user, 'profile') and request.user.profile.semester:
        semester = request.user.profile.semester

    if not date_str or not subject:
        return JsonResponse({'success': False, 'error': 'Missing date or subject'}, status=400)
    
    if not semester:
        return JsonResponse({'success': False, 'error': 'No semester found in your profile. Please contact administrator.'}, status=400)

    # normalize whitespace and non-breaking spaces
    try:
        if isinstance(date_str, str):
            date_str = date_str.strip().replace('\u00A0', ' ')
    except Exception:
        pass

    # Parse date: accept ISO (YYYY-MM-DD) or 'DD Month YYYY'
    try:
        try:
            selected_date = datetime.fromisoformat(date_str).date()
        except Exception:
            parts = date_str.strip().split(' ')
            if len(parts) >= 3:
                day_part = parts[0]
                month_part = parts[1]
                year_part = parts[2]
                sel_day = int(day_part)
                sel_year = int(year_part)
                import calendar
                month_names = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
                month_num = month_names.get(month_part.lower(), None)
                if month_num is None:
                    month_names_short = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}
                    month_num = month_names_short.get(month_part.lower(), None)
                if month_num is None:
                    raise ValueError('Invalid month')
                selected_date = date(sel_year, month_num, sel_day)

        # No past bookings
        if selected_date < date.today():
            return JsonResponse({'success': False, 'error': 'Cannot book a previous date. Only today or future dates allowed.'}, status=400)
    except Exception as e:
        # Return the received date string to help debugging client/server mismatch
        return JsonResponse({'success': False, 'error': 'Invalid date format', 'received': date_str, 'detail': str(e)}, status=400)

    # Ensure the selected_date corresponds to an active UnlockSlot
    # Students can only book dates where admin has created an active slot
    try:
        slot = UnlockSlot.objects.filter(date=selected_date, is_active=True).first()
        if not slot:
            # Reject booking if no active slot exists for this date
            return JsonResponse({'success': False, 'error': 'This date is not available. Only dates with active slots can be booked.'}, status=403)
        
        # Check duplicate booking
        if UnlockBooking.objects.filter(user=request.user, slot=slot).exists():
            return JsonResponse({'success': False, 'error': 'You have already booked this date'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Server error checking slot availability'}, status=500)
    # Ensure data directory exists at the project root
    data_dir = os.path.join(settings.BASE_DIR, 'data')
    os.makedirs(data_dir, exist_ok=True)

    # Build a safe filename: username + timestamp
    safe_username = ''.join(c for c in request.user.username if c.isalnum() or c in ('-', '_')) or 'user'
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f"{safe_username}_{ts}.json"
    filepath = os.path.join(data_dir, filename)

    payload = {
        'username': request.user.username,
        'date': date_str,
        'subject': subject,
        'semester': semester,
        'saved_at': ts,
    }

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)

    # create booking record (if not already created above)
    try:
        UnlockBooking.objects.create(user=request.user, slot=slot)
    except IntegrityError:
        # already exists or race; ignore as we checked earlier
        pass

    return JsonResponse({'success': True, 'file': filename})

@login_required(login_url='login')
def notification_details(request):
    # No approved notifications - just render empty page
    return render(request, 'notification_details.html', {'approved_records': []})

@login_required(login_url='login')
def exam_results_view(request):
    """Display marks uploaded by faculty for the logged-in user."""
    results = ExamResult.objects.filter(user=request.user).order_by('-graded_at')
    return render(request, 'results.html', {'results': results})


def api_get_attendance(request, slot_id):
    """API endpoint to get attendance records for a specific unlock slot."""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    subject = (request.GET.get('subject') or '').strip()
    if not subject:
        return JsonResponse({'success': False, 'error': 'Subject is required'}, status=400)

    if not has_admin_or_staff_access(request):
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

    try:
        slot = UnlockSlot.objects.get(id=slot_id)
    except UnlockSlot.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Slot not found'}, status=404)
    
    # Get today's date for creating attendance records
    today = date.today()

    # Return attendance for ALL users (so admin can mark everyone present/absent)
    # Ensure consistent ascending order (by username)
    users = User.objects.all().select_related('profile').order_by('username')
    records = []

    for user in users:
        # Safely access profile fields
        prof = getattr(user, 'profile', None)
        full_name = prof.full_name if prof and getattr(prof, 'full_name', None) else ''
        enrollment = prof.enrollment if prof and getattr(prof, 'enrollment', None) else ''

        # Get or create attendance record for this user and slot
        attendance = Attendance.objects.filter(user=user, slot=slot, subject=subject).first()
        if not attendance:
            # Create attendance record for any date (current, past, or future)
            attendance = Attendance.objects.create(
                user=user,
                slot=slot,
                subject=subject,
                is_present=False
            )

        records.append({
            'username': user.username,
            'full_name': full_name,
            'enrollment': enrollment,
            'attendance_id': attendance.id,
            'is_present': attendance.is_present,
            'subject': attendance.subject,
        })

    return JsonResponse({'success': True, 'records': records})


@csrf_exempt
def api_update_attendance(request):
    """API endpoint to update attendance status."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    if not has_admin_or_staff_access(request):
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

    try:
        data = json.loads(request.body)
        attendance_id = data.get('attendance_id')
        is_present = data.get('is_present', False)

        attendance = Attendance.objects.get(id=attendance_id)
        
        # Prevent marking attendance for future dates
        today = date.today()
        if attendance.slot and attendance.slot.date and attendance.slot.date > today:
            return JsonResponse({'success': False, 'error': 'Cannot mark attendance for future dates. Only current date and past dates are allowed.'}, status=403)
        
        attendance.is_present = is_present
        attendance.marked_by = request.user if request.user.is_authenticated else None
        attendance.marked_at = now()
        attendance.save()

        return JsonResponse({'success': True})
    except Attendance.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Attendance record not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def api_update_attendance_bulk(request):
    """Bulk update attendance records. Expects JSON: { updates: [{attendance_id, is_present}, ...] }"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    if not has_admin_or_staff_access(request):
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

    try:
        payload = json.loads(request.body)
        updates = payload.get('updates', [])
        if not isinstance(updates, list):
            return JsonResponse({'success': False, 'error': 'Invalid payload'}, status=400)

        updated = 0
        today = date.today()
        for u in updates:
            aid = u.get('attendance_id')
            is_present = u.get('is_present', False)
            try:
                att = Attendance.objects.get(id=aid)
                
                # Prevent marking attendance for future dates
                if att.slot and att.slot.date and att.slot.date > today:
                    continue  # Skip future dates
                
                att.is_present = bool(is_present)
                att.marked_by = request.user if request.user.is_authenticated else None
                att.marked_at = now()
                att.save()
                updated += 1
            except Attendance.DoesNotExist:
                continue

        return JsonResponse({'success': True, 'updated': updated})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def api_generate_attendance_report_by_month(request):
    """Generate a CSV attendance report filtered by month/year showing all dates separately."""
    if not has_admin_or_staff_access(request):
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    # Parse optional month and year from query params
    month_filter = request.GET.get('month', '').strip()
    year_filter = request.GET.get('year', '').strip()
    subject_filter = request.GET.get('subject', '').strip()
    
    # Validate month (01-12) and year (4 digits)
    if month_filter and not (month_filter.isdigit() and 1 <= int(month_filter) <= 12):
        month_filter = ''
    if year_filter and not (year_filter.isdigit() and len(year_filter) == 4):
        year_filter = ''

    if not month_filter and not year_filter:
        return JsonResponse({'success': False, 'error': 'Please provide month and/or year filter'}, status=400)

    # Build CSV with columns matching the screenshot
    response = HttpResponse(content_type='text/csv')
    if month_filter and year_filter:
        filename = f"attendance_{year_filter}_{month_filter}.csv"
    elif month_filter:
        filename = f"attendance_month_{month_filter}.csv"
    else:
        filename = f"attendance_{year_filter}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Subject', 'Full Name', 'Enrollment', 'Present', 'Absent'])

    all_attendance_records = Attendance.objects.exclude(
        slot__date__isnull=True
    ).select_related('user', 'user__profile', 'slot').order_by('slot__date', 'user__username', '-marked_at')

    today = date.today()
    filtered_attendance = []
    for att in all_attendance_records:
        if not att.slot or not att.slot.date:
            continue
        slot_date = att.slot.date
        today = date.today()
        for att in all_attendance_records:
            if not att.slot or not att.slot.date:
                continue
            slot_date = att.slot.date
            if slot_date > today:
                continue
            att_year = str(slot_date.year).zfill(4)
            att_month = str(slot_date.month).zfill(2)
            if month_filter and att_month != month_filter:
                continue
            if year_filter and att_year != year_filter:
                continue
            user = att.user
            prof = getattr(user, 'profile', None)
            full_name = prof.full_name if prof and getattr(prof, 'full_name', None) else ''
            enrollment = prof.enrollment if prof and getattr(prof, 'enrollment', None) else ''
            present = 'Yes' if att.is_present else 'No'
            absent = 'No' if att.is_present else 'Yes'
            writer.writerow([
                slot_date.strftime('%Y-%m-%d'),
                att.subject,
                full_name,
                enrollment,
                present,
                absent
            ])
    today = date.today()
    filtered_attendance = []
    for att in all_attendance_records:
        if not att.slot or not att.slot.date:
            continue
        
        slot_date = att.slot.date
        
        # Exclude future dates - only show dates up to today
        if slot_date > today:
            continue
        
        att_year = str(slot_date.year).zfill(4)
        att_month = str(slot_date.month).zfill(2)
        
        # Check if this date matches the filter
        if month_filter and att_month != month_filter:
            continue
        if year_filter and att_year != year_filter:
            continue
        if subject_filter and (att.subject or '').strip() != subject_filter:
            continue
        
        filtered_attendance.append(att)
    
    # Get all users for enrollment cache
    users = User.objects.all().select_related('profile').order_by('username')
    
    # Create a cache for user enrollments (to avoid repeated file reads)
    enrollment_cache = {}
    for user in users:
        prof = getattr(user, 'profile', None)
        enrollment = prof.enrollment if prof and getattr(prof, 'enrollment', None) else ''
        
        # If enrollment missing in profile, try to read from saved exam JSON files in data/
        if not enrollment:
            try:
                data_dir = os.path.join(settings.BASE_DIR, 'data')
                best = None
                if os.path.isdir(data_dir):
                    for fname in os.listdir(data_dir):
                        if not fname.lower().endswith('.json'):
                            continue
                        path = os.path.join(data_dir, fname)
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                rec = json.load(f)
                                if rec.get('username') == user.username:
                                    rec_enr = rec.get('enrollment') or ''
                                    if rec_enr:
                                        saved_token = rec.get('saved_at', '')
                                        # Prefer the most recent saved_at lexicographically if available
                                        if best is None or str(saved_token) > str(best[0]):
                                            best = (saved_token, rec_enr)
                        except Exception:
                            continue
                if best:
                    enrollment = best[1]
            except Exception:
                pass
        
        enrollment_cache[user.id] = enrollment
    
    # Track written rows to prevent any duplicates (date, subject, user_id)
    written_rows = set()
    
    # Deduplicate: keep only the most recent attendance record per user per date/subject
    seen_user_dates = {}
    for att in filtered_attendance:
        if not att.slot or not att.slot.date:
            continue
        
        slot_date = att.slot.date
        key = (slot_date, (att.subject or '').strip(), att.user.id)
        
        # Keep the most recent attendance record for each user-date combination
        if key not in seen_user_dates:
            seen_user_dates[key] = att
        else:
            # Compare marked_at timestamps to keep the most recent
            if att.marked_at and seen_user_dates[key].marked_at:
                if att.marked_at > seen_user_dates[key].marked_at:
                    seen_user_dates[key] = att
    
    # Write rows using the actual slot dates from attendance records
    # Sort by date first to ensure proper ordering in CSV
    sorted_attendance = sorted(seen_user_dates.items(), key=lambda x: (x[0][0], x[0][1], x[0][2]))
    
    for (slot_date, subject_value, user_id), attendance in sorted_attendance:
        # Double-check: Get the actual slot date directly from the attendance record
        # This ensures the date in CSV exactly matches the slot date where attendance was marked
        if attendance.slot and attendance.slot.date:
            actual_slot_date = attendance.slot.date
        else:
            actual_slot_date = slot_date  # Fallback to the key date
        
        # Skip if already written (using actual slot date)
        if (actual_slot_date, subject_value, user_id) in written_rows:
            continue
        
        user = attendance.user
        actual_date_str = actual_slot_date.strftime('%Y-%m-%d')
        
        prof = getattr(user, 'profile', None)
        full_name = prof.full_name if prof and getattr(prof, 'full_name', None) else ''
        enrollment = enrollment_cache.get(user.id, '')
        
        # Get attendance status
        present = 'Yes' if attendance.is_present else 'No'
        absent = 'Yes' if not attendance.is_present else 'No'
        
        # Prevent Excel from converting long numeric enrollments to scientific notation
        enrollment_out = enrollment
        try:
            if enrollment and str(enrollment).strip().isdigit() and len(str(enrollment).strip()) >= 10:
                enrollment_out = f'="{str(enrollment).strip()}"'
        except Exception:
            enrollment_out = enrollment
        
        # Write row using the actual slot date from the attendance record
        writer.writerow([actual_date_str, subject_value or '-', user.username, full_name, enrollment_out, present, absent])
        # Track using the actual slot date to ensure consistency
        written_rows.add((actual_slot_date, subject_value, user_id))

    return response


def api_generate_attendance_report(request, slot_id):
    """Generate a CSV attendance report for a given slot, with optional month/year filtering."""
    if not has_admin_or_staff_access(request):
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    try:
        slot = UnlockSlot.objects.get(id=slot_id)
    except UnlockSlot.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Slot not found'}, status=404)

    # Parse optional month and year from query params
    month_filter = request.GET.get('month', '').strip()
    year_filter = request.GET.get('year', '').strip()
    subject = (request.GET.get('subject') or '').strip()
    if not subject:
        return JsonResponse({'success': False, 'error': 'Subject is required'}, status=400)
    
    # Validate month (01-12) and year (4 digits)
    if month_filter and not (month_filter.isdigit() and 1 <= int(month_filter) <= 12):
        month_filter = ''
    if year_filter and not (year_filter.isdigit() and len(year_filter) == 4):
        year_filter = ''

    # Build CSV with columns matching the screenshot
    response = HttpResponse(content_type='text/csv')
    date_str_for_filename = slot.date.strftime('%Y-%m-%d') if slot.date else 'unknown'
    filename = f"attendance_{date_str_for_filename}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    # Header row as in screenshot
    writer.writerow(['Date', 'Full Name', 'Enrollment', 'Data Structure', 'Dgengo', 'DWDM', 'FON', 'UIUX'])

    # Ensure attendance records exist for all users (for past or current slots)
    today = date.today()
    users = User.objects.all().select_related('profile').order_by('username')
    if slot.date and slot.date <= today:
        for user in users:
            Attendance.objects.get_or_create(
                user=user,
                slot=slot,
                subject=subject,
                defaults={'is_present': False}
            )

    attendance_records = Attendance.objects.filter(slot=slot, subject=subject).select_related('user', 'user__profile').order_by('user__username')
    for attendance in attendance_records:
        user = attendance.user
        prof = getattr(user, 'profile', None)
        full_name = prof.full_name if prof and getattr(prof, 'full_name', None) else ''
        enrollment = prof.enrollment if prof and getattr(prof, 'enrollment', None) else ''
        
        # If enrollment missing in profile, try to read from saved exam JSON files in data/
        if not enrollment:
            try:
                data_dir = os.path.join(settings.BASE_DIR, 'data')
                best = None
                if os.path.isdir(data_dir):
                    for fname in os.listdir(data_dir):
                        if not fname.lower().endswith('.json'):
                            continue
                        path = os.path.join(data_dir, fname)
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                rec = json.load(f)
                                if rec.get('username') == user.username:
                                    # Apply month/year filter to enrollment lookup
                                    saved_token = rec.get('saved_at', '')
                                    if saved_token and (month_filter or year_filter):
                                        # Extract YYYYMMDD from saved_at token
                                        ymd = saved_token.split('-', 1)[0] if '-' in saved_token else saved_token[:8]
                                        if len(ymd) >= 8:
                                            try:
                                                rec_year = ymd[0:4]
                                                rec_month = ymd[4:6]
                                                # Check if this record matches the filter
                                                if month_filter and rec_month != month_filter:
                                                    continue
                                                if year_filter and rec_year != year_filter:
                                                    continue
                                            except Exception:
                                                continue
                                    
                                    rec_enr = rec.get('enrollment') or ''
                                    if rec_enr:
                                        # Prefer the most recent saved_at lexicographically if available
                                        if best is None or str(saved_token) > str(best[0]):
                                            best = (saved_token, rec_enr)
                        except Exception:
                            continue
                if best:
                    enrollment = best[1]
            except Exception:
                # ignore fallback errors; leave enrollment blank
                pass
        
        present = 'Yes' if attendance.is_present else 'No'
        absent = 'Yes' if not attendance.is_present else 'No'
        
        # Prevent Excel from converting long numeric enrollments to scientific notation
        enrollment_out = enrollment
        try:
            if enrollment and str(enrollment).strip().isdigit() and len(str(enrollment).strip()) >= 10:
                enrollment_out = f'="{str(enrollment).strip()}"'
        except Exception:
            enrollment_out = enrollment

        # Format date as YYYY-MM-DD (ISO format)
        date_str = slot.date.strftime('%Y-%m-%d') if slot.date else 'N/A'

        writer.writerow([date_str, subject, user.username, full_name, enrollment_out, present, absent])

    return response


def faculty_register(request):
    if request.method == 'POST':
        username = (request.POST.get('username') or request.POST.get('faculty_id') or '').strip()
        email = (request.POST.get('email') or '').strip()
        password = request.POST.get('password') or ''
        full_name = (request.POST.get('full_name') or '').strip()
        profession = (request.POST.get('profession') or '').strip()

        if not all([username, email, password, full_name, profession]):
            messages.error(request, 'All fields are required.')
            return redirect('faculty_register')

        registration_request = {
            'username': username,
            'email': email,
            'password': password,
            'full_name': full_name,
            'profession': profession,
            'approved': False,
            'status': 'pending',
            'submitted_at': now().isoformat()
        }

        requests_path = os.path.join(settings.BASE_DIR, 'data', 'registration_requests.json')
        os.makedirs(os.path.dirname(requests_path), exist_ok=True)

        try:
            if os.path.exists(requests_path):
                with open(requests_path, 'r', encoding='utf-8') as f:
                    existing_requests = json.load(f)
            else:
                existing_requests = []

            updated = False
            for idx, req in enumerate(existing_requests):
                if (req.get('username') or '').strip() == username:
                    existing_requests[idx].update(registration_request)
                    updated = True
                    break

            if not updated:
                existing_requests.append(registration_request)

            with open(requests_path, 'w', encoding='utf-8') as f:
                json.dump(existing_requests, f, indent=4)

            messages.success(request, 'Registration request submitted for admin approval.')
        except Exception as e:
            messages.error(request, f'Error submitting registration request: {e}')

        return redirect('faculty_login')

    return render(request, 'faculty_register.html')

@require_POST
def approve_request(request):
    username = (request.POST.get('username') or '').strip()
    action = (request.POST.get('action') or 'approve').strip().lower()

    if not username:
        messages.error(request, 'No faculty username provided.')
        return redirect('Admin_dashboard')

    if not (request.session.get('is_site_admin') or (request.user.is_authenticated and request.user.is_staff)):
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('Admin_dashboard')

    requests_path = os.path.join(settings.BASE_DIR, 'data', 'registration_requests.json')
    if not os.path.exists(requests_path):
        messages.error(request, 'No registration requests found.')
        return redirect('Admin_dashboard')

    try:
        with open(requests_path, 'r', encoding='utf-8') as f:
            registration_requests = json.load(f)
    except Exception as exc:
        messages.error(request, f'Error reading requests: {exc}')
        return redirect('Admin_dashboard')

    updated = False
    for req in registration_requests:
        req_username = (req.get('username') or '').strip()
        if req_username != username:
            continue

        updated = True
        if action == 'approve':
            if not User.objects.filter(username=username).exists():
                try:
                    User.objects.create_user(
                        username=username,
                        email=req.get('email', ''),
                        password=req.get('password') or User.objects.make_random_password(),
                        first_name=req.get('full_name', '')
                    )
                except Exception as exc:
                    messages.error(request, f'Failed to create user: {exc}')
                    break
            req['approved'] = True
            req['status'] = 'approved'
            req['status_updated_at'] = now().isoformat()
            messages.success(request, f'Faculty {username} approved.')
        elif action == 'reject':
            req['approved'] = False
            req['status'] = 'rejected'
            req['status_updated_at'] = now().isoformat()
            messages.info(request, f'Faculty {username} has been rejected.')
        else:
            messages.error(request, 'Unknown action.')
        break

    if updated:
        try:
            with open(requests_path, 'w', encoding='utf-8') as f:
                json.dump(registration_requests, f, indent=4)
        except Exception as exc:
            messages.error(request, f'Error saving requests: {exc}')
    else:
        messages.error(request, 'Registration request not found.')

    return redirect('Admin_dashboard')


def api_reject_faculty(request, username):
    """API endpoint to reject a faculty member without page redirect"""
    # Check authorization - accept both session-based and user-based auth
    allowed = False
    
    # Check if user is authenticated via Django auth
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        allowed = True
    # Check if user is logged in as site admin via session
    elif request.session.get('is_site_admin'):
        allowed = True
    
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    username = (username or '').strip()
    if not username:
        return JsonResponse({'success': False, 'error': 'Username required'}, status=400)
    
    requests_path = os.path.join(settings.BASE_DIR, 'data', 'registration_requests.json')
    if not os.path.exists(requests_path):
        return JsonResponse({'success': False, 'error': 'No registration requests found'}, status=404)
    
    try:
        with open(requests_path, 'r', encoding='utf-8') as f:
            registration_requests = json.load(f)
    except Exception as exc:
        return JsonResponse({'success': False, 'error': f'Error reading requests: {exc}'}, status=500)
    
    found = False
    for req in registration_requests:
        if (req.get('username') or '').strip() == username:
            found = True
            req['approved'] = False
            req['status'] = 'rejected'
            req['status_updated_at'] = now().isoformat()
            break
    
    if not found:
        return JsonResponse({'success': False, 'error': 'Faculty not found'}, status=404)
    
    try:
        with open(requests_path, 'w', encoding='utf-8') as f:
            json.dump(registration_requests, f, indent=4)
        return JsonResponse({'success': True, 'message': f'Faculty {username} rejected successfully'})
    except Exception as exc:
        return JsonResponse({'success': False, 'error': f'Error saving requests: {exc}'}, status=500)


def api_get_exam_dates_by_subject(request):
    """API endpoint to get available exam dates for a subject
    Only returns dates that have active UnlockSlots created by admin
    """
    subject = request.GET.get('subject', '').strip()
    
    if not subject:
        return JsonResponse({'error': 'Subject is required'}, status=400)
    
    # Get all active unlock slots (dates where admin has enabled exams)
    active_slot_dates = UnlockSlot.objects.filter(
        is_active=True
    ).values_list('date', flat=True).distinct()
    
    # Get exam dates for the subject that also have active slots
    exam_dates = ExamResult.objects.filter(
        subject=subject,
        exam_date__in=active_slot_dates
    ).exclude(exam_date__isnull=True).values_list('exam_date', flat=True).distinct().order_by('-exam_date')
    
    # Convert dates to strings
    dates_list = [str(date) for date in exam_dates]
    
    return JsonResponse({'dates': dates_list})


def download_exam_attendance(request):
    if request.method == 'GET':
        try:
            subject = request.GET.get('subject', '').strip()
            exam_date = request.GET.get('exam_date', '').strip()
            
            if not subject or not exam_date:
                return JsonResponse({'error': 'Subject and exam date are required'}, status=400)
            
            # Try to parse exam_date
            try:
                exam_date_obj = datetime.strptime(exam_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': f'Invalid date format. Use YYYY-MM-DD'}, status=400)
            
            # Get students who have BOOKED this specific subject for this date
            # Find the UnlockSlot for this date
            try:
                slot = UnlockSlot.objects.get(date=exam_date_obj, is_active=True)
            except UnlockSlot.DoesNotExist:
                return JsonResponse({'error': 'No active slot found for this date.'}, status=400)
            
            # Get all students who booked this slot
            booked_students = UnlockBooking.objects.filter(
                slot=slot
            ).select_related('user', 'user__profile').order_by('user__username')
            
            # Get the set of user IDs who booked
            booked_user_ids = set(booking.user.id for booking in booked_students)
            
            # Now filter by those who have exam records for this specific subject on this date
            exam_students_for_subject = ExamResult.objects.filter(
                subject=subject,
                exam_date=exam_date_obj,
                user_id__in=booked_user_ids
            ).values_list('user_id', flat=True).distinct()
            
            # Final list: students who booked AND have exam results for THIS SUBJECT
            final_user_ids = list(exam_students_for_subject)
            
            if not final_user_ids:
                # Even if no exam results yet, include students who booked this slot
                # Get students who booked and saved selection for this subject/date
                final_user_ids = list(booked_user_ids)
                
                # Verify they selected this subject by checking saved exam files
                students_with_subject = set()
                try:
                    data_dir = os.path.join(settings.BASE_DIR, 'data')
                    if os.path.isdir(data_dir):
                        for fname in os.listdir(data_dir):
                            if not fname.lower().endswith('.json'):
                                continue
                            filepath = os.path.join(data_dir, fname)
                            try:
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    record = json.load(f)
                                    if (record.get('subject') == subject and 
                                        (record.get('date') == exam_date or record.get('date') == str(exam_date_obj))):
                                        username = record.get('username', '').strip()
                                        if username:
                                            try:
                                                user = User.objects.get(username=username)
                                                if user.id in booked_user_ids:
                                                    students_with_subject.add(user.id)
                                            except User.DoesNotExist:
                                                pass
                            except Exception:
                                continue
                except Exception:
                    pass
                
                final_user_ids = list(students_with_subject) if students_with_subject else list(booked_user_ids)
            
            if not final_user_ids:
                return JsonResponse({'error': 'No students have booked this subject for this date.'}, status=400)
            
            # Get all student objects for the final list
            all_students = User.objects.filter(id__in=final_user_ids).order_by('username').select_related('profile')
            
            if not all_students.exists():
                return JsonResponse({'error': 'No students found in the system.'}, status=400)
            
            # Extract subject code if available
            subject_code = '000000'
            
            # Create a file-like buffer to receive PDF data
            buffer = io.BytesIO()
            
            # Use SimpleDocTemplate for proper page layout
            doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
            story = []
            
            # Create styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=colors.black,
                spaceAfter=0,
                alignment=TA_CENTER
            )
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.black,
                spaceAfter=12,
                alignment=TA_CENTER
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=3
            )
            
            # Add title
            story.append(Paragraph("LOK JAGRUTI KENDRA UNIVERSITY", title_style))
            story.append(Paragraph("Sarkhej Sanand Highway Ahmedabad", subtitle_style))
            
            # Add exam details
            story.append(Paragraph(f"<b>Subject Name:</b> {subject}", normal_style))
            story.append(Paragraph(f"<b>Subject Code:</b> {subject_code}", normal_style))
            story.append(Paragraph(f"<b>Exam Date:</b> {exam_date}", normal_style))
            story.append(Spacer(1, 12))
            
            # Create table data
            data = [['Roll No', 'Enrollment Number', 'Name', 'Signature']]
            
            # Add only booked students to the table
            roll_no_counter = 1
            for student in all_students:
                try:
                    # Try to get enrollment from profile
                    enrollment = ''
                    if hasattr(student, 'profile'):
                        enrollment = getattr(student.profile, 'enrollment', '') or ''
                    
                    full_name = student.get_full_name() or student.username
                    
                    data.append([str(roll_no_counter), enrollment, full_name, ''])
                    roll_no_counter += 1
                except Exception as e:
                    # Skip this student if there's an error
                    continue
            
            # Create table
            table = Table(data, colWidths=[60, 120, 150, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 12))
            story.append(Paragraph("<b>Supervisor's Signature:</b> _______________________", normal_style))
            
            # Build PDF
            doc.build(story)
            
            # File response with PDF
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="exam_attendance_{subject}_{exam_date}.pdf"'
            return response
        except Exception as e:
            return JsonResponse({'error': f'Error generating PDF: {str(e)}'}, status=500)


def api_get_subjects_by_date(request):
    """API endpoint to get subjects that have exams on a specific date"""
    slot_id = request.GET.get('slot_id', '').strip()
    
    if not slot_id:
        return JsonResponse({'error': 'slot_id is required'}, status=400)
    
    try:
        slot = UnlockSlot.objects.get(id=slot_id)
    except UnlockSlot.DoesNotExist:
        return JsonResponse({'error': 'Slot not found'}, status=404)
    
    # Get all subjects that have exams on this date
    subjects = ExamResult.objects.filter(
        exam_date=slot.date
    ).values_list('subject', flat=True).distinct().order_by('subject')
    
    return JsonResponse({'subjects': list(subjects)})


def api_get_subjects_for_date(request):
    """API endpoint to get subjects that students have BOOKED exams for on a specific date"""
    exam_date = request.GET.get('exam_date', '').strip()
    
    if not exam_date:
        return JsonResponse({'error': 'exam_date is required'}, status=400)
    
    try:
        from datetime import datetime
        exam_date_obj = datetime.strptime(exam_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
    
    # Find the UnlockSlot for this date
    try:
        slot = UnlockSlot.objects.get(date=exam_date_obj, is_active=True)
    except UnlockSlot.DoesNotExist:
        return JsonResponse({'subjects': []})  # No active slot for this date
    
    # Get all subjects that students have booked for this slot
    # by checking student exam selections saved in the data directory
    subjects = set()
    
    try:
        data_dir = os.path.join(settings.BASE_DIR, 'data')
        if os.path.isdir(data_dir):
            for fname in os.listdir(data_dir):
                if not fname.lower().endswith('.json'):
                    continue
                filepath = os.path.join(data_dir, fname)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        record = json.load(f)
                        # Check if this exam is for the selected date
                        if record.get('date') == exam_date or record.get('date') == str(exam_date_obj):
                            subject = record.get('subject', '').strip()
                            if subject:
                                subjects.add(subject)
                except Exception:
                    continue
    except Exception:
        pass
    
    # Also check ExamResult records for this date
    exam_subjects = ExamResult.objects.filter(
        exam_date=exam_date_obj
    ).values_list('subject', flat=True).distinct()
    subjects.update(exam_subjects)
    
    # Sort and return
    return JsonResponse({'subjects': sorted(list(subjects))})
    return JsonResponse({'error': 'Invalid request method'}, status=400)
