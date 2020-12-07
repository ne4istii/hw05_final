from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import  Follow, Group, Post, User


def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request,"index.html", {         
        'page': page,
        'paginator': paginator
    }) 


@login_required
def follow_index(request):
    posts_following = Post.objects.filter(
        author__following__user=request.user
    )
    paginator = Paginator(posts_following, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {
        'page': page,
        'paginator': paginator,
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_group = group.posts.all()
    paginator = Paginator(posts_group, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html", {
        'page': page, 
        'paginator': paginator
    })


@login_required
def new_post(request):
    if request.method != 'POST':
        form = PostForm()
        return render(request, 'new.html', {
            'form': form
        })
    form = PostForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'new.html', {
       'form': form,
        'is_author': True
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    is_author = author == request.user  
    # is_following - подписан ли request.user на /username/?
    is_following = author.following.filter(
        user__username=request.user
        ).exists()
    # кол-во подписанных на /username/ - "подписчиков"
    if author.following.exists():
        following_counter = author.following.count()
    else:
        following_counter = 0
    # кол-во на кого подписан /username/ - "подписан"
    if author.follower.exists():
        follower_counter = author.follower.count()
    else:
        follower_counter = 0
    return render(request, "profile.html", {
        'page': page, 
        'author': author,
        'paginator': paginator,
        'posts': posts,
        'is_author': is_author,
        'is_following': is_following,
        'following_counter': following_counter,
        'follower_counter': follower_counter
    })


def post_view(request, username, post_id):
    post = get_object_or_404(
        Post.objects, 
        id=post_id,
        author__username=username,
    )
    posts = post.author.posts.all()
    author = post.author
    comments = post.comments.all()
    form = CommentForm()
    return render(request, 'post.html', {
        'form': form,
        'post': post,
        'author': author,
        'posts': posts,
        'comments': comments
    })


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(
        Post.objects, 
        author__username=username, 
        id=post_id
    )
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect(
           'post_view', 
            post.author, 
            post.id,
        )
    return render(request, 'comments.html', {
        'form': form,
        'post': post,
    })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(
        Post.objects, 
        author__username=username, 
        id=post_id
    )
    is_author = post.author == request.user
    if not is_author:
        return redirect(
            'post_view', 
            post.author, 
            post.id,
        )
    form = PostForm(
        request.POST or None, 
        files=request.FILES or None, 
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect(
            'post_view', 
            post.author, 
            post.id,
        )
    return render(request, 'new.html', {
        'form': form, 
        'post': post,
        'is_author': is_author
    })


def page_not_found(request, exception):
    return render(request, 'misc/404.html', 
        {"path": request.path}, 
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', 
        status=500
    ) 


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = get_object_or_404(User, username=request.user) 
    if author == user:
        return redirect(
            'profile', 
            author, 
        )
    is_following = author.following.filter(
        user__username=request.user
        ).exists()
    if is_following:
        return redirect(
            'profile', 
            username, 
        )
    Follow.objects.create(
            user = user,
            author = author
        )
    return redirect(
           'profile', 
            author, 
    )


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_following = author.following.filter(
        user__username=request.user
        ).exists()
    if is_following:
        author.following.filter(user__username=request.user).delete()
    return redirect(
           'profile', 
            author, 
    )
