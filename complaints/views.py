from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy, reverse
from django.contrib.auth import logout  # Import the logout function
from django.views.generic import DeleteView, ListView, FormView
from django.conf import settings
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta

from django.db import transaction
from django.db import IntegrityError



import re
from django.core.exceptions import ValidationError
import pandas as pd
import random
import string
from django.contrib import messages

from .models import (
School, Department, Course, Student, Lecturer, Unit, NominalRoll, PasswordResetToken,
Response, LecturerUnit, Result, Complaint, System_User, AcademicYear
)

from .forms import (
SignUpForm, LoginForm, ResponseForm, PostComplaintForm, UploadFileForm, StudentRegNoForm, PasswordResetForm , ResetForm
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
        # Retrieve username from session
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is missing

        # Get logged-in lecturer details
        lecturer = Lecturer.objects.filter(username=username).first()
        last_name = lecturer.last_name  # Add last name to context
        user = System_User.objects.get(username=username)
        if not lecturer:
            return redirect('login')  # Redirect if no matching lecturer found

        department_name = lecturer.dep_code.dep_name

        # Total students taking courses related to the lecturer's department
        total_students = Student.objects.filter(
            course_code__dep_code=lecturer.dep_code
        ).count()

        # Total lecturers within the same department
        total_lecturers_in_department = Lecturer.objects.filter(
            dep_code=lecturer.dep_code
        ).count()

        # Total units related to the lecturer from LecturerUnit model
        total_units_for_lecturer = LecturerUnit.objects.filter(
            lec_no=lecturer.lec_no
        ).count()

        # Filter complaints related to lecturer's unit codes, academic year, and course codes
        lecturer_unit_codes = LecturerUnit.objects.filter(
            lec_no=lecturer.lec_no
        ).values_list('unit_code', flat=True)

        related_complaints_count = Complaint.objects.filter(
            unit_code__in=lecturer_unit_codes,
            academic_year__in=LecturerUnit.objects.filter(lec_no=lecturer).values_list('academic_year', flat=True),
            reg_no__course_code__in=LecturerUnit.objects.filter(lec_no=lecturer).values_list('course_code', flat=True)
        ).count()


        # Get all LecturerUnit instances for the lecturer
        units = LecturerUnit.objects.filter(lec_no=lecturer.lec_no)


        # Fetch all courses in the lecturer's department
        courses = Course.objects.filter(dep_code=lecturer.dep_code)

        # Pass calculated counts, units, and courses to the template
        context = {
            'total_students': total_students,
            'total_lecturers_in_department': total_lecturers_in_department,
            'total_units_for_lecturer': total_units_for_lecturer,
            'related_complaints_count': related_complaints_count,
            'last_name': last_name,
            'user': user,
            'units': units,
            'courses': courses,
            'department_name': department_name,
        }

        return render(request, 'lecturer_dashboard.html', context)

class Exam_DashboardView(View):
    def get(self, request):
        # Retrieve username from session
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is missing

        # Get logged-in lecturer details
        lecturer = Lecturer.objects.filter(username=username).first()
        last_name = lecturer.last_name  # Add last name to context
        user = System_User.objects.get(username=username)
        if not lecturer:
            return redirect('login')  # Redirect if no matching lecturer found

        department_name = lecturer.dep_code.dep_name

        # Total students taking courses related to the lecturer's department
        total_students = Student.objects.filter(
            course_code__dep_code=lecturer.dep_code
        ).count()

        # Total lecturers within the same department
        total_lecturers_in_department = Lecturer.objects.filter(
            dep_code=lecturer.dep_code
        ).count()

        # Total units related to the lecturer from LecturerUnit model
        total_units_for_lecturer = LecturerUnit.objects.filter(
            lec_no=lecturer.lec_no
        ).count()

        # Filter complaints related to lecturer's unit codes, academic year, and course codes
        lecturer_unit_codes = LecturerUnit.objects.filter(
            lec_no=lecturer.lec_no
        ).values_list('unit_code', flat=True)

        related_complaints_count = Complaint.objects.filter(
            unit_code__in=lecturer_unit_codes,
            academic_year__in=LecturerUnit.objects.filter(lec_no=lecturer).values_list('academic_year', flat=True),
            reg_no__course_code__in=LecturerUnit.objects.filter(lec_no=lecturer).values_list('course_code', flat=True)
        ).count()

        # Get all LecturerUnit instances for the lecturer
        units = LecturerUnit.objects.filter(lec_no=lecturer.lec_no)

        # Fetch all courses in the lecturer's department
        courses = Course.objects.filter(dep_code=lecturer.dep_code)

        # Pass calculated counts, units, and courses to the template
        context = {
            'total_students': total_students,
            'total_lecturers_in_department': total_lecturers_in_department,
            'total_units_for_lecturer': total_units_for_lecturer,
            'related_complaints_count': related_complaints_count,
            'last_name': last_name,
            'user': user,
            'units': units,
            'courses': courses,
            'department_name': department_name,
        }

        return render(request, 'exam_dashboard.html', context)

class COD_DashboardView(View):
    def get(self, request):
        # Retrieve username from session
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is missing

        # Get logged-in lecturer details
        lecturer = Lecturer.objects.filter(username=username).first()
        last_name = lecturer.last_name  # Add last name to context
        user = System_User.objects.get(username=username)
        if not lecturer:
            return redirect('login')  # Redirect if no matching lecturer found

        department_name = lecturer.dep_code.dep_name

        # Total students taking courses related to the lecturer's department
        total_students = Student.objects.filter(
            course_code__dep_code=lecturer.dep_code
        ).count()

        # Total lecturers within the same department
        total_lecturers_in_department = Lecturer.objects.filter(
            dep_code=lecturer.dep_code
        ).count()

        # Total units related to the lecturer from LecturerUnit model
        total_units_for_lecturer = LecturerUnit.objects.filter(
            lec_no=lecturer.lec_no
        ).count()

        # Filter complaints related to lecturer's unit codes, academic year, and course codes
        lecturer_unit_codes = LecturerUnit.objects.filter(
            lec_no=lecturer.lec_no
        ).values_list('unit_code', flat=True)

        related_complaints_count = Complaint.objects.filter(
            unit_code__in=lecturer_unit_codes,
            academic_year__in=LecturerUnit.objects.filter(lec_no=lecturer).values_list('academic_year', flat=True),
            reg_no__course_code__in=LecturerUnit.objects.filter(lec_no=lecturer).values_list('course_code', flat=True)
        ).count()

        # Get all LecturerUnit instances for the lecturer
        units = LecturerUnit.objects.filter(lec_no=lecturer.lec_no)

        # Fetch all courses in the lecturer's department
        courses = Course.objects.filter(dep_code=lecturer.dep_code)

        # Pass calculated counts, units, and courses to the template
        context = {
            'total_students': total_students,
            'total_lecturers_in_department': total_lecturers_in_department,
            'total_units_for_lecturer': total_units_for_lecturer,
            'related_complaints_count': related_complaints_count,
            'last_name': last_name,
            'user': user,
            'units': units,
            'courses': courses,
            'department_name': department_name,
        }

        return render(request, 'cod_dashboard.html', context)

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

        # Fetch the lecturer's units with academic years and course codes
        lecturer_units = LecturerUnit.objects.filter(lec_no=lecturer.lec_no)

        # Extract unit codes, course codes, and academic years into sets for optimized querying
        unit_codes = lecturer_units.values_list('unit_code', flat=True).distinct()
        academic_years = lecturer_units.values_list('academic_year', flat=True).distinct()
        course_codes = lecturer_units.values_list('course_code', flat=True).distinct()

        # Fetch student registration numbers associated with the courses taught by the lecturer
        reg_nos = Student.objects.filter(course_code__in=course_codes).values_list('reg_no', flat=True)

        # Query complaints associated with the lecturer's units, academic years, and student registration numbers
        complaints = Complaint.objects.filter(
            reg_no__in=reg_nos,
            unit_code__in=unit_codes,
            academic_year__in=academic_years
        )

        # Render the complaints in the template
        return render(request, self.template_name, {'complaints': complaints})

class Exam_ComplaintsView(ListView):
    template_name = 'exam_complaints_list.html'
    context_object_name = 'complaints'

    def get(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is not in session

        # Retrieve the lecturer based on the username
        lecturer = get_object_or_404(Lecturer, username=username)

        # Fetch the lecturer's units with academic years and course codes
        lecturer_units = LecturerUnit.objects.filter(lec_no=lecturer.lec_no)

        # Extract unit codes, course codes, and academic years into sets for optimized querying
        unit_codes = lecturer_units.values_list('unit_code', flat=True).distinct()
        academic_years = lecturer_units.values_list('academic_year', flat=True).distinct()
        course_codes = lecturer_units.values_list('course_code', flat=True).distinct()

        # Fetch student registration numbers associated with the courses taught by the lecturer
        reg_nos = Student.objects.filter(course_code__in=course_codes).values_list('reg_no', flat=True)

        # Query complaints associated with the lecturer's units, academic years, and student registration numbers
        complaints = Complaint.objects.filter(
            reg_no__in=reg_nos,
            unit_code__in=unit_codes,
            academic_year__in=academic_years
        )

        # Render the complaints in the template
        return render(request, self.template_name, {'complaints': complaints})

class COD_ComplaintsView(ListView):
    template_name = 'cod_complaints_list.html'
    context_object_name = 'complaints'

    def get(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is not in session

        # Retrieve the lecturer based on the username
        lecturer = get_object_or_404(Lecturer, username=username)

        # Fetch the lecturer's units with academic years and course codes
        lecturer_units = LecturerUnit.objects.filter(lec_no=lecturer.lec_no)

        # Extract unit codes, course codes, and academic years into sets for optimized querying
        unit_codes = lecturer_units.values_list('unit_code', flat=True).distinct()
        academic_years = lecturer_units.values_list('academic_year', flat=True).distinct()
        course_codes = lecturer_units.values_list('course_code', flat=True).distinct()

        # Fetch student registration numbers associated with the courses taught by the lecturer
        reg_nos = Student.objects.filter(course_code__in=course_codes).values_list('reg_no', flat=True)

        # Query complaints associated with the lecturer's units, academic years, and student registration numbers
        complaints = Complaint.objects.filter(
            reg_no__in=reg_nos,
            unit_code__in=unit_codes,
            academic_year__in=academic_years
        )

        # Render the complaints in the template
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
                response.academic_year = complaint.academic_year
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

class Exam_ResponseView(FormView):
    template_name = 'exam_response_form.html'
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
                response.academic_year = complaint.academic_year
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

        return redirect(reverse('exam-complaints'))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

class COD_ResponseView(FormView):
    template_name = 'cod_response_form.html'
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
                response.academic_year = complaint.academic_year
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

        return redirect(reverse('cod-complaints'))

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

class Exam_LoadNominalRollView(View):
    def get(self, request):
        form = UploadFileForm()
        return render(request, 'exam_load_nominal_roll.html', {'form': form})

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
                    return render(request, 'exam_load_nominal_roll.html', {'form': form})

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

                return render(request, 'exam_load_nominal_roll.html', {'form': form})

            except Exception as e:
                messages.error(request, f'An error occurred while processing the file: {str(e)}')
        else:
            messages.error(request, 'Invalid form submission.')

        return render(request, 'exam_load_nominal_roll.html', {'form': form})

class Exam_LoadResultView(View):
    def get(self, request):
        form = UploadFileForm()
        return render(request, 'exam_load_result.html', {'form': form})

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
                    return render(request, 'exam_load_result.html', {'form': form})

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

                return render(request, 'exam_load_result.html', {'form': form})

            except Exception as e:
                messages.error(request, f'An error occurred while processing the file: {str(e)}')
        else:
            messages.error(request, 'Invalid form submission.')

        return render(request, 'exam_load_result.html', {'form': form})

class Exam_ResultListView(ListView):
    model = Result
    template_name = 'exam_result_list.html'
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

class Exam_NominalRollListView(ListView):
    model = NominalRoll
    template_name = 'exam_nominal_roll_list.html'
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

class COD_LoadNominalRollView(View):
    def get(self, request):
        form = UploadFileForm()
        return render(request, 'cod_load_nominal_roll.html', {'form': form})

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
                    return render(request, 'cod_load_nominal_roll.html', {'form': form})

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

                return render(request, 'cod_load_nominal_roll.html', {'form': form})

            except Exception as e:
                messages.error(request, f'An error occurred while processing the file: {str(e)}')
        else:
            messages.error(request, 'Invalid form submission.')

        return render(request, 'cod_load_nominal_roll.html', {'form': form})

class COD_LoadResultView(View):
    def get(self, request):
        form = UploadFileForm()
        return render(request, 'cod_load_result.html', {'form': form})

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
                    return render(request, 'cod_load_result.html', {'form': form})

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

                return render(request, 'cod_load_result.html', {'form': form})

            except Exception as e:
                messages.error(request, f'An error occurred while processing the file: {str(e)}')
        else:
            messages.error(request, 'Invalid form submission.')

        return render(request, 'cod_load_result.html', {'form': form})

class COD_ResultListView(ListView):
    model = Result
    template_name = 'cod_result_list.html'
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

class COD_NominalRollListView(ListView):
    model = NominalRoll
    template_name = 'cod_nominal_roll_list.html'
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
            # Get the COD's department
            cod_lecturer = Lecturer.objects.get(username=username)
            department_lecturers = Lecturer.objects.filter(dep_code=cod_lecturer.dep_code)

            # Retrieve units taught by lecturers in the department
            lecturer_units = LecturerUnit.objects.filter(lec_no__in=department_lecturers)
            department_unit_codes = lecturer_units.values_list('unit_code', flat=True)
            department_course_codes = lecturer_units.values_list('course_code', flat=True)
            department_academic_years = lecturer_units.values_list('academic_year', flat=True)

            # Calculate the time threshold for overdue complaints (more than 24 hours)
            overdue_threshold = timezone.now() - timedelta(hours=24)

            # Retrieve overdue complaints related to the department's unit codes
            overdue_complaints = Complaint.objects.filter(
                date__lt=overdue_threshold,
                unit_code__in=department_unit_codes,
                academic_year__in=department_academic_years
            ).select_related('reg_no', 'academic_year', 'unit_code')  # Optimize with select_related

            # Extract reg_nos, unit codes, and academic years from the overdue complaints
            reg_nos = overdue_complaints.values_list('reg_no', flat=True)
            unit_codes = overdue_complaints.values_list('unit_code', flat=True)
            academic_years = overdue_complaints.values_list('academic_year', flat=True)

            # Get all course codes associated with the students in overdue complaints
            student_courses = Student.objects.filter(reg_no__in=reg_nos).values_list('course_code', flat=True).distinct()

            # Retrieve lec_no based on unit codes, academic years, and course codes
            relevant_lecturer_units = LecturerUnit.objects.filter(
                unit_code__in=unit_codes,
                academic_year__in=academic_years,
                course_code__in=student_courses
            ).values_list('lec_no', flat=True).distinct()

            # Retrieve lecturers with relevant lec_no to the complaints
            overdue_lecturers = Lecturer.objects.filter(
                lec_no__in=relevant_lecturer_units
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

            #lecturer_units = LecturerUnit.objects.all()

           # Extract reg_nos, unit codes, and academic years from the overdue complaints
            reg_nos = overdue_complaints.values_list('reg_no', flat=True)
            unit_codes = overdue_complaints.values_list('unit_code', flat=True)
            academic_years = overdue_complaints.values_list('academic_year', flat=True)

            # Get all course codes associated with the students in overdue complaints
            student_courses = Student.objects.filter(reg_no__in=reg_nos).values_list('course_code', flat=True).distinct()

            # Retrieve lec_no based on unit codes, academic years, and course codes
            relevant_lecturer_units = LecturerUnit.objects.filter(
                unit_code__in=unit_codes,
                academic_year__in=academic_years,
                course_code__in=student_courses
            ).values_list('lec_no', flat=True).distinct()

            # Retrieve lecturers with relevant lec_no to the complaints
            overdue_lecturers = Lecturer.objects.filter(
                lec_no__in=relevant_lecturer_units
            ).only('phone_number', 'email_address')

            # Prepare context data
            context = {
                'overdue_complaints': overdue_complaints,
                'overdue_lecturers': overdue_lecturers,
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

class LecturerStudentResponsesView(View):
    def get(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')  # Redirect to login if username is not in session

        try:
            # Get the COD's lecturer object
            lecturer = Lecturer.objects.get(username=username)
            department_code = lecturer.dep_code

            # Query responses and loaded results for students in the COD's department
            student_responses = Response.objects.filter(
                reg_no__course_code__dep_code=department_code
            ).select_related('reg_no', 'unit_code')


            context = {
                'student_responses': student_responses,
            }
            return render(request, 'lecturer_student_responses.html', context)

        except Lecturer.DoesNotExist:
            return render(request, 'lecturer_student_responses.html', {'error': 'Lecturer not found.'})

class DeleteResponseView(DeleteView):
    model = Response
    template_name = 'confirm_delete_response.html'
    success_url = reverse_lazy('lecturer-student-responses')

    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(request, "Response deleted successfully.")
            return response
        except Exception as e:
            messages.error(request, "Failed to delete response.")
            return redirect(self.success_url)



class ResetPasswordView(View):
    template_name = 'reset_password.html'
    form_class = PasswordResetForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']  # This is the email address
            user = System_User.objects.filter(username=username).first()
            if user:
                try:
                    # Generate a unique token
                    token = get_random_string(length=32)
                    # Save the token to the database
                    PasswordResetToken.objects.create(username=user, token=token)
                    # Generate the reset link
                    reset_link = request.build_absolute_uri(f'/reset-password/{token}/')
                    # Send password reset email
                    send_mail(
                        'Reset Your Password',
                        f'Click the link to reset your password: {reset_link}',
                        settings.EMAIL_HOST_USER,
                        [user.username],  # Use the username as the email address
                        fail_silently=False,
                    )
                    success_message = f"A password reset link has been sent to {user.username}."
                    return render(request, self.template_name, {'form': form, 'success_message': success_message})
                except Exception as e:
                    error_message = f"An error occurred: {str(e)} or Email Address does not exist in our records"
                    return render(request, self.template_name, {'form': form, 'error_message': error_message})
            else:
                error_message = "Email Address does not exist in our records."
                return render(request, self.template_name, {'form': form, 'error_message': error_message})

        return render(request, self.template_name, {'form': form})


class ResetPasswordConfirmView(View):
    template_name = 'reset_password_confirm.html'

    def get(self, request, token):
        form = ResetForm()
        password_reset_token = PasswordResetToken.objects.filter(token=token).first()

        if not password_reset_token or password_reset_token.is_expired():
            error_message = "Token is invalid or expired."
            return render(request, self.template_name, {'form': form, 'token': token, 'error_message': error_message})

        return render(request, self.template_name, {'form': form, 'token': token})

    def post(self, request, token):
        form = ResetForm(request.POST)
        password_reset_token = PasswordResetToken.objects.filter(token=token).first()

        if not password_reset_token or password_reset_token.is_expired():
            error_message = "Token is invalid or expired."
            return render(request, self.template_name, {'form': form, 'token': token, 'error_message': error_message})

        if form.is_valid():
            # Get user related to the token
            user = get_object_or_404(System_User, username=password_reset_token.username)
            form.save(user)  # Save the password to the user

            # Delete the token for security
            password_reset_token.delete()

            # Success message
            messages.success(request, "Your password has been reset successfully.")
            return render(request, self.template_name, {'form': form, 'token': token})

        # If form is not valid, show errors
        return render(request, self.template_name, {'form': form, 'token': token, 'error_message': "Invalid form submission."})


