from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.views import View
from django.urls import reverse_lazy, reverse
from django.contrib.auth import logout  # Import the logout function
from django.views.generic import UpdateView, DeleteView, ListView, TemplateView, FormView
from django.conf import settings
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django import forms
from django.utils import timezone
from datetime import timedelta

from django.db import transaction
from django.db import IntegrityError

from .utils import SubscriptionManager, PaymentProcessor
import requests  # For M-Pesa API calls

from django.db import models
import re
from django.db.models import DecimalField
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal
import pandas as pd
import random
import string
from datetime import datetime
import time
import hashlib
import uuid
from django.contrib import messages

from .models import ( 
School, Department, Course, Student, Lecturer, Unit, NominalRoll, UnitCourse, 
Response, LecturerUnit, Result, Complaint, System_User, Payment, AcademicYear
)

from .forms import (
SignUpForm, LoginForm, ResponseForm, PostComplaintForm, UploadFileForm, StudentRegNoForm
)

class SignUpView(View):
    template_name = 'signup.html'

    def get(self, request):
        form = SignUpForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password_hash = form.cleaned_data['password_hash']

            # Check if username already exists in System_User model
            if System_User.objects.filter(username=username).exists():
                form.add_error('username', "This username has already been used in the system!")
                return render(request, self.template_name, {'form': form})
            if self.is_lecturer_username(username):
                # Check if the lecturer exists in the Lecturer model
                if not Lecturer.objects.filter(username=username).exists():
                    form.add_error('username', "This lecturer email does not exist.")
                    return render(request, self.template_name, {'form': form})
            else:
                form.add_error('username', "Invalid username format. Please enter a valid student registration number or lecturer email.")
                return render(request, self.template_name, {'form': form})

            # Create the account if all checks pass
            new_account = form.save(commit=False)
            new_account.set_password(password_hash)
            new_account.save()
            return redirect('login')
        else:
            # If the form is not valid, render the template with the form and errors
            return render(request, self.template_name, {'form': form})

    def is_lecturer_username(self, username):
        # Check if the username is in the lecturer email format
        return bool(re.match(r'^[a-zA-Z0-9]{1,15}@mmust\.ac\.ke$', username))

        

class LoginView(View):
    template_name = 'login.html'

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            if self.is_lecturer_username(username):
                # Check if the username exists in the System_User model
                user = System_User.objects.filter(username=username).first()
                if user and user.check_password(password):
                    # Check if the user exists in the Lecturer model
                    lecturer = Lecturer.objects.filter(username=username).first()
                    if lecturer is not None:
                        role = lecturer.role
                        request.session['username'] = user.username  # Store username in session
                        if role == "Member":
                            return redirect(reverse('lecturer-dashboard'))
                        elif role == "Exam Officer":
                            return redirect(reverse('exam-dashboard'))
                        elif role == "COD":
                            return redirect(reverse('cod-dashboard'))
                    else:
                        # Username does not exist in Lecturer model
                        form.add_error('username', "Wrong Username or Password.")
                else:
                    # Authentication failed for lecturer
                    form.add_error('username', "Wrong Username or Password.")

        return render(request, self.template_name, {'form': form})

    def is_lecturer_username(self, username):
        # Check if the username is in the lecturer email format
        return bool(re.match(r'^[a-zA-Z0-9]{1,15}@mmust\.ac\.ke$', username))

class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)  # Use logout directly
        return redirect('login')  # Redirect to the login page or another appropriate page


class Lecturer_DashboardView(View):
    def get(self, request):
        units = Unit.objects.all()
        courses = Course.objects.all()
            
        context = {
            'units': units,
            'courses': courses,
        }
        
        # Retrieve username from session
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is not in session
            
        try:
            user = System_User.objects.get(username=username)
            # Retrieve the lecturer based on the username
            lecturer = Lecturer.objects.get(username=username)
            context['last_name'] = lecturer.last_name  # Add last name to context
        except (System_User.DoesNotExist, Lecturer.DoesNotExist):
            return redirect('login')
        
        # Add the 'user' object to the context
        context['user'] = user

        # Pass the full context to the template
        return render(request, 'lecturer_dashboard.html', context)
  
