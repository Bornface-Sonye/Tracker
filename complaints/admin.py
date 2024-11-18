# complaints/admin.py
from django.contrib import admin
from .models import ( School, Department, Course, Student, Lecturer, Unit, NominalRoll,
Response, LecturerUnit, Result, Complaint, System_User, AcademicYear, PasswordResetToken
)

admin.site.register(NominalRoll)
admin.site.register(Result)
admin.site.register(Complaint)
admin.site.register(Response)
admin.site.register(School)
admin.site.register(Department)
admin.site.register(Course)
admin.site.register(Student)
admin.site.register(Lecturer)
admin.site.register(Unit)
admin.site.register(LecturerUnit)
admin.site.register(System_User)
admin.site.register(AcademicYear)
admin.site.register(PasswordResetToken)
