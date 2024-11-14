from django.db import models
from datetime import date
from django.utils import timezone
import random
import string
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from .validators import validate_reg_no, validate_kenyan_phone_number
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class School(models.Model):
    school_code = models.CharField(primary_key=True, unique=True, max_length=20, help_text="Please Enter School Code")
    school_name = models.CharField(max_length=200, help_text="Please Enter School Name")
    
    def __str__(self):
        return f"{self.school_code}"
    
class Department(models.Model):
    dep_code = models.CharField(primary_key=True, unique=True, max_length=20, help_text="Please Enter Department Code")
    dep_name = models.CharField(max_length=200, help_text="Please Enter Department Name")
    school_code = models.ForeignKey(School, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.dep_name}"
    
class Course(models.Model):
    course_code = models.CharField(primary_key=True, unique=True, max_length=20, help_text="Please Enter Course Code")
    course_name = models.CharField(max_length=200, help_text="Please Enter Course Name")
    dep_code = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.course_code}"
    
class Student(models.Model):
    reg_no = models.CharField(primary_key=True, unique=True, max_length=200, validators=[validate_reg_no], help_text="Please Enter Student Registration Number")
    username = models.CharField(unique=True, max_length=200, help_text="Enter a valid Username")
    first_name = models.CharField(max_length=200, help_text="Please Enter Student First Name")
    last_name = models.CharField(max_length=200, help_text="Please Enter Student Last Name")
    email_address = models.EmailField(max_length=200, help_text="Please Enter Student Email Address")
    phone_number = models.CharField(max_length=13, validators=[validate_kenyan_phone_number], help_text="Enter phone number in the format 0798073204 or +254798073404")
    course_code = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.reg_no}"
    
class Lecturer(models.Model):
    lec_no = models.CharField(primary_key=True, unique=True, max_length=20, help_text="Please Enter Lecturer Number")
    email_address = models.EmailField(max_length=200, help_text="Please Enter Lecturer Email Address")
    username = models.EmailField(unique=True, max_length=200, help_text="Enter a valid Username")
    first_name = models.CharField(max_length=200, help_text="Please Enter Student First Name")
    last_name = models.CharField(max_length=200, help_text="Please Enter Student Last Name")
    phone_number = models.CharField(max_length=13, validators=[validate_kenyan_phone_number], help_text="Enter phone number in the format 0798073204 or +254798073404")
    role = models.CharField(max_length=50, choices=[('Member', 'Member'), ('Exam Officer', 'Exam Officer'), ('COD', 'COD')])
    dep_code = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.email_address}"
    
class Unit(models.Model):
    unit_code = models.CharField(primary_key=True, unique=True, max_length=20, help_text="Please Enter Unit Code")
    unit_name = models.CharField(max_length=200, help_text="Please Enter Unit Name")
    dep_code = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.unit_code}"
   
class AcademicYear(models.Model):
    year_id = models.AutoField(primary_key=True)
    academic_year = models.CharField(max_length=200, help_text="Please Enter Academic Year")
    
    def __str__(self):
        return f"{self.academic_year}"
     
class LecturerUnit(models.Model):
    unit_code = models.ForeignKey(Unit, on_delete=models.CASCADE)
    lec_no = models.ForeignKey(Lecturer, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    course_code = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.lec_no}"

class NominalRoll(models.Model):
    unit_code = models.ForeignKey(Unit, on_delete=models.CASCADE)
    reg_no = models.ForeignKey(Student, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['unit_code', 'reg_no', 'academic_year'],
                name='unique_nominal_roll_per_unit_student_year'
            )
        ]

    def __str__(self):
        return f"{self.reg_no} - {self.unit_code} - {self.academic_year}"

    def clean(self):
        # Additional custom validation can be added here if needed
        if not self.unit_code or not self.reg_no or not self.academic_year:
            raise ValidationError("Unit code, student registration number, and academic year must be provided.")

    def save(self, *args, **kwargs):
        # Call clean method to perform validations before saving
        self.clean()
        super().save(*args, **kwargs)

