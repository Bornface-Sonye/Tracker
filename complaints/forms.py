from django import forms
import random
import string
from .models import (
School, Department, Course, Student, Lecturer, Unit, NominalRoll, PasswordResetToken,
Response, LecturerUnit, Result, Complaint, System_User, AcademicYear
)

class SignUpForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'})
    )
    class Meta:
        model = System_User
        fields = ['username', 'password_hash']
        labels = {
            'username': 'Username',
            'password_hash': 'Password',
            'confirm_password': 'Confirm Password',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Username eg awaliaro@mmust.ac.ke'}),
            'password_hash': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Password'}),
            'confirm_password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password_hash")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Password and confirm password do not match")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.set_password(self.cleaned_data["password_hash"])
        if commit:
            instance.save()
        return instance
    
class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your Username:'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password:'})
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        return cleaned_data


class StudentRegNoForm(forms.Form):
    registration_number = forms.CharField(
        max_length=55,
        label="Registration Number",
        widget=forms.TextInput(attrs={'placeholder': 'Enter Registration Number'})
    )

class PostComplaintForm(forms.ModelForm):
    exam_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Exam Date"
    )

    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        empty_label="Select Academic Year",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Academic Year"
    )
    unit_code = forms.ModelChoiceField(
        queryset=Unit.objects.all(),  # Load all units
        empty_label="Select Unit",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Unit Code"
    )

    class Meta:
        model = Complaint
        fields = ['unit_code', 'academic_year', 'missing_mark', 'description', 'exam_date']
        widgets = {
            'missing_mark': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Select Missing Mark'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe the Issue', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)  # Pop 'student' out of kwargs if provided
        super().__init__(*args, **kwargs)
        
        # Load `missing_mark` choices from model
        self.fields['missing_mark'].choices = Complaint._meta.get_field('missing_mark').choices

    def generate_complaint_code(self):
        while True:
            letters = ''.join(random.choices(string.ascii_uppercase, k=3))
            numbers = ''.join(random.choices(string.digits, k=3))
            code = letters + numbers
            if not Complaint.objects.filter(complaint_code=code).exists():
                return code

    def save(self, commit=True):
        if not self.instance.complaint_code:
            self.instance.complaint_code = self.generate_complaint_code()
        return super().save(commit=commit)

class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ['response', 'cat', 'exam']
        widgets = {
            'response': forms.Select(attrs={'class': 'form-control'}),
            'cat': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '- for No mark'}),
            'exam': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '- for No mark'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        response = cleaned_data.get("response")
        cat = cleaned_data.get("cat")
        exam = cleaned_data.get("exam")

        if response == 'No Result':
            if cat != '-' or exam != '-':
                raise forms.ValidationError("For 'No Result', both CAT and Exam should be '-'")
        elif response == 'No CAT Mark' and cat != '-':
            raise forms.ValidationError("For 'No CAT Mark', CAT should be '-'")
        elif response == 'No Exam Mark' and exam != '-':
            raise forms.ValidationError("For 'No Exam Mark', Exam should be '-'")

        return cleaned_data

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select a CSV or Excel file')


class PasswordResetForm(forms.Form):
    username = forms.EmailField(
        label='Username',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address(Username)'})
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not System_User.objects.filter(username=username).exists():
            raise forms.ValidationError("This Username is not associated with any account.")
        return username
    
 
class ResetForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'})
    )
    
    class Meta:
        model = System_User
        fields = ['password_hash']
        labels = {
            'password_hash': 'Password',
            'confirm_password': 'Confirm Password',
        }
        widgets = {
            'password_hash': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password_hash")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Password and confirm password do not match")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.set_password(self.cleaned_data["password_hash"])
        if commit:
            instance.save()
        return instance    