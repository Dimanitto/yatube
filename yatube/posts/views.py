from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow
from django.contrib.auth.decorators import login_required


# Главная страница
def index(request):
    '''в переменную posts будет сохранена выборка из 10 объектов модели Post,
    отсортированных уже в метаклассе по убыванию (от больших к меньшим)'''
    # порядок сортировки определен в классе Meta модели,
    post_list = Post.objects.all()
    # Показывать по 10 записей на странице.
    paginator = Paginator(post_list, 10)

    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get('page')

    # Получаем набор записей для страницы с запрошенным номером
    page_obj = paginator.get_page(page_number)
    # В словаре context отправляем информацию в шаблон
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


# Страница отфильтрованных по группам
def group_posts(request, slug):
    '''Функция get_object_or_404 получает по заданным критериям объект
    из базы данных или возвращает сообщение об ошибке, если объект не найден.
    В нашем случае в переменную group будут переданы объекты модели Group,
    поле slug у которых соответствует значению slug в запросе'''
    group = get_object_or_404(Group, slug=slug)

    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Страница для профиля"""
    # пришлось дать не дэфолтное название переменной (client)
    # вместо user, из-за этого совпадало с шапкой и показывало
    # пользователя неверно
    client = get_object_or_404(User, username=username)
    posts = client.posts.all()
    user_posts = posts.count()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Проверим подписан ли текующий пользователь на автора
    following = True
    # Передам в конекст проверку, чтобы не было кнопок
    # под самим собой же
    is_myself = False
    # Без этой проверки профиль не открывался у анонима
    if request.user.is_anonymous:
        following = False
    # Самого на себя подписаться нельзя
    elif client != request.user:
        if not Follow.objects.filter(
            user=request.user,
            author=client
        ).exists():
            following = False
    else:
        is_myself = True
    # Здесь код запроса к модели и создание словаря контекста
    context = {
        'client': client,
        'posts': posts,
        'user_posts': user_posts,
        'page_obj': page_obj,
        'following': following,
        'is_myself': is_myself,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница одного поста"""
    # Здесь код запроса к модели и создание словаря контекста
    post = get_object_or_404(Post, pk=post_id)
    # получаем все посты фильтруем их по автору имея один пост
    # благодаря тому что могу обраться к имени автора по одному
    # посту и посчитали
    count = Post.objects.all().filter(author=post.author).count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'count': count,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Страница для публикации постов"""
    # Проверяем, получен POST-запрос или какой-то другой:
    if request.method == 'POST':
        # Создаём объект формы класса ContactForm
        # и передаём в него полученные данные
        form = PostForm(request.POST or None, files=request.FILES or None)
        # Если все данные формы валидны - работаем с "очищенными данными" формы
        if form.is_valid():
            # Берём валидированные данные формы из словаря form.cleaned_data
            text = form.cleaned_data['text']
            group = form.cleaned_data['group']
            author = request.user
            image = form.cleaned_data['image']
            # сохраняем объект в базу
            Post.objects.create(
                text=text,
                group=group,
                author=author,
                image=image,
            )
            # Функция redirect перенаправляет пользователя
            # на другую страницу сайта, чтобы защититься
            # от повторного заполнения формы
            # сохраним адресс пользователя для redirect
            return redirect('posts:profile', author)
        # Если условие if form.is_valid() ложно и данные не прошли валидацию -
        # передадим полученный объект в шаблон,
        # чтобы показать пользователю информацию об ошибке

        # Заодно заполним все поля формы данными, прошедшими валидацию,
        # чтобы не заставлять пользователя вносить их повторно
        return render(request, 'posts/create_post.html', {'form': form})
    # Если пришёл не POST-запрос - создаём и передаём в шаблон пустую форму
    # пусть пользователь напишет что-нибудь
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Страница для редактирования поста"""
    is_edit = True
    # Проверим и найдем пост
    post = get_object_or_404(Post, pk=post_id)
    # Проверим что это не автор поста и сделаем
    # редирект
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    form = PostForm(instance=post)
    return render(
        request,
        'posts/create_post.html',
        {'is_edit': is_edit, 'form': form}
    )


@login_required
def add_comment(request, post_id):
    """Страница добавления комментария"""
    # Получили пост
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница  постов на подписанных авторов"""
    user = get_object_or_404(User, username=request.user)
    # Двойной related_name
    posts = Post.objects.filter(author__following__user=user)
    # Показывать по 10 страниц
    paginator = Paginator(posts, 10)
    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get('page')
    # Получаем набор записей для страницы с запрошенным номером
    page_obj = paginator.get_page(page_number)
    # В словаре context отправляем информацию в шаблон
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    # Получим автора
    author = get_object_or_404(User, username=username)
    # Самого на себя подписаться нельзя
    if author != request.user:
        # Чтобы не создавать повторяющихся объектов
        # get_or_create создаст объект если его нет,
        # а если есть просто вернет его
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора"""
    author = get_object_or_404(User, username=username)
    obj = Follow.objects.filter(
        user=request.user,
        author=author
    )
    obj.delete()
    return redirect('posts:profile', username)