class COD_DashboardView(View):
    def get(self, request):
        units = Unit.objects.all()
        courses = Course.objects.all()
            
        context = {
            'units': units,
            'courses': courses,
        }
        
        # Retrieve username from session
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is not in session
            
        try:
            user = System_User.objects.get(username=username)
            # Retrieve the lecturer based on the username
            lecturer = Lecturer.objects.get(username=username)
            context['last_name'] = lecturer.last_name  # Add last name to context
        except (System_User.DoesNotExist, Lecturer.DoesNotExist):
            return redirect('login')
        
        # Add the 'user' object to the context
        context['user'] = user

        # Pass the full context to the template
        return render(request, 'cod_dashboard.html', context)

class Exam_DashboardView(View):
    def get(self, request):
        units = Unit.objects.all()
        courses = Course.objects.all()
            
        context = {
            'units': units,
            'courses': courses,
        }
        
        # Retrieve username from session
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is not in session
            
        try:
            user = System_User.objects.get(username=username)
            # Retrieve the lecturer based on the username
            lecturer = Lecturer.objects.get(username=username)
            context['last_name'] = lecturer.last_name  # Add last name to context
        except (System_User.DoesNotExist, Lecturer.DoesNotExist):
            return redirect('login')
        
        # Add the 'user' object to the context
        context['user'] = user

        # Pass the full context to the template
        return render(request, 'exam_dashboard.html', context)

class StudentRegNo(View):
    def get(self, request):
        form = StudentRegNoForm()
        return render(request, 'student_reg_no.html', {'form': form})

    def post(self, request):
        form = StudentRegNoForm(request.POST)
        if form.is_valid():
            reg_no = form.cleaned_data['registration_number']
            try:
                student = Student.objects.get(reg_no=reg_no)
                request.session['registration_number'] = reg_no
                return redirect('post-complaint')
            except Student.DoesNotExist:
                messages.error(request, "Registration number not found.")
                return render(request, 'student_reg_no.html', {'form': form})
        return render(request, 'student_reg_no.html', {'form': form})

class PostComplaint(View):
    def get(self, request):
        reg_no = request.session.get('registration_number')
        if not reg_no:
            return redirect('student')
        
        try:
            student = get_object_or_404(Student, reg_no=reg_no)
            form = PostComplaintForm(student=student)
            return render(request, 'post_complaint.html', {'form': form, 'student': student})
        except Student.DoesNotExist:
            messages.error(request, "Student details could not be found.")
            return redirect('student')

    def post(self, request):
        reg_no = request.session.get('registration_number')
        if not reg_no:
            return redirect('student')

        student = get_object_or_404(Student, reg_no=reg_no)
        form = PostComplaintForm(request.POST, student=student)

        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.reg_no = student  # Attach the student
            complaint.complaint_code = form.generate_complaint_code()
            complaint.exam_date = form.cleaned_data['exam_date']

            # Check if a complaint already exists with the same reg_no and unit_code
            if Complaint.objects.filter(reg_no=student, unit_code=complaint.unit_code).exists():
                messages.error(request, "A complaint for this unit and student already exists.")
                return render(request, 'post_complaint.html', {'form': form, 'student': student})
            
            try:
                # Attempt to save the complaint
                complaint.save()
                messages.success(request, "Complaint posted successfully!")
                return redirect('post-complaint')
            except IntegrityError:
                messages.error(request, "Failed to post complaint due to a unique constraint violation.")
        
        # If form is invalid or if there is an error, re-render the form
        messages.error(request, "Failed to post complaint. Please check the details and try again.")
        return render(request, 'post_complaint.html', {'form': form, 'student': student})

