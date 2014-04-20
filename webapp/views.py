# coding=utf-8
from ajax import models as models_ajax
from bson import ObjectId
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from webapp.models import Profile, Tastes, Recipe, Comment, Time, Savour, Step, Picture
from ajax.models import UploadedImage

from django.contrib.auth.decorators import login_required
from django.contrib.auth import views

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotAllowed
from django.shortcuts import render

from webapp.forms import NewAccountForm, EditAccountForm, NewRecipeForm, AddComment
from django.forms.util import ErrorList
from datetime import datetime

from django.utils.translation import ugettext as _


def main(request):
    recipes = Recipe.objects.all().order_by('-creation_date')
    return render(request, 'webapp/main.html', {'recipes': recipes[:9]})


def new_account(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('main'))

    if request.method == 'POST':
        form = NewAccountForm(request.POST)
        if form.is_valid():  # else -> render respone with the obtained form, with errors and stuff
            # Extract the data from the form and create the User and Profile instance
            # TODO validar que el nombre de usuario sea único
            data = form.cleaned_data
            username = data['username']
            email = data['email']
            password = data['password']
            password_repeat = data['password_repeat']

            display_name = data['display_name']
            main_language = data['main_language']

            additional_languages = data['additional_languages']
            gender = data['gender']
            location = data['location']
            website = data['website']
            birth_date = data['birth_date']

            avatar_id = data['avatar_id']
            if avatar_id != u'':
                avatar = models_ajax.UploadedImage.objects.get(id=avatar_id)

            if not password == password_repeat:
                errors = form._errors.setdefault("password_repeat", ErrorList())
                output = _("Passwords don't match")
                errors.append(unicode(output))

            elif User.objects.filter(username=username).count():
                errors = form._errors.setdefault("username", ErrorList())
                output = _("Username alerady taken")
                errors.append(unicode(output))
            #todo: validar email único también
            else:
                u = User.objects.create_user(username, email, password)
                t = Tastes(salty=data['salty'],
                           sour=data['sour'],
                           bitter=data['bitter'],
                           sweet=data['sweet'],
                           spicy=data['spicy'])
                p = Profile(display_name=display_name, main_language=main_language, user=u,
                            additional_languages=additional_languages, gender=gender,
                            location=location, website=website,
                            birth_date=birth_date, tastes=t)
                #TODO capturar cualquier error de validación y meterlo como error en el formulario

                #avatar.image.name = str(p.id) + '.png' # No vale así, hay que copiar el archivo en otro
                if avatar_id != u'':
                    p.avatar = avatar.image

                p.clean()
                p.save()  # TODO borrar el User si falla al guardar el perfil

                #TODO marco de el UploadedImage para que no se borre. Pero lo mejor sería copiar la imagen a otro sitio
                if avatar_id != u'':
                    avatar.persist = True
                    avatar.save()

                u = authenticate(username=username, password=password)
                login(request, u)
                return HttpResponseRedirect(reverse('main'))  # Redirect after POST

    else:
        form = NewAccountForm()

    return render(request, 'webapp/newaccount.html', {'form': form})


@login_required
def new_recipe(request):
    #TODO if user is authenticated redirect to main
    if request.method == 'POST':
        # else -> render respone with the obtained form, with errors and stuff
        form = NewRecipeForm(request.POST)
        if form.is_valid:  # else -> render respone with the obtained form, with errors and stuff
            recipe = store_recipe(form, request.user)
            if recipe:
                return HttpResponseRedirect(reverse('recipe', kwargs={'recipe_id': recipe.id}))  # Redirect after POST
    else:
        form = NewRecipeForm()

    return render(request, 'webapp/newrecipe.html', {'form': form})


@login_required
def edit_receta(request, recipe_id):
    user = request.user
    r = Recipe.objects.get(id=ObjectId(recipe_id))

    if r.author != user:
        return HttpResponse('Unauthorized', status=401)

    if request.method == 'POST':
        form = NewRecipeForm(request.POST)
        if form.is_valid:  # else -> render respone with the obtained form, with errors and stuff
            recipe = store_recipe(form, request.user)
            if recipe:
                return HttpResponseRedirect(reverse('recipe', kwargs={'recipe_id': recipe.id}))  # Redirect after POST

    else:
        # fill the form with the recipe's data
        form = NewRecipeForm.get_filled_form(r)
        return render(request, 'webapp/newrecipe.html', {'form': form, 'edit': True})


