from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse

import os

class Post(models.Model):
    title = models.CharField(max_length=100)
    file = models.FileField(null=True, blank=True, upload_to='Files')
    content = models.TextField()
    location = models.CharField(max_length=255)  # Add default value here
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    application_count = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.title
    
    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk})

class Resume(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='resumes')
    resume = models.FileField(null=True, blank=True, upload_to='resumes')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    application_count = models.PositiveIntegerField(default=0)  # New field to track applications
    user = models.ForeignKey(User, on_delete=models.CASCADE)


    def __str__(self):
        return f'Resume for {self.post.title}'

        