class ComplaintsView(ListView):
    template_name = 'complaints_list.html'
    context_object_name = 'complaints'

    def get(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is not in session
        
        # Retrieve the lecturer based on the username
        lecturer = get_object_or_404(Lecturer, username=username)

        # Get the units and academic years associated with the lecturer
        lec_no = lecturer.lec_no
        lecturer_units = LecturerUnit.objects.filter(lec_no=lec_no)

        # Get the unit codes and academic years
        unit_codes = lecturer_units.values_list('unit_code', flat=True)
        academic_years = lecturer_units.values_list('academic_year', flat=True)

        # Query complaints related to the lecturer's units and academic years
        complaints = Complaint.objects.filter(unit_code__in=unit_codes, academic_year__in=academic_years)

        return render(request, self.template_name, {'complaints': complaints})

class ResponseView(FormView):
    template_name = 'response_form.html'
    form_class = ResponseForm

    def generate_response_code(self):
        while True:
            letters = ''.join(random.choices(string.ascii_uppercase, k=3))
            numbers = ''.join(random.choices(string.digits, k=3))
            code = letters + numbers
            if not Response.objects.filter(response_code=code).exists():
                return code

    def dispatch(self, request, *args, **kwargs):
        # Ensure the user is logged in
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if not logged in
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        complaint_code = self.kwargs['complaint_code']
        complaint = get_object_or_404(Complaint, complaint_code=complaint_code)

        # Pass complaint data to the context
        context['complaint_code'] = complaint_code
        context['reg_no'] = complaint.reg_no
        context['unit_code'] = complaint.unit_code
        context['academic_year'] = complaint.academic_year
        return context

    def form_valid(self, form):
        complaint_code = self.kwargs['complaint_code']
        complaint = get_object_or_404(Complaint, complaint_code=complaint_code)
        username = self.request.session.get('username')
        lecturer = get_object_or_404(Lecturer, username=username)

        # Check if a response already exists for the given reg_no and unit_code
        if Response.objects.filter(reg_no=complaint.reg_no, unit_code=complaint.unit_code).exists():
            messages.error(self.request, 'A response already exists for this unit and student.')
            return self.form_invalid(form)

        # Wrap save and delete operations in a transaction
        with transaction.atomic():
            try:
                # Create response instance but don't save it yet
                response = form.save(commit=False)
                response.response_code = self.generate_response_code()
                response.responder = lecturer
                response.reg_no = complaint.reg_no
                response.unit_code = complaint.unit_code
                response.date = timezone.now()

                # Attempt to save the response instance
                response.save()

                # Delete the complaint after saving the response
                complaint.delete()

                # Add a success message
                messages.success(self.request, 'Response saved successfully.')
            except IntegrityError:
                messages.error(self.request, 'Error: Response with this unit and registration number already exists.')
                return self.form_invalid(form)

        return redirect(reverse('complaints'))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

class LoadNominalRollView(View):
    def get(self, request):
        form = UploadFileForm()
        return render(request, 'load_nominal_roll.html', {'form': form})

    def post(self, request):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # Read the CSV or Excel file
                if file.name.endswith('.csv'):
                    data = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    data = pd.read_excel(file)
                else:
                    messages.error(request, 'Invalid file format. Please upload a CSV or Excel file.')
                    return render(request, 'load_nominal_roll.html', {'form': form})

                # Get the lecturer based on session username
                username = request.session.get('username')
                if not username:
                    return redirect('login')  # Redirect to login if not logged in
                lecturer = get_object_or_404(Lecturer, username=username)
                lec_no = lecturer.lec_no

                # Get unit codes related to the lecturer
                related_units = LecturerUnit.objects.filter(lec_no=lec_no).values_list('unit_code', 'academic_year')
                allowed_unit_codes = {(u[0], u[1]) for u in related_units}  # Set of tuples for fast lookup

                # Initialize error list
                errors = []

                # Process each row
                for index, row in data.iterrows():
                    try:
                        # Retrieve related instances
                        unit = Unit.objects.get(unit_code=row['unit_code'])
                        student = Student.objects.get(reg_no=row['reg_no'])
                        academic_year = AcademicYear.objects.get(academic_year=row['academic_year'])

                        # Check if the unit and academic year are allowed for this lecturer
                        if (unit.unit_code, academic_year.academic_year) not in allowed_unit_codes:
                            errors.append(f"Row {index + 1}: Unit {unit.unit_code} not assigned to this lecturer or wrong academic year.")
                            continue

                        # Check if entry already exists to avoid duplicates
                        if NominalRoll.objects.filter(unit_code=unit, reg_no=student, academic_year=academic_year).exists():
                            errors.append(f"Row {index + 1}: Duplicate entry in nominal roll for unit {unit.unit_code} and student {student.reg_no}.")
                            continue

                        # Create NominalRoll instance and save
                        nominal_roll = NominalRoll(
                            unit_code=unit,
                            reg_no=student,
                            academic_year=academic_year
                        )
                        nominal_roll.full_clean()  # Validate model instance
                        nominal_roll.save()

                    except (Unit.DoesNotExist, Student.DoesNotExist, AcademicYear.DoesNotExist):
                        errors.append(f"Row {index + 1}: Foreign key reference not found (unit, student, or academic year).")
                    except ValidationError as ve:
                        errors.append(f"Row {index + 1}: {ve}")
                    except Exception as e:
                        errors.append(f"Row {index + 1}: Unexpected error - {str(e)}")

                # Display success or error messages
                if errors:
                    for error in errors:
                        messages.error(request, error)
                else:
                    messages.success(request, 'Nominal roll loaded successfully.')

                return render(request, 'load_nominal_roll.html', {'form': form})

            except Exception as e:
                messages.error(request, f'An error occurred while processing the file: {str(e)}')
        else:
            messages.error(request, 'Invalid form submission.')

        return render(request, 'load_nominal_roll.html', {'form': form})

class LoadResultView(View):
    def get(self, request):
        form = UploadFileForm()
        return render(request, 'load_result.html', {'form': form})

    def post(self, request):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # Load file into a DataFrame
                if file.name.endswith('.csv'):
                    data = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    data = pd.read_excel(file)
                else:
                    messages.error(request, 'Invalid file format. Please upload a CSV or Excel file.')
                    return render(request, 'load_result.html', {'form': form})

                # Get the lecturer's username from session
                username = request.session.get('username')
                if not username:
                    return redirect('login')  # Redirect to login if not logged in
                lecturer = get_object_or_404(Lecturer, username=username)
                lec_no = lecturer.lec_no

                # Get the units and academic years assigned to this lecturer
                related_units = LecturerUnit.objects.filter(lec_no=lec_no).values_list('unit_code', 'academic_year')
                allowed_units = {(u[0], u[1]) for u in related_units}  # Set for fast lookup

                errors = []

                for index, row in data.iterrows():
                    try:
                        # Retrieve foreign key instances
                        unit = Unit.objects.get(unit_code=row['unit_code'])
                        student = Student.objects.get(reg_no=row['reg_no'])
                        academic_year = AcademicYear.objects.get(academic_year=row['academic_year'])

                        # Check if unit and academic year are allowed for this lecturer
                        if (unit.unit_code, academic_year.academic_year) not in allowed_units:
                            errors.append(f"Row {index + 1}: Unit {unit.unit_code} is not assigned to this lecturer.")
                            continue

                        # Check for duplicate entries
                        if Result.objects.filter(unit_code=unit, reg_no=student, academic_year=academic_year).exists():
                            errors.append(f"Row {index + 1}: Duplicate result entry for student {student.reg_no} in unit {unit.unit_code}.")
                            continue

                        # Check CAT and exam marks, ensuring they meet field constraints
                        cat = row['cat']
                        exam = row['exam']
                        if not (0 <= cat <= 30):
                            errors.append(f"Row {index + 1}: Invalid CAT mark ({cat}). It should be between 0 and 30.")
                            continue
                        if not (0 <= exam <= 70):
                            errors.append(f"Row {index + 1}: Invalid exam mark ({exam}). It should be between 0 and 70.")
                            continue

                        # Create and validate the Result instance
                        result = Result(
                            unit_code=unit,
                            reg_no=student,
                            academic_year=academic_year,
                            cat=cat,
                            exam=exam
                        )
                        result.full_clean()  # Validate the instance
                        result.save()  # Save to the database

                    except (Unit.DoesNotExist, Student.DoesNotExist, AcademicYear.DoesNotExist):
                        errors.append(f"Row {index + 1}: Foreign key references not found (unit, student, or academic year).")
                    except ValidationError as ve:
                        errors.append(f"Row {index + 1}: Validation error - {ve}")
                    except Exception as e:
                        errors.append(f"Row {index + 1}: Unexpected error - {str(e)}")

                # Display error or success messages
                if errors:
                    for error in errors:
                        messages.error(request, error)
                else:
                    messages.success(request, 'Results loaded successfully.')

                return render(request, 'load_result.html', {'form': form})

            except Exception as e:
                messages.error(request, f'An error occurred while processing the file: {str(e)}')
        else:
            messages.error(request, 'Invalid form submission.')

        return render(request, 'load_result.html', {'form': form})

class ResultListView(ListView):
    model = Result
    template_name = 'result_list.html'
    context_object_name = 'results'
    
    def get_queryset(self):
        # Get lecturer's lec_no from session username
        username = self.request.session.get('username')
        lecturer = get_object_or_404(Lecturer, username=username)
        
        # Get lec_no associated with the lecturer
        lec_no = lecturer.lec_no
        lec_units = LecturerUnit.objects.filter(lec_no=lec_no)

        # Base queryset filtered by lecturer's units
        queryset = Result.objects.filter(
            unit_code__in=[unit.unit_code for unit in lec_units]
        )

        # Filter by academic year, unit code, and reg_no if provided in request
        academic_year = self.request.GET.get('academic_year')
        unit_code = self.request.GET.get('unit_code')
        reg_no = self.request.GET.get('reg_no')
        sort_field = self.request.GET.get('sort', 'reg_no')  # Default sort by reg_no

        if academic_year:
            queryset = queryset.filter(academic_year__academic_year=academic_year)
        if unit_code:
            queryset = queryset.filter(unit_code__unit_code=unit_code)
        if reg_no:
            queryset = queryset.filter(reg_no=reg_no)

        return queryset.order_by(sort_field)  # Apply sorting

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['academic_years'] = AcademicYear.objects.all()  # To populate filter options
        return context
    
class NominalRollListView(ListView):
    model = NominalRoll
    template_name = 'nominal_roll_list.html'
    context_object_name = 'nominal_rolls'
    
    def get_queryset(self):
        username = self.request.session.get('username')
        lecturer = get_object_or_404(Lecturer, username=username)
        
        # Get lec_no associated with the lecturer
        lec_no = lecturer.lec_no
        lec_units = LecturerUnit.objects.filter(lec_no=lec_no)
        queryset = NominalRoll.objects.filter(
            unit_code__in=[unit.unit_code for unit in lec_units]
        )

        academic_year = self.request.GET.get('academic_year')
        unit_code = self.request.GET.get('unit_code')
        reg_no = self.request.GET.get('reg_no')
        sort_field = self.request.GET.get('sort', 'reg_no')

        if academic_year:
            queryset = queryset.filter(academic_year__academic_year=academic_year)
        if unit_code:
            queryset = queryset.filter(unit_code__unit_code=unit_code)
        if reg_no:
            queryset = queryset.filter(reg_no=reg_no, unit_code=unit_code, academic_year=acdemic_year)

        return queryset.order_by(sort_field)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['academic_years'] = AcademicYear.objects.all()
        return context

class LecturerOverdueComplaintsView(View): 
    def get(self, request):
        # Access the logged-in user's username from the session
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is not in session

        try:
            # Get the COD's department and associated lecturers
            cod_lecturer = Lecturer.objects.get(username=username)
            department_lecturers = Lecturer.objects.filter(dep_code=cod_lecturer.dep_code)

            # Retrieve units taught by lecturers in the department
            lecturer_units = LecturerUnit.objects.filter(lec_no__in=department_lecturers)
            department_unit_codes = lecturer_units.values_list('unit_code', flat=True)

            # Calculate the time threshold for overdue complaints (more than 24 hours)
            overdue_threshold = timezone.now() - timedelta(hours=24)

            # Retrieve overdue complaints related to the specific units
            overdue_complaints = Complaint.objects.filter(
                date__lt=overdue_threshold,
                unit_code__in=department_unit_codes
            ).select_related('reg_no', 'academic_year', 'unit_code')  # Optimize with select_related

            # Get lecturer numbers associated with the overdue unit codes
            lecturer_numbers = lecturer_units.filter(
                unit_code__in=overdue_complaints.values_list('unit_code', flat=True)
            ).values_list('lec_no', flat=True).distinct()

            # Retrieve lecturers details who are associated with overdue complaints
            overdue_lecturers = Lecturer.objects.filter(
                lec_no__in=lecturer_numbers
            ).only('phone_number', 'email_address')

            # Prepare context data
            context = {
                'overdue_complaints': overdue_complaints,
                'overdue_lecturers': overdue_lecturers,
            }
            return render(request, 'lecturer_complaints.html', context)

        except Lecturer.DoesNotExist:
            return render(request, 'lecturer_complaints.html', {'error': 'Lecturer not found.'})

class StudentOverdueComplaintsView(View):
    def get(self, request):
        # Access the logged-in user's username from the session
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is not in session

        try:
            # Get the COD's department
            cod_lecturer = Lecturer.objects.get(username=username)
            department_code = cod_lecturer.dep_code

            # Calculate the time threshold for overdue complaints (more than 24 hours)
            overdue_threshold = timezone.now() - timedelta(hours=24)

            # Step 1: Query for overdue complaints related to students in the COD's department
            overdue_complaints = Complaint.objects.filter(
                reg_no__course_code__dep_code=department_code,
                date__lt=overdue_threshold
            ).select_related('reg_no', 'unit_code', 'academic_year')  # Optimize queries

            lecturer_units = LecturerUnit.objects.all()
            
            # Get lecturer numbers associated with the overdue unit codes
            lecturer_numbers = lecturer_units.filter(
                unit_code__in=overdue_complaints.values_list('unit_code', flat=True)
            ).values_list('lec_no', flat=True).distinct()

            # Retrieve lecturers details who are associated with overdue complaints
            overdue_lecturers = Lecturer.objects.filter(
                lec_no__in=lecturer_numbers
            ).only('phone_number', 'email_address')

            # Prepare context for rendering
            context = {
                'overdue_complaints': overdue_complaints,
                'overdue_lecturers': overdue_lecturers,  # Pass lecturer details to template
            }
            return render(request, 'overdue_student_complaints.html', context)

        except Lecturer.DoesNotExist:
            return render(request, 'overdue_student_complaints.html', {'error': 'Lecturer not found.'})

class ResponsesView(View):
    def get(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is not in session

        try:
            # Get the COD's department
            cod_lecturer = Lecturer.objects.get(username=username)
            department_code = cod_lecturer.dep_code

            # Query for responses from the lecturers in the COD's department
            responses = Response.objects.filter(
                responder__dep_code=department_code
            ).select_related('reg_no', 'unit_code', 'responder')


            context = {
                'responses': responses,
            }
            return render(request, 'responses.html', context)

        except Lecturer.DoesNotExist:
            return render(request, 'responses.html', {'error': 'Lecturer not found.'})

class StudentResponsesView(View):
    def get(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is not in session

        try:
            # Get the COD's lecturer object
            cod_lecturer = Lecturer.objects.get(username=username)
            department_code = cod_lecturer.dep_code

            # Query responses and loaded results for students in the COD's department
            student_responses = Response.objects.filter(
                reg_no__course_code__dep_code=department_code
            ).select_related('reg_no', 'responder', 'unit_code')


            context = {
                'student_responses': student_responses,
            }
            return render(request, 'student_responses.html', context)

        except Lecturer.DoesNotExist:
            return render(request, 'student_responses.html', {'error': 'Lecturer not found.'})
