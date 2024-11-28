from django.urls import path
from . import views
from .views import (
    SignUpView, LoginView, COD_DashboardView, Exam_DashboardView, Lecturer_DashboardView, LogoutView, StudentRegNo,
    ComplaintsView, Exam_ComplaintsView, COD_ComplaintsView, ResponseView, Exam_ResponseView, COD_ResponseView, 
    LoadNominalRollView, LoadResultView, Exam_LoadNominalRollView, Exam_LoadResultView, COD_LoadNominalRollView, 
    COD_LoadResultView, LecturerOverdueComplaintsView, PostComplaint, StudentOverdueComplaintsView, ResponsesView, 
    StudentResponsesView, LecturerStudentResponsesView, DeleteResponseView, NominalRollListView, ResultListView,
    Exam_NominalRollListView, Exam_ResultListView, COD_NominalRollListView, COD_ResultListView, ResetPasswordView, 
    ResetPasswordConfirmView
)

urlpatterns = [
    path('student/', StudentRegNo.as_view(), name='student'),
    path('post-complaint/', PostComplaint.as_view(), name='post-complaint'),
    
    path('complaints/', ComplaintsView.as_view(), name='complaints'),
    path('exam/complaints/', Exam_ComplaintsView.as_view(), name='exam-complaints'),
    path('cod/complaints/', COD_ComplaintsView.as_view(), name='cod-complaints'),
    
    path('lecturer/respond/<str:complaint_code>/', ResponseView.as_view(), name='response-form'),
    path('exam/respond/<str:complaint_code>/', Exam_ResponseView.as_view(), name='exam-response-form'),
    path('cod/respond/<str:complaint_code>/', COD_ResponseView.as_view(), name='cod-response-form'),
 
    path('register/',SignUpView.as_view(), name='signup'),
    path('login/',LoginView.as_view(), name='login'),
    
    path('lecturer-dashboard/',Lecturer_DashboardView.as_view(), name='lecturer-dashboard'),
    path('exam-dashboard/',Exam_DashboardView.as_view(), name='exam-dashboard'),
    path('cod-dashboard/',COD_DashboardView.as_view(), name='cod-dashboard'),
    
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('load-nominal-roll/', LoadNominalRollView.as_view(), name='load-nominal-roll'),
    path('load-result/', LoadResultView.as_view(), name='load-result'),
    
    path('exam/load-nominal-roll/', Exam_LoadNominalRollView.as_view(), name='exam-load-nominal-roll'),
    path('exam/load-result/', Exam_LoadResultView.as_view(), name='exam-load-result'),
    
    path('load-nominal-roll/', LoadNominalRollView.as_view(), name='load-nominal-roll'),
    path('load-result/', LoadResultView.as_view(), name='load-result'),
    
    path('cod/nominal-roll/', COD_NominalRollListView.as_view(), name='cod-nominal-roll'),
    path('cod/result/', COD_ResultListView.as_view(), name='cod-result'),
    
    path('exam/nominal-roll/', Exam_NominalRollListView.as_view(), name='exam-nominal-roll'),
    path('exam/result/', Exam_ResultListView.as_view(), name='exam-result'),
    
    path('cod/nominal-roll/', COD_LoadNominalRollView.as_view(), name='cod-load-nominal-roll'),
    path('cod/result/', COD_LoadResultView.as_view(), name='cod-load-result'),
    
    path('overdue-lecturer-complaints/', LecturerOverdueComplaintsView.as_view(), name='overdue-lecturer-complaints'),
    path('overdue-student-complaints/', StudentOverdueComplaintsView.as_view(), name='overdue-student-complaints'),
    
    path('responses/', ResponsesView.as_view(), name='responses'),
    path('students/responses/', StudentResponsesView.as_view(), name='student-responses'),    
    
    path('student/responses/', LecturerStudentResponsesView.as_view(), name='lecturer-student-responses'),
    
    path('delete-response/<int:pk>/', DeleteResponseView.as_view(), name='delete-response'),
    
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('reset-password/<str:token>/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
]
