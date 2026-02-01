from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('superadmin', 'Superadmin'),
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student'
    )
    
    is_super = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_superuser_role(self):
        return self.role == 'superuser'
    
    def is_admin_role(self):
        return self.role == 'admin'
    
    def is_teacher_role(self):
        return self.role == 'teacher'
    
    def is_student_role(self):
        return self.role == 'student'