def store_recipe(form, user):
    if form.is_valid():
        # Extract the data from the form and create the User and Profile instance
        data = form.cleaned_data

        # Basic information
        title = data['title']
        description = data['description']
        main_picture = data['main_picture_id']

        pictures_id_list = form.get_pictures_ids_list()
        ingredients = form.get_ingredients_list()
        steps = form.get_steps_list()

        serves = data['serves']
        language = data['language']
        temporality = data['temporality']
        nationality = data['nationality']
        special_conditions = data['special_conditions']
        notes = data['notes']
        difficult = data['difficult']
        food_type = data['food_type']
        tags = []
        tags_all = data['tags']
        prep_time = data['prep_time']
        cook_time = data['cook_time']
        if tags_all:
            tags = tags_all.split(",")

        # Genera la receta
        t = Savour(salty=data['salty'],
                   sour=data['sour'],
                   bitter=data['bitter'],
                   sweet=data['sweet'],
                   spicy=data['spicy'])

        time = Time(prep_time=prep_time, cook_time=cook_time)
        imagen_principal = UploadedImage.objects.get(id=main_picture).image

        r = Recipe(title=title, description=description, ingredients=ingredients, serves=serves,
                   language=language, temporality=temporality, nationality=nationality,
                   special_conditions=special_conditions,
                   notes=notes, difficult=difficult, food_type=food_type, tags=tags,
                   main_image=imagen_principal)
        u = user

        # steps is a list of dict
        step_list = list()
        for step in steps:
            if "picture" in step:
                picture = UploadedImage.objects.get(id=step["picture"]).image
                step_object = Step(text=step['text'], image=picture)
            else:
                step_object = Step(text=step['text'])

            step_list.append(step_object)
        r.steps = step_list

        # pictures_id_list is a list of ids
        pictures_list = list()
        if pictures_id_list:
            for pic in pictures_id_list:
                if pic:
                    picture = Picture(image=UploadedImage.objects.get(id=pic).image)
                    pictures_list.append(picture)

        r.pictures = pictures_list
        r.savours = t
        r.time = time
        r.author = u
        r.clean()
        r.save()
        return r
    else:
        return None


@login_required
def modification_account(request, username):
    # todo: hay mucho código repetido con respecto a la vista new_account. ¿Se pueden simplificar?
    if request.method == 'POST':
        form = EditAccountForm(request.POST)
        if form.is_valid():  # else -> render respone with the obtained form, with errors and stuff
            valid = True
            # Extract the data from the form, validate, and update the current user
            # TODO validar que el nombre de usuario sea único
            data = form.cleaned_data
            #username = data['username']
            #email = data['email']
            password = data['password']
            password_repeat = data['password_repeat']
            # TODO comparar las contraseñas y dar error si no son iguales

            display_name = data['display_name']
            main_language = data['main_language']

            additional_languages = data['additional_languages']
            gender = data['gender']
            location = data['location']
            website = data['website']
            birth_date = data['birth_date']

            avatar_id = data['avatar_id']

            if password:  # todo comprobar también que sea válida en cuanto a caracteres y tal
                if not password == password_repeat:
                    errors = form._errors.setdefault("password_repeat", ErrorList())
                    output = _("Passwords don't match")
                    errors.append(unicode(output))
                    valid = False

            u = request.user
            p = u.profile.get()

            t = Tastes(salty=data['salty'] if data['salty'] != None else 0,
                       sour=data['sour'] if data['sour'] != None else 0,
                       bitter=data['bitter'] if data['bitter'] != None else 0,
                       sweet=data['sweet'] if data['sweet'] != None else 0,
                       spicy=data['spicy'] if data['spicy'] != None else 0)

            p.display_name = display_name
            p.main_language = main_language
            p.additional_languages = additional_languages
            p.gender = gender
            p.website = website
            p.location = location
            p.birth_date = birth_date
            p.tastes = t

            if password:
                u.set_password(password)

            avatar = None
            if avatar_id:
                avatar = models_ajax.UploadedImage.objects.get(id=avatar_id)
                if avatar.image:
                    p.avatar = avatar.image
            # TODO capturar cualquier error de validación y meterlo como error en el formulario

            if valid:
                p.clean()
                p.save()  # TODO borrar el User si falla al guardar el perfil

                #TODO marco de el UploadedImage para que no se borre. Pero lo mejor sería copiar la imagen a otro sitio
                if avatar:
                    avatar.persist = True
                    avatar.save()
                # TODO mandar a la misma página y mostrar un mensaje de éxito
                return HttpResponseRedirect(reverse('main'))  # Redirect after POST

    else:
        u = request.user
        p = u.profile.get()
        data = {
            'username': u.username,
            'email': u.email,
            'display_name': p.display_name,
            'main_language': p.main_language,
            'additional_languages': p.additional_languages,
            'gender': p.gender,
            'location': p.location,
            'website': p.website,
            'birth_date': p.birth_date,
            'avatar_url': p.avatar.url,
            'salty': p.tastes.salty,
            'sour': p.tastes.sour,
            'bitter': p.tastes.bitter,
            'sweet': p.tastes.sweet,
            'spicy': p.tastes.spicy,
        }
        form = EditAccountForm(initial=data)

    return render(request, 'webapp/newaccount.html', {'form': form, 'edit': True})


