# complaints/admin.py
from django.contrib import admin
from .models import (
    School, Department, Course, Student, Lecturer, Unit, NominalRoll,
    Response, LecturerUnit, Result, Complaint, System_User, AcademicYear, PasswordResetToken
)

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('school_code', 'school_name')
    search_fields = ('school_code', 'school_name')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('dep_code', 'dep_name', 'school_code')
    list_filter = ('school_code',)
    search_fields = ('dep_name', 'dep_code')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'course_name', 'dep_code')
    list_filter = ('dep_code',)
    search_fields = ('course_name', 'course_code')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('reg_no', 'first_name', 'last_name', 'email_address', 'phone_number', 'course_code')
    list_filter = ('course_code',)
    search_fields = ('reg_no', 'first_name', 'last_name', 'email_address')
    

@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ('lec_no', 'first_name', 'last_name', 'email_address', 'phone_number', 'dep_code')
    list_filter = ('dep_code',)
    search_fields = ('lec_no', 'first_name', 'role', 'last_name', 'email_address')

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('unit_code', 'unit_name', 'dep_code')
    list_filter = ('dep_code',)
    search_fields = ('unit_code', 'unit_name')

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year_id', 'academic_year')
    search_fields = ('academic_year',) 
    
@admin.register(LecturerUnit)
class LecturerUnitAdmin(admin.ModelAdmin):
    list_display = ('unit_code', 'lec_no', 'academic_year', 'course_code')
    list_filter = ('unit_code', 'course_code')
    search_fields = ('unit_code', 'lec_no', 'academic_year', 'course_code')
    
@admin.register(NominalRoll)
class NominalRollAdmin(admin.ModelAdmin):
    list_display = ('unit_code', 'reg_no', 'academic_year')
    list_filter = ('unit_code', 'reg_no', 'academic_year')
    search_fields = ('unit_code', 'reg_no', 'academic_year')
    
@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('unit_code', 'reg_no', 'academic_year', 'cat', 'exam')
    list_filter = ('unit_code', 'reg_no', 'academic_year')
    search_fields = ('unit_code', 'reg_no', 'academic_year', 'cat', 'exam')


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('complaint_code', 'unit_code', 'reg_no', 'missing_mark', 'exam_date')
    list_filter = ('unit_code', 'reg_no', 'academic_year')
    search_fields = ('unit_code', 'reg_no', 'academic_year')

@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('response_code', 'reg_no', 'unit_code', 'academic_year')
    list_filter = ('response_code', 'reg_no', 'unit_code', 'academic_year')
    search_fields = ('response_code', 'reg_no', 'unit_code', 'academic_year')

@admin.register(System_User)
class SystemUserAdmin(admin.ModelAdmin):
    list_display = ('username',)
    list_filter = ('username',)
    search_fields = ('username',)

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('username', 'token', 'created_at')
    list_filter = ('username',)
    search_fields = ('username', 'token', 'created_at')
