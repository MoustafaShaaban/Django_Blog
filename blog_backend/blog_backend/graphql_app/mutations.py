from graphql import GraphQLError

import graphene
from graphene_django.forms.mutation import DjangoModelFormMutation

from blog_backend.blog.models import Post, Comment, Tag
from blog_backend.blog.forms import TagForm

from .types import (
    PostType,
    CommentType,
    TagType,
)
from .inputs import PostInput, CommentInput


class CreatePostMutation(graphene.Mutation):
    class Arguments:
        input = PostInput(required=True)

    success = graphene.Boolean()
    post = graphene.Field(PostType)

    @staticmethod
    def mutate(root, info, input=None):
        success = True
        user = info.context.user
        tags = []

        for tag_input in input.tags:
            tag = Tag.objects.get(slug=tag_input.slug)
            if tag is None:
                return CreatePostMutation(success=False, post=None)
            tags.append(tag)
        
        post_instance = Post.objects.create(
            title=input.get('title'),
            author=user,
            content=input.get('content'),
        )
        post_instance.save()
        post_instance.tag.set(tags)
        success = True
        return CreatePostMutation(success=success, post=post_instance)


class UpdatePostMutation(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        input = PostInput(required=True)

    success = graphene.Boolean()
    post = graphene.Field(PostType)

    @staticmethod
    def mutate(root, info, id, input=None):
        success = False
        user = info.context.user
        tags = []
        post_instance = Post.objects.get(pk=id)

        if post_instance.author != user:
            raise GraphQLError("Only post author can update it")
        else:
            for tag_input in input.tags:
                tag = Tag.objects.get(slug=tag_input.slug)
                if tag is None:
                    return CreatePostMutation(success=False, post=None)
                tags.append(tag)

            post_instance.title = input.title
            post_instance.content = input.content
            post_instance.save()
            post_instance.tag.set(tags)
            success = True
        return UpdatePostMutation(success=success, post=post_instance)
    

class DeletePostMutation(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, info, id, input=None):
        user = info.context.user
        post_instance = Post.objects.get(pk=id)

        if post_instance.author != user:
            raise GraphQLError("Only post author can delete it")
        else:
            post_instance.delete()
            success = True
        return DeletePostMutation(success=success)


class CreateCommentMutation(graphene.Mutation):
    class Arguments:
        inputs = CommentInput(required=True)

    post = graphene.Field(PostType)
    comment = graphene.Field(CommentType)
        

    def mutate(self, info, inputs=None):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged to add a comment!')

        post = Post.objects.filter(slug=inputs.post_slug).first()
        if not post:
            raise GraphQLError('Invalid Post Slug!')

        Comment.objects.create(
            user=user,
            post=post,
            email=inputs.email,
            comment=inputs.comment,
        )

        return CreateCommentMutation(post=post)
    

class UpdateCommentMutation(graphene.Mutation):
    class Arguments:
        id = graphene.Int()
        comment = graphene.String()

    success = graphene.Boolean()
    comment = graphene.Field(CommentType)

    def mutate(root, info, id, comment):
        success = False
        user = info.context.user
        comment_instance = Comment.objects.get(pk=id)

        if comment_instance.user != user:
            raise GraphQLError("Only comment user can update it")
        else:
            comment_instance.comment = comment
            comment_instance.save()
            success = True
        return UpdateCommentMutation(success=success, comment=comment_instance)


class DeleteCommentMutation(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, info, id):
        user = info.context.user
        comment_instance = Comment.objects.get(pk=id)

        if comment_instance.user != user:
            raise GraphQLError("Only comment user can delete it")
        else:
            comment_instance.delete()
            success = True
        return DeleteCommentMutation(success=success, comment_instance=comment_instance)


class CreateTagMutation(DjangoModelFormMutation):
    tag = graphene.Field(TagType)

    class Meta:
        form_class = TagForm


class UpdateTagMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=True)
        slug = graphene.String()

    tag = graphene.Field(TagType)

    @classmethod
    def mutate(cls, root, info, id, name, slug):
        tag = Tag.objects.get(id=id)
        tag.name = name
        tag.slug = slug
        tag.save()

        return UpdateTagMutation(tag=tag)


class DeleteTagMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    tag = graphene.Field(TagType)
    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, id):
        tag = Tag.objects.get(id=id)
        tag.delete()
        success = True
        return DeleteTagMutation(tag=tag, success=success)