from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.migrations import serializer
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from django.utils.decorators import method_decorator
from django.views.defaults import page_not_found
from django.views.generic import ListView
from pytz import unicode
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView, UpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.views import APIView

from articles.decorators import editor_only, unauthenticated_user
from articles.forms import WriterLoginForm, ArticleEditForm, ArticleCreateForm, WriterCreationForm
from articles.models import Writer, Article, PENDING, APPROVED, REJECTED
from articles.permissions import WriterHasEditorPermission
from articles.serializers import WriterRegistrationSerializer, WriterLoginSerializer, WriterDetailSerializer, DashboardSerializer, \
    ArticleRetrieveUpdateSerializer, ArticleApprovalListSerializer, ArticleApprovalUpdateSerializer, ArticleDetailSerializer, ArticleCreateSerializer


class DashboardWriterListView(ListView):
    template_name = 'index.html'
    paginate_by = 3

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super(DashboardWriterListView, self).get_context_data(*args, **kwargs)
        paginator = Paginator(context["object_list"], self.paginate_by)
        page = self.request.GET.get('page')
        try:
            writers = paginator.page(page)
        except PageNotAnInteger:
            writers = paginator.page(1)
        except EmptyPage:
            writers = paginator.page(paginator.num_pages)
        #
        context["object_list"] = writers
        # print(context)
        return context

    def get_queryset(self):
        return Writer.objects.get_writers_with_total_article_numbers_and_total_article_numbers_last_30_days()


@login_required(login_url='login')
def article_create_view(request):
    form = ArticleCreateForm()
    if request.method == 'POST':
        form = ArticleCreateForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.written_by = request.user
            article.save()
            #
            return redirect('article_update', pk=article.pk)
    context = {'form': form}
    return render(request, 'articles/create.html', context)


@login_required(login_url='login')
def article_update_view(request, pk):
    try:
        article = Article.objects.get(id=pk)
    except Article.DoesNotExist as dne:
        raise Http404()
    if request.user != article.written_by:
        # business logic is that only writer who wrote the article can update it.
        raise PermissionDenied('You are not authorize to edit this post!')
    form = ArticleEditForm(instance=article)
    if request.method == 'POST':
        form = ArticleEditForm(request.POST, instance=article)
        if form.is_valid():
            form.save(commit=False)
            # This will be used in 'article-approval' not here if we want to keep model without approval_by field
            # article.edited_by = request.user
            print(form)
            print(article)
            article.save()
            #
            return redirect("article_update", pk=article.id)
    context = {'form': form}
    return render(request, 'articles/update.html', context)


@login_required(login_url='login')
@editor_only
def article_approval_view(request):
    # articles = Article.objects.filter(status__exact=PENDING)
    if request.method == 'POST':
        # print(request.POST)
        # print(request.POST.get('action'))
        # print(request.POST.get('article_id'))
        article_id = request.POST.get('article_id')
        article = Article.objects.get(id=article_id)
        action = request.POST.get('action')
        if action == 'Approve':
            article.status = APPROVED
        elif action == 'Reject':
            article.status = REJECTED
        else:
            raise ValueError('Something wrong with approval form!!!')
        #
        # if we want to keep model without approval_by field
        article.edited_by = request.user
        article.save()
    articles = Article.objects.filter(status__exact=PENDING)

    context = {'articles': articles}
    return render(request, 'articles/approval.html', context=context)


