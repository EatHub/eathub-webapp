import django
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db.models import IntegerField, ForeignKey, CharField, TextField, DateTimeField, BooleanField
from djangotoolbox.fields import EmbeddedModelField, ListField, DictField
from django.core.exceptions import ValidationError
from datetime import datetime
from django_mongodb_engine.contrib import MongoDBManager

# --- Email registration ---

class Activation(models.Model):
    user = models.ForeignKey(User, related_name="activation", unique=True)
    code = models.CharField(max_length=100) #hash del usuario y la fecha
    date = models.DateTimeField()


# --- Profile ---

# Validators

def validate_savour(savour):
    if savour <= -1 or savour >= 100:
        raise ValidationError("Value is not in range 0 to 99")


def validate_main_language(main_language):
    pass


def validate_additional_languages(additional_languages):
    pass


def validate_last_login(last_login):
    if type(last_login) is not datetime:
        raise ValidationError(u'last login type must be date')
    if last_login is None:
        raise ValidationError(u'last login cannot be None')
    date = datetime.today()
    if last_login > date:
        raise ValidationError(u'last_login date cannot be after current date')


def validate_gender(gender):
    if not (gender == "u" or gender == "m" or gender == "f"):
        raise ValidationError(u'%s is not a valid gender' % gender)


def validate_past_date(date):
    now = datetime.now()
    if now > date:
        raise ValidationError(u'date cannot be future')


class Tastes(models.Model):
    salty = models.IntegerField(validators=[validate_savour])
    sour = models.IntegerField(validators=[validate_savour])
    bitter = models.IntegerField(validators=[validate_savour])
    sweet = models.IntegerField(validators=[validate_savour])
    spicy = models.IntegerField(validators=[validate_savour])

    def __str__(self):
        return "{}, {}, {}, {}, {}".format(self.salty, self.sour, self.bitter, self.sweet, self.spicy)


class Profile(models.Model):
    display_name = models.CharField(max_length=50, blank=False)
    modification_date = models.DateTimeField(null=True)
    main_language = models.CharField(max_length=50, validators=["""validate_main_language"""])
    additional_languages = ListField(validators=["""validate_additional_languages"""], null=True, blank=False)
    avatar = models.ImageField(upload_to='avatars/', null=True)
    website = models.URLField(null=True)
    gender = models.CharField(max_length=1, validators=[validate_gender], null=True)
    birth_date = models.DateField(null=True)
    location = models.CharField(max_length=50, blank=False)
    tastes = EmbeddedModelField('Tastes', null=True)
    user = models.ForeignKey(User, related_name="profile", unique=True)
    following = ListField(EmbeddedModelField('Following'))
    karma = models.IntegerField(default=6)
    username = models.CharField(max_length=50, blank=False)

    objects = MongoDBManager()

    def __str__(self):
        return str(self.display_name)

    def translate_to_lengague(self,lang):
        self.main_language=Language.objects.get(code=self.main_language).name_dict.get(lang)

    def get_recipes(self):
        return Recipe.objects.filter(author=self.user)


class Following(models.Model):
    display_name = models.CharField(max_length=50, blank=False)
    username = models.CharField(max_length=50, blank=False)
    user = models.ForeignKey(User)

    @staticmethod
    def create_following(user):
        return Following(display_name=user.profile.get().display_name, username=user.username, user=user)

# --- Recipe ---

# Validators

def validate_tags(tags):
    if len(tags) > 10:
        raise ValidationError("Max number of tags is 10")


def validate_difficult(difficult):
    if difficult <= 0 or difficult >= 4:
        raise ValidationError("Difficult must be in range 1 to 3")


# Models

class Comment(models.Model):
    text = models.TextField(blank=False)
    create_date = models.DateTimeField()
    user_own = ForeignKey(User)
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class Time(models.Model):
    prep_time = models.IntegerField()
    cook_time = models.IntegerField()

    def __str__(self):
        return "{}+{}".format(self.prep_time, self.cook_time)


class Savour(models.Model):
    salty = models.IntegerField(validators=[validate_savour])
    sour = models.IntegerField(validators=[validate_savour])
    bitter = models.IntegerField(validators=[validate_savour])
    sweet = models.IntegerField(validators=[validate_savour])
    spicy = models.IntegerField(validators=[validate_savour])

    def __str__(self):
        return "{}, {}, {}, {}, {}".format(self.salty, self.sour, self.bitter, self.sweet, self.spicy)


class Vote(models.Model):
    date = models.DateField(validators=[validate_past_date])
    user = ForeignKey(User)

    def __eq__(self, other):
        return self.user is other.user and self.date == other.date


class Step(models.Model):
    text = models.TextField(blank=False)
    image = models.ImageField(upload_to="images/recipe/",null=True)


