from django.urls import re_path

from articles.views import DashboardWriterListView, logout_view, login_view, article_update_view, article_create_view, register_view, \
    article_approval_view, ArticlesEditedListView, drf_register_view, CustomWriterObtainAuthToken, DRFDashboardListAPIView, \
    DRFArticleRetrieveUpdateAPIView, DRFArticleApprovalListAPIView, DRFArticleApprovalUpdateAPIView, DRFArticleEditedListAPIView, \
    drf_article_create

urlpatterns = [
    #
    re_path('^$', DashboardWriterListView.as_view(), name='dashboard'),
    re_path('^article/create/$', article_create_view, name='article_create'),
    re_path('^article/(?P<pk>\d+)/$', article_update_view, name='article_update'),
    re_path('^article-approval/$', article_approval_view, name='article_approval'),
    re_path('^articles-edited/$', ArticlesEditedListView.as_view(), name='articles_edited'),
    #
    re_path('^register$', register_view, name='register'),
    re_path('^logout$', logout_view, name='logout'),
    re_path('^login$', login_view, name='login'),
    #
    ### Django Rest Framework API
    re_path('^drf-register$', drf_register_view, name='drf_register'),
    re_path('^drf-login$', CustomWriterObtainAuthToken.as_view(), name='drf_login'),
    #
    re_path('^drf-index$', DRFDashboardListAPIView.as_view(), name='drf_dashboard'),
    re_path('^drf-article/create/$', drf_article_create, name='drf_article_create'),
    re_path('^drf-article/(?P<pk>\d+)/$', DRFArticleRetrieveUpdateAPIView.as_view(), name='drf_article_retrieve_update'),
    re_path('^drf-article-approval/$', DRFArticleApprovalListAPIView.as_view(), name='drf_article_approval_list'),
    re_path('^drf-article-approval/(?P<pk>\d+)/$', DRFArticleApprovalUpdateAPIView.as_view(), name='drf_article_approval_update'),
    re_path('^drf_articles-edited/$', DRFArticleEditedListAPIView.as_view(), name='drf_articles_edited'),

]
