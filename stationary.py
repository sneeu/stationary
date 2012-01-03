import config
import shutil
import jinja2
import markdown2 as markdown
import os.path
import re
import yaml


POST_HEADER_SEP_RE = re.compile('^---$', re.MULTILINE)
DATE_FORMAT = '%Y-%m-%d %H:%M'


class Blog(object):
    def __init__(self, title, posts):
        self.title = title
        self.posts = posts

    def __str__(self):
        return config.TITLE

    @property
    def path(self):
        return '%s%sindex.html' % (
            config.OUT_PATH,
            config.BLOG_URL, )

    @property
    def url(self):
        return '/%s' % (config.BLOG_URL, )


class Post(object):
    def __init__(self, pub_date, title, slug, content):
        self.pub_date = pub_date
        self.title = title
        self.slug = slug
        self.content = content

    def __cmp__(self, other):
        return cmp(self.pub_date, other.pub_date)

    def __str__(self):
        return self.title

    @property
    def path(self):
        return '%s%s%s/index.html' % (
            config.OUT_PATH,
            config.BLOG_URL,
            config.POST_URL.format(post=self), )

    @property
    def url(self):
        return '/%s%s/' % (
            config.BLOG_URL,
            config.POST_URL.format(post=self), )


def post_from_filename(filename):
    with open(filename) as post:
        post_data = post.read()

    headers, content = re.split(POST_HEADER_SEP_RE, post_data, 1)

    headers = yaml.load(headers)
    content = markdown.markdown(content).strip()

    pub_date = headers['date']
    title = headers['title']

    slug, __ = os.path.splitext(os.path.basename(filename))

    match = re.match('\d{4}-\d{2}-\d{2}-(.+)', slug)
    if match:
        slug = match.group(1)

    return Post(pub_date, title, slug, content)


def blog_from_path(title, path):
    posts = []
    posts_path = os.path.join(path, 'posts/')
    for filename in os.listdir(posts_path):
        posts.append(post_from_filename(os.path.join(posts_path, filename)))
    return Blog(title, list(reversed(sorted(posts))))


def build_site():
    blog = blog_from_path(config.TITLE, config.IN_PATH)
    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(
            os.path.join(config.IN_PATH, 'templates/')))

    # Copy static files
    shutil.copytree(
        os.path.join(config.IN_PATH, 'static/'),
        config.OUT_PATH)

    # Render static pages

    # Render the base blog page
    blog_template = environment.get_template('index.html')
    if not os.path.isdir(os.path.dirname(blog.path)):
        os.makedirs(os.path.dirname(blog.path))
    with open(blog.path, 'w') as out_file:
        out_file.write(blog_template.render(blog=blog))

    # Render post pages
    post_template = environment.get_template('post.html')
    for post in blog.posts:
        if not os.path.isdir(os.path.dirname(post.path)):
            os.makedirs(os.path.dirname(post.path))
        with open(post.path, 'w') as out_file:
            out_file.write(post_template.render(blog=blog, post=post))


def clean():
    try:
        shutil.rmtree(config.OUT_PATH)
    except OSError:
        print '%s could not be deleted.' % config.OUT_PATH