class Picture(models.Model):
    image = models.ImageField(upload_to="images/",null=False)


class Recipe(models.Model):
    title = CharField(max_length=50, blank=False)
    description = TextField(blank=False)
    creation_date = DateTimeField(auto_now_add=True)
    main_image = models.ImageField(upload_to="images/recipe/", null=False)
    modification_date = DateTimeField(auto_now_add=True, null=True)
    ingredients = ListField(blank=False)
    serves = CharField(max_length=50, blank=False)
    language = CharField(max_length=50, blank=False)
    temporality = ListField(null=True)
    nationality = CharField(max_length=50, null=True)
    special_conditions = ListField(null=True)
    notes = TextField(null=True)
    difficult = IntegerField(null=True, validators=[validate_difficult])
    food_type = CharField(max_length=50, null=True)
    tags = ListField(null=True, validators=[validate_tags])

    is_published = BooleanField()
    parent = ForeignKey('self', null=True, blank=True)
    #embedded
    steps = ListField(EmbeddedModelField('Step'), null=False)
    author = ForeignKey(User)
    pictures = ListField(EmbeddedModelField('Picture'))
    time = EmbeddedModelField('Time')
    savours = EmbeddedModelField('Savour')
    comments = ListField(EmbeddedModelField('Comment'), blank=True)

    positives = ListField(EmbeddedModelField('Vote'))
    negatives = ListField(EmbeddedModelField('Vote'))

    objects = MongoDBManager()

    def __str__(self):
        return self.title

    def get_child_recipes(self):
        return Recipe.objects.filter(parent=self.id)

    def translate_to_language(self, lang):
        self.language=Language.objects.get(code=self.language).name_dict.get(lang)

    @staticmethod
    def search_recipes(data):
        query=dict()
        queryFullText = ""
        if data['bitter']!="":
            bitter = { "$lte": int(data['bitter'].split(',')[1]), "$gte": int(data['bitter'].split(',')[0])}
            query["savours.bitter"]=bitter
        if data['salty']!="":
            salty = { "$lte": int(data['salty'].split(',')[1]), "$gte": int(data['salty'].split(',')[0])}
            query["savours.salty"]=salty
        if data['sour']!="":
            sour = { "$lte": int(data['sour'].split(',')[1]), "$gte": int(data['sour'].split(',')[0])}
            query["savours.sour"]=sour
        if data['sweet']!="":
            sweet = { "$lte": int(data['sweet'].split(',')[1]), "$gte": int(data['sweet'].split(',')[0])}
            query["savours.sweet"]=sweet
        if data['spicy']!="":
            spicy = { "$lte": int(data['spicy'].split(',')[1]), "$gte": int(data['spicy'].split(',')[0])}
            query["savours.spicy"]=spicy
        if data['difficult']!="":
            query["difficult"]=data['difficult']
        if data['language']!="":
            query["language"] = data['language']
        if data['food_type']!="":
            query["food_type"] = data['food_type']
        if data['srchterm']!="":
            queryFullText= queryFullText + data['srchterm']
        if len(data['special_conditions'])!=0:
            special=list()
            for sp in data['special_conditions']:
                special.append(sp)
            queryFullText = queryFullText + " ".join(special)

        if queryFullText!="":
            query["$text"] = {"$search" : queryFullText}

        if len(data['temporality'])!=0:
            temporal=list()
            for sp in data['temporality']:
                temporal.append({"temporality": sp})
            query["$or"] = temporal
        #"$or": [{"language": "spanish"},{"language": "english"}],

        results_recipes = Recipe.objects.raw_query(query)
        return results_recipes


#enum to entity


class Temporality(models.Model):
    code = CharField(max_length=50, blank=False)
    name_dict = DictField()

    @staticmethod
    def get_name_on_language(lang):
        all = Temporality.objects.all()
        dict=list()
        for t in all:
            dict.append((t.code,t.name_dict.get(lang)))
        return dict


class Language(models.Model):
    code = CharField(max_length=50, blank=False)
    name_dict = DictField()

    @staticmethod
    def get_name_on_language(lang):
        all = Language.objects.all()
        dict=list()
        for t in all:
            dict.append((t.code,t.name_dict.get(lang)))
        return dict

class Food_Type(models.Model):
    code = CharField(max_length=50, blank=False)
    name_dict = DictField()

    @staticmethod
    def get_name_on_language(lang):
        all = Food_Type.objects.all()
        dict=list()
        for t in all:
            dict.append((t.code,t.name_dict.get(lang)))
        return dict


class Special_Condition(models.Model):
    code = CharField(max_length=50, blank=False)
    name_dict = DictField()

    @staticmethod
    def get_name_on_language(lang):
        all = Special_Condition.objects.all()
        dict=list()
        for t in all:
            dict.append((t.code,t.name_dict.get(lang)))
        return dict
