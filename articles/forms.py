from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import Form, CharField, PasswordInput, ModelForm, BooleanField

from articles.models import Writer, Article, STATUS_CHOICES


class WriterCreationForm(ModelForm):
    password = CharField(widget=PasswordInput)
    confirm_password = CharField(widget=PasswordInput)
    is_editor = BooleanField(required=False, initial=False)

    class Meta:
        model = Writer
        fields = ['name', 'password']

    def clean_name(self):
        name = self.cleaned_data['name']
        if Writer.objects.filter(name__iexact=name).exists():
            raise ValidationError(f"Writer with name:'{name}' already exists!")
        return name

    # def clean_password(self):
    #     print('clean_password')
    #     print(self.cleaned_data)
    #     password = self.cleaned_data['password']
    #     confirm_password = self.cleaned_data['confirm_password']
    #     if password != confirm_password:
    #         raise ValidationError('Passwords are not identical!')
    #     return password

    def clean(self):
        # print('clean')
        cleaned_data = super().clean()
        password = cleaned_data['password']
        confirm_password = cleaned_data['confirm_password']
        if password != confirm_password:
            raise ValidationError('Passwords are not identical!')
        return cleaned_data


class WriterLoginForm(Form):
    name = CharField()
    password = CharField(widget=PasswordInput)

    class Meta:
        fields = ['name', 'password']

    # def clean_name(self):
    #     name = self.cleaned_data['name']
    #
    #     if not Writer.objects.filter(name__iexact=name).exists():
    #         raise ValidationError(f"Bad credentials - Writer with name: '{name}' does not exist!")
    #     return name

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data['name']
        password = cleaned_data['password']
        writer_qs = Writer.objects.filter(name__iexact=name)
        if not writer_qs.exists():
            raise ValidationError(f"Bad credentials - Writer with name: '{name}' does not exist!")
        writer = writer_qs[0]
        if not writer.check_password(password):
            raise ValidationError("Bad credentials - Wrong password!")
        cleaned_data['writer'] = writer
        #
        return cleaned_data


class ArticleEditForm(ModelForm):
    # status = ChoiceField(choices=STATUS_CHOICES, widget=TextInput(attrs={'readonly': 'True'}))

    def __init__(self, *args, **kwargs):
        super(ArticleEditForm, self).__init__(*args, **kwargs)
        self.fields['status'].disabled = True
        self.fields['written_by'].disabled = True
        self.fields['edited_by'].disabled = True

    class Meta:
        model = Article
        fields = ['title', 'content', 'status', 'written_by', 'edited_by']

    def clean_title(self):
        new_title = self.cleaned_data['title']
        if Article.objects.filter(
                Q(title=new_title) &
                ~Q(id=self.instance.id)
        ).exists():
            raise ValidationError(f"Article with title:'{new_title}' already written!")
        #
        return new_title

    def clean_content(self):
        new_content = self.cleaned_data['content']
        if Article.objects.filter(
                Q(content=new_content) &
                ~Q(id=self.instance.id)
        ).exists():
            raise ValidationError("Article with the same content already written!")
        #
        return new_content


class ArticleCreateForm(ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content']

    def clean_title(self):
        title = self.cleaned_data['title']
        if Article.objects.filter(title=title).exists():
            raise ValidationError(f"Article with title:'{title}' already written!")
        return title
