from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from .models import Post
import operator
from django.urls import reverse_lazy
from django.contrib.staticfiles.views import serve

from django.db.models import Q
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from django.views.generic import DetailView
from .models import Post, Resume
from django.core.files.storage import FileSystemStorage
#------------------------------------------------------------
import os
import PyPDF2 as pdf
from django.shortcuts import render
from dotenv import load_dotenv
import google.generativeai as genai

# Load the environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

input_prompt = """
You are a skilled and very experienced ATS(Application Tracking System) with a deep understanding of tech field, software engineering,
data science, data analysis, and big data engineering. Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive and you should provide the best assistance for improving resumes. 
Assign the percentage Matching based on Job description and the missing keywords with high accuracy.
Resume:{extracted_text}
Description:{jd}

I want the only response in 3 sectors as follows:
• Job Description Match: \n
• Missing Keywords: \n
• Profile Summary: \n
"""

@login_required()
def tracking(request):
    response_data = None
    jd_value = ''
    if request.method == 'POST':
        jd_value = request.POST.get('jd', '')  # Lưu giữ giá trị job description nhập vào form

        # Check if 'resume' is in request.FILES
        if 'resume' in request.FILES:
            uploaded_file = request.FILES['resume']
            if uploaded_file.name.endswith('.pdf'):
                reader = pdf.PdfReader(uploaded_file)
                extracted_text = ""
                for page in reader.pages:
                    extracted_text += page.extract_text()

                # Generate content using generative AI model
                response = model.generate_content(input_prompt.format(extracted_text=extracted_text, jd=jd_value))
                # Process the response to split into sections
                # response_data = {
                #     'job_description_match': response.text.split('• Job Description Match: ')[1].split('• Missing Keywords: ')[0].strip(),
                #     'missing_keywords': response.text.split('• Missing Keywords: ')[1].split('• Profile Summary: ')[0].strip(),
                #     'profile_summary': response.text.split('• Profile Summary: ')[1].strip(),
                # }

                response_data = {
                    'result': response.text,
                }
    # Render the home.html template and pass response_data and jd_value
    return render(request, 'blog/tracking.html', {'response_data': response_data, 'jd_value': jd_value})


def home(request):
    context = {
        'posts': Post.objects.all()
    }
    return render(request, 'blog/home.html', context)

def search(request):
    template='blog/home.html'

    query=request.GET.get('q')

    result=Post.objects.filter(Q(title__icontains=query) | Q(author__username__icontains=query) | Q(content__icontains=query))
    paginate_by=2
    context={ 'posts':result }
    return render(request,template,context)
   


def getfile(request):
   return serve(request, 'File')


class PostListView(ListView):
    model = Post
    template_name = 'blog/home.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5


class UserPostListView(ListView):
    model = Post
    template_name = 'blog/user_posts.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    paginate_by = 2

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')


# class PostDetailView(DetailView):
#     model = Post
#     template_name = 'blog/post_detail.html'
class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        response_data = None
        jd_value = self.object.content  # Lấy giá trị job description từ nội dung bài viết

        if 'resume_matcher' in request.POST:
            # Handle Resume Matcher functionality
            if 'resume' in request.FILES:
                uploaded_file = request.FILES['resume']
                if uploaded_file.name.endswith('.pdf'):
                    reader = pdf.PdfReader(uploaded_file)
                    extracted_text = ""
                    for page in reader.pages:
                        extracted_text += page.extract_text()

                    # Generate content using generative AI model
                    response = model.generate_content(input_prompt.format(extracted_text=extracted_text, jd=jd_value))
                    response_data = {
                        'result': response.text,
                    }
                    
                context['response_data'] = response_data
                return self.render_to_response(context)

        elif 'apply' in request.POST:
            # Handle Apply functionality
            if 'resume' in request.FILES:
                resume_file = request.FILES['resume']
                resume_submission = Resume(
                    post=self.object,
                    resume=resume_file,
                    user=request.user  # Set the user who submitted the resume
                )
                resume_submission.save()

                # Increment the application count
                self.object.application_count += 1
                self.object.save()

                context['applied'] = True
                return self.render_to_response(context)

        return self.render_to_response(context)

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/post_form.html'
    fields = ['title', 'location', 'content', 'file']  # Include 'location'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    template_name = 'blog/post_update.html'
    fields = ['title', 'location', 'content', 'file']  # Include 'location'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author or self.request.user.is_superuser:
            return True
        return False


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'
    template_name = 'blog/post_confirm_delete.html'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author or self.request.user.is_superuser:
            return True
        return False


def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})

# def post_resumes(request, pk):
#     post = get_object_or_404(Post, pk=pk)
#     resumes = post.resumes.all()
#     return render(request, 'blog/post_resumes.html', {'post': post, 'resumes': resumes})

def post_resumes(request, pk):
    post = get_object_or_404(Post, pk=pk)
    resumes = Resume.objects.filter(post=pk)
    return render(request, 'blog/post_resumes.html', {'post': post, 'resumes': resumes})