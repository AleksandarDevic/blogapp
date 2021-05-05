from django.db.models import Q
from rest_framework.authtoken.models import Token
from rest_framework.fields import IntegerField, ChoiceField, CharField
from rest_framework.serializers import ModelSerializer, ValidationError, Serializer

from articles.models import Writer, Article, APPROVAL_STATUS_CHOICES, APPROVED, REJECTED, PENDING


class WriterRegistrationSerializer(ModelSerializer):
    confirm_password = CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = Writer
        fields = ['name', 'password', 'is_editor', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def save(self, **kwargs):
        # print('save')
        writer = Writer(
            name=self.validated_data['name'],
            is_editor=self.validated_data['is_editor']
        )
        password = self.validated_data['password']
        confirm_password = self.validated_data['confirm_password']
        if password != confirm_password:
            raise ValidationError({'password': 'Passwords are not identical!'})
        writer.set_password(password)
        is_editor = self.validated_data['is_editor']
        writer.is_editor = is_editor
        writer.save()
        #
        Token.objects.create(user=writer)
        # print('token', token)
        #
        return writer


class WriterLoginSerializer(Serializer):
    name = CharField()
    password = CharField(style={'input_type': 'password'}, write_only=True)

    def validate(self, attrs):
        # print('validate')
        # print(attrs)
        # print(type(attrs))
        name = attrs['name']
        password = attrs['password']
        # print(name)
        # print(password)
        writer_qs = Writer.objects.filter(name__iexact=name)
        if not writer_qs.exists():
            raise ValidationError(f"Bad credentials - Writer with name: '{name}' does not exist!")
        writer = writer_qs[0]
        if not writer.check_password(password):
            raise ValidationError("Bad credentials - Wrong password!")
        attrs['writer'] = writer
        #
        return attrs


class WriterDetailSerializer(ModelSerializer):
    class Meta:
        model = Writer
        fields = ('id', 'name', 'is_editor')


class DashboardSerializer(ModelSerializer):
    num_all = IntegerField()
    num_lte30 = IntegerField()

    class Meta:
        model = Writer
        fields = ('id', 'name', 'is_editor', 'num_all', 'num_lte30')


class ArticleCreateSerializer(ModelSerializer):
    written_by = WriterDetailSerializer(read_only=True)
    edited_by = WriterDetailSerializer(allow_null=True, read_only=True)

    class Meta:
        model = Article
        fields = ('id', 'title', 'content', 'status', 'created_at', 'written_by', 'edited_by')
        extra_kwargs = {
            'id': {'read_only': True, },
            'title': {'write_only': True},
            'content': {'write_only': True},
            'status': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def validate(self, attrs):
        title = attrs['title']
        content = attrs['content']
        if Article.objects.filter(title=title).exists():
            raise ValidationError(f"Article with title:'{title}' already written!")
        if Article.objects.filter(content=content).exists():
            raise ValidationError("Article with the same content already written!")
        return attrs

    def create(self, validated_data):
        # print('create')
        writer = self.context['writer']
        # print(writer)
        title = validated_data['title']
        content = validated_data['content']
        status = PENDING
        article = Article.objects.create(
            title=title,
            content=content,
            status=status,
            written_by=writer
        )
        #
        return article


class ArticleDetailSerializer(ModelSerializer):
    written_by = WriterDetailSerializer(read_only=True)
    edited_by = WriterDetailSerializer(allow_null=True, read_only=True)

    class Meta:
        model = Article
        fields = ('id', 'title', 'content', 'status', 'created_at', 'written_by', 'edited_by')
        extra_kwargs = {
            'id': {'read_only': True},
            'status': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.title)
        #
        instance.save()

        return instance


class ArticleRetrieveUpdateSerializer(ModelSerializer):
    written_by = WriterDetailSerializer(read_only=True)
    edited_by = WriterDetailSerializer(allow_null=True, read_only=True)

    class Meta:
        model = Article
        fields = ('id', 'title', 'content', 'status', 'created_at', 'written_by', 'edited_by')
        extra_kwargs = {
            'id': {'read_only': True},
            'status': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def validate(self, attrs):
        title = attrs['title']
        content = attrs['content']
        # print(self.instance)
        if Article.objects.filter(
                Q(title=title) &
                ~Q(id=self.instance.id)
        ).exists():
            raise ValidationError(f"Article with title:'{title}' already written!")
        if Article.objects.filter(
                Q(content=content) &
                ~Q(id=self.instance.id)
        ).exists():
            raise ValidationError("Article with the same content already written!")
        #
        return attrs


class ArticleApprovalListSerializer(ModelSerializer):
    written_by = WriterDetailSerializer(read_only=True)

    class Meta:
        model = Article
        fields = ('id', 'title', 'content', 'created_at', 'written_by')
        extra_kwargs = {
            'id': {'read_only': True},
            'title': {'read_only': True},
            'content': {'read_only': True},
            'created_at': {'read_only': True},
        }


class ArticleApprovalUpdateSerializer(ModelSerializer):
    written_by = WriterDetailSerializer(read_only=True)
    edited_by = WriterDetailSerializer(allow_null=True, read_only=True)
    action = ChoiceField(write_only=True, allow_blank=False, choices=APPROVAL_STATUS_CHOICES)

    class Meta:
        model = Article
        fields = ('id', 'title', 'content', 'status', 'created_at', 'written_by', 'edited_by', 'action')
        extra_kwargs = {
            'id': {'read_only': True},
            'title': {'read_only': True},
            'content': {'read_only': True},
            'status': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def update(self, instance, validated_data):
        # print('update')
        action = validated_data.get('action', None)
        if action is None:
            raise ValidationError('Action field missing!')
        if action == APPROVED:
            instance.status = APPROVED
        elif action == REJECTED:
            instance.status = REJECTED
        else:
            raise ValidationError(f"The field: 'action' must have one of the values:('{APPROVED},{REJECTED}')!")
        # print(self.validated_data)
        # print(self.context['writer'])
        instance.edited_by = self.context['writer']
        instance.save()
        #
        return instance
