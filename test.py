import datetime
import stationary
import unittest


class TestPost(unittest.TestCase):
    def test_load_from_filename(self):
        post = stationary.post_from_filename('example/posts/example-post.md')
        self.assertEqual(post.title, 'Example Post')
        self.assertEqual(post.slug, 'example-post')
        self.assertEqual(post.pub_date, datetime.date(2012, 5, 19))

    def test_load_from_filename_stamped_slug(self):
        post = stationary.post_from_filename('example/posts/2012-05-21-example-post.md')
        self.assertEqual(post.slug, 'example-post')

    def test_urls(self):
        post = stationary.post_from_filename('example/posts/2012-05-21-example-post.md')
        self.assertEqual(post.url, '/blog/2012/05/21/example-post/')
        self.assertEqual(post.path, 'html/blog/2012/05/21/example-post/index.html')


class TestBlog(unittest.TestCase):
    def setUp(self):
        self.blog = stationary.blog_from_path('Blog Title', 'example/')

    def test_blog_from_path(self):
        self.assertEqual(self.blog.path, 'html/blog/index.html')
        for post in self.blog.posts:
            self.assertEqual(post.title, 'Example Post')
