from django.urls import path
from . import views
from .views import (
    SignUpView, LoginView, COD_DashboardView, Exam_DashboardView, Lecturer_DashboardView, LogoutView, StudentRegNo,
    ComplaintsView, Exam_ComplaintsView, COD_ComplaintsView,
    ResponseView, Exam_ResponseView, COD_ResponseView, 
    LoadNominalRollView, LoadResultView, LecturerOverdueComplaintsView, PostComplaint,
    StudentOverdueComplaintsView, ResponsesView, StudentResponsesView, NominalRollListView, ResultListView,
    LecturerStudentResponsesView, DeleteResponseView
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
    
    path('nominal-roll/', NominalRollListView.as_view(), name='nominal-roll'),
    path('result/', ResultListView.as_view(), name='result'),
    
    path('overdue-lecturer-complaints/', LecturerOverdueComplaintsView.as_view(), name='overdue-lecturer-complaints'),
    path('overdue-student-complaints/', StudentOverdueComplaintsView.as_view(), name='overdue-student-complaints'),
    
    path('responses/', ResponsesView.as_view(), name='responses'),
    path('students/responses/', StudentResponsesView.as_view(), name='student-responses'),    
    
    path('student/responses/', LecturerStudentResponsesView.as_view(), name='lecturer-student-responses'),
    
    path('delete-response/<int:pk>/', DeleteResponseView.as_view(), name='delete-response'),
]