# @login_required(login_url='login')
# @editor_only
class ArticlesEditedListView(ListView):
    template_name = 'articles/edited.html'
    paginate_by = 3

    @method_decorator(login_required)
    @method_decorator(editor_only)
    def dispatch(self, request, *args, **kwargs):
        # print(request)
        # print(args)
        # print(kwargs)
        # print('#' * 5)
        return super(ArticlesEditedListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super(ArticlesEditedListView, self).get_context_data(*args, **kwargs)
        paginator = Paginator(context["object_list"], self.paginate_by)
        page = self.request.GET.get('page')
        # print(context)
        try:
            articles = paginator.page(page)
        except PageNotAnInteger:
            articles = paginator.page(1)
        except EmptyPage:
            articles = paginator.page(paginator.num_pages)
        #
        context["object_list"] = articles
        # print(context)
        return context

    def get_queryset(self):
        return Article.objects.filter(
            Q(edited_by=self.request.user) &
            ~Q(status=PENDING)
        ).order_by('id')


@unauthenticated_user
def register_view(request):
    form = WriterCreationForm()
    if request.method == 'POST':
        form = WriterCreationForm(request.POST)
        if form.is_valid():
            # print('is_valid')
            writer = form.save(commit=False)
            writer.set_password(form.cleaned_data["password"])
            if form.cleaned_data['is_editor']:
                writer.is_editor = True
            #
            writer.save()
            login(request, user=writer)
            return redirect("dashboard")
    context = {'form': form}
    return render(request, "register.html", context)


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        return HttpResponseRedirect("/")
    else:
        return redirect('dashboard')


@unauthenticated_user
def login_view(request):
    form = WriterLoginForm()
    if request.method == 'POST':
        form = WriterLoginForm(request.POST)
        if form.is_valid():
            # print('is_valid')
            writer = form.cleaned_data.get('writer')
            login(request, user=writer)
            return redirect("/")
    context = {'form': form}
    return render(request, "login.html", context)


# Django REST Framework API

@api_view(['POST'])
@permission_classes([AllowAny])
def drf_register_view(request):
    # print('drf_register_view')
    if request.method == 'POST':
        serializer = WriterRegistrationSerializer(data=request.data)
        data = {}
        if serializer.is_valid():
            # print('is_valid')
            writer = serializer.save()
            data['response'] = "Successfully registered a new user."
            data['name'] = writer.name
            data['is_editor'] = writer.is_editor
            token = Token.objects.get(user=writer)
            data['token'] = token.key
            # print('data', data)
        else:
            data = serializer.errors
        # print(data)
        return Response(data)


class CustomWriterObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        # print('request.data: ', request.data)
        serializer = WriterLoginSerializer(data=request.data, context={'request': request})
        # print(serializer)
        # print(dir(serializer))
        data = {}
        if serializer.is_valid(raise_exception=True):
            # print('is_valid')
            writer = serializer.validated_data['writer']
            # print(writer)
            serialized_writer = WriterDetailSerializer(writer).data
            # print(serialized_writer)
            data['writer'] = serialized_writer
            token, created = Token.objects.get_or_create(user=writer)
            data['token'] = unicode(token.key)
        else:
            data = serializer.errors
        return Response(data)


class DRFDashboardListAPIView(ListAPIView):
    serializer_class = DashboardSerializer
    permission_classes = []

    def get_queryset(self):
        qs = Writer.objects.get_writers_with_total_article_numbers_and_total_article_numbers_last_30_days()
        # print(qs[0])
        # print(dir(qs[0]))
        return qs


@api_view(['POST'])
def drf_article_create(request):
    serializer = ArticleCreateSerializer(data=request.data, context={'writer': request.user})
    if serializer.is_valid():
        serializer.save()
        article_serialized = serializer.data
        return Response(article_serialized, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DRFArticleRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleRetrieveUpdateSerializer
    permission_classes = [IsAuthenticated, ]
    lookup_field = 'pk'


class DRFArticleApprovalListAPIView(ListAPIView):
    serializer_class = ArticleApprovalListSerializer
    permission_classes = [IsAuthenticated, WriterHasEditorPermission]

    def get_queryset(self):
        qs = Article.objects.filter(status__exact=PENDING)
        # print(qs)
        return qs


class DRFArticleApprovalUpdateAPIView(UpdateAPIView):
    serializer_class = ArticleApprovalUpdateSerializer
    permission_classes = [IsAuthenticated, WriterHasEditorPermission]
    queryset = Article.objects.all()
    lookup_field = 'pk'

    def put(self, request, *args, **kwargs):
        article = self.get_object()
        serializer = ArticleApprovalUpdateSerializer(instance=article, data=request.data, context={'writer': request.user})
        if serializer.is_valid():
            self.perform_update(serializer)
            article_serialized = serializer.data
            return Response(article_serialized, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DRFArticleEditedListAPIView(ListAPIView):
    serializer_class = ArticleRetrieveUpdateSerializer
    permission_classes = [IsAuthenticated, WriterHasEditorPermission]

    def get_queryset(self):
        return Article.objects.filter(
            Q(edited_by=self.request.user) &
            ~Q(status=PENDING)
        ).order_by('id')