class Result(models.Model):
    unit_code = models.ForeignKey(Unit, on_delete=models.CASCADE)
    reg_no = models.ForeignKey(Student, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    cat = models.IntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0), MaxValueValidator(30)]
    )
    exam = models.IntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0), MaxValueValidator(70)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['unit_code', 'reg_no', 'academic_year'],
                name='unique_result_per_unit_student_year'
            )
        ]

    @property
    def total(self):
        return (self.cat or 0) + (self.exam or 0)

    def __str__(self):
        return f"{self.reg_no} - {self.unit_code} - {self.academic_year}"

    def clean(self):
        if not self.unit_code or not self.reg_no or not self.academic_year or not self.cat or not self.exam:
            raise ValidationError("Unit code, student registration number, cat, exam, and academic year must be provided.")
        # Custom validation to ensure cat and exam fields are within range
        if self.cat and not (0 <= self.cat <= 30):
            raise ValidationError({'cat': 'CAT marks should be between 0 and 30.'})
        if self.exam and not (0 <= self.exam <= 70):
            raise ValidationError({'exam': 'Exam marks should be between 0 and 70.'})

    def save(self, *args, **kwargs):
        # Call clean method to perform validations before saving
        self.clean()
        super().save(*args, **kwargs)

class Complaint(models.Model):
    complaint_code = models.CharField(
        max_length=100,
        primary_key=True,
        unique=True,
        help_text="Please Enter Complaint Code"
    )
    unit_code = models.ForeignKey(Unit, on_delete=models.CASCADE)
    reg_no = models.ForeignKey(Student, on_delete=models.CASCADE)
    missing_mark = models.CharField(
        max_length=20,
        choices=[('CAT', 'CAT'), ('EXAM', 'EXAM'), ('ALL', 'ALL')]
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        help_text="Select Academic Year"
    )
    exam_date = models.DateField(help_text="Enter Main Exam Date, [dd, mm, yy]")
    description = models.TextField(help_text="Please Enter Description")
    date = models.DateField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['unit_code', 'reg_no'],
                name='unique_complaint_per_unit_student'
            )
        ]

    def __str__(self):
        return f"{self.complaint_code}"

    def save(self, *args, **kwargs):
        # Ensure clean validations are run before saving
        self.clean()
        super().save(*args, **kwargs)

class Response(models.Model):
    response_id = models.AutoField(primary_key=True, unique=True)
    response_code = models.CharField(max_length=100, unique=True)
    responder = models.ForeignKey(Lecturer, on_delete=models.CASCADE)
    response = models.CharField(
        max_length=100,
        choices=[
            ('No Result', 'No Result'),
            ('No CAT Mark', 'No CAT Mark'),
            ('No Exam Mark', 'No Exam Mark'),
            ('Result Loaded', 'Result Loaded')
        ],
        help_text="Select a response"
    )
    reg_no = models.ForeignKey(Student, on_delete=models.CASCADE)
    unit_code = models.ForeignKey(Unit, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    cat = models.CharField(max_length=3, default='-', help_text="Enter Cat Mark or -")  # Now non-nullable with default
    exam = models.CharField(max_length=3, default='-', help_text="Enter Exam Mark or -")  # Required field
    date = models.DateField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['reg_no', 'unit_code'],
                name='unique_response_per_student_unit'
            )
        ]

    def __str__(self):
        return f"{self.response_code}"

    def clean(self):
        # Ensure CAT and Exam are either '-' or within specified ranges
        if self.cat == '-' or (self.cat.isdigit() and 0 <= int(self.cat) <= 30):
            pass
        else:
            raise ValidationError("CAT must be an integer between 0 and 30, or '-'")
        
        if self.exam == '-' or (self.exam.isdigit() and 0 <= int(self.exam) <= 70):
            pass
        else:
            raise ValidationError("Exam must be an integer between 0 and 70, or '-'")

    def save(self, *args, **kwargs):
        # Apply custom clean validation before saving
        self.clean()
        super().save(*args, **kwargs)
    
class System_User(models.Model):
    username = models.CharField(primary_key=True, unique=True, max_length=50, help_text="Enter a valid Username")
    password_hash = models.CharField(max_length=128, help_text="Enter a valid password")  # Store hashed password

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def clean(self):
        # Custom validation for password field
        if len(self.password_hash) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

    def __str__(self):
        return self.username   