def login_user(request):
    # Usa la Authentication View:
    # https://docs.djangoproject.com/en/1.5/topics/auth/default/#module-django.contrib.auth.views
    return views.login(request, 'webapp/login.html')


def logout_user(request):
    # TODO: estaría bien mostrar una página de logout correcto, o un mensaje en la principal
    return views.logout(request, next_page=reverse('main'))


def receta(request, recipe_id):
    recipe = Recipe.objects.get(id=recipe_id)
    return render(request, 'webapp/recipe_template.html', {'receta': recipe})


def profile(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise Http404
    user_profile = Profile.objects.get(user=user)
    recipes = Recipe.objects.raw_query({'author_id': ObjectId(user.id)})
    followers_list = Profile.objects.raw_query({'following.user_id': ObjectId(user.id)})
    is_owner = False
    if request.user.username == username:
        is_owner = True

    # Compruebo si está en mi lista de seguidos
    is_following = False
    if request.user.is_authenticated() and user.id != request.user.id:
        my_profile = request.user.profile.get()
        #TODO: INEFICIENTE, habría que hacer una búsqueda de verdad en la bbdd, pero ahora mismo no sé cómo se haría
        following_now = my_profile.following
        for f in following_now:
            if f.user.id == user.id:
                is_following = True

    return render(request, 'webapp/profile.html',
                  {'profile': user_profile, 'following': is_following, 'followers_list': followers_list,
                   'recipes': recipes, 'is_owner': is_owner})


def recipes(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise Http404

    recipes_list = Recipe.objects.raw_query({'author_id': ObjectId(user.id)})
    recipes_list.order_by('creation_date')
    return render(request, 'webapp/recipes.html', {'recipes': recipes_list})


def following(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise Http404

    is_owner = False
    if request.user.username == username:
        is_owner = True

    user_profile = Profile.objects.get(user=user)
    tag = "Following"
    return render(request, 'webapp/following.html',
                  {'follows': user_profile.following, 'profile': user_profile, 'tag': tag, 'is_owner': is_owner})


def followers(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise Http404

    is_owner = False
    if request.user.username == username:
        is_owner = True

    followers_list = Profile.objects.raw_query({'following.user_id': ObjectId(user.id)})
    user_profile = Profile.objects.get(user=user)
    tag = "Followers"
    return render(request, 'webapp/following.html',
                  {'follows': followers_list, 'profile': user_profile, 'tag': tag, 'is_owner': is_owner})


@login_required
def comment(request, recipe_id):
    if request.method == 'POST':
        u = request.user
        profile = u.profile.get()
        form = AddComment(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            c = Comment(text=text, create_date=datetime.now(), user_own=u, )
            r = Recipe.objects.get(id=recipe_id)
            r.comments.append(c)
            r.save()
    return HttpResponseRedirect(reverse('recipe', args=(recipe_id,)))


@login_required
def banned_comment(request, recipe_id, comment_id):
    if request.method == 'GET':
        u = request.user
        if u.is_staff:
            r = Recipe.objects.get(id=recipe_id)
            r.comments[int(comment_id)].is_banned = True
            r.save()
    return HttpResponseRedirect(reverse('recipe', args=(recipe_id,)))


@login_required
def unbanned_comment(request, recipe_id, comment_id):
    if request.method == 'GET':
        u = request.user
        if u.is_staff:
            r = Recipe.objects.get(id=recipe_id)
            r.comments[int(comment_id)].is_banned = False
            r.save()
    return HttpResponseRedirect(reverse('recipe', args=(recipe_id,)))
