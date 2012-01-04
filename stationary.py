import config
import shutil
import jinja2
import markdown2 as markdown
import os.path
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, TextLexer

import re
import yaml


POST_HEADER_SEP_RE = re.compile('^---$', re.MULTILINE)
DATE_FORMAT = '%Y-%m-%d %H:%M'
SOURCECODE_RE = re.compile(
    r'\[sourcecode:(.+?)\](.+?)\[/sourcecode\]', re.S)


def pygments_preprocess(lines):
    formatter = HtmlFormatter(noclasses=False)
    def repl(m):
        try:
            lexer = get_lexer_by_name(m.group(1))
        except ValueError:
            lexer = TextLexer()
        code = highlight(m.group(2), lexer, formatter)
        code = code.replace('\n\n', '\n&nbsp;\n').strip().replace('\n', '<br />')
        return '\n\n<div class="code">%s</div>\n\n' % code
    return SOURCECODE_RE.sub(repl, lines)


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


class Page(object):
    def __init__(self, path, content, meta_data=None):
        self._path = path
        self.content = content
        self.meta_data = meta_data

    @property
    def path(self):
        return '%s%s/index.html' % (
            config.OUT_PATH,
            self._path, )

    @property
    def url(self):
        return '/%s/' % (self._path, )


def post_from_filename(filename):
    with open(filename) as post_file:
        post_data = post_file.read()

    headers, content = re.split(POST_HEADER_SEP_RE, post_data, 1)

    headers = yaml.load(headers)
    content = markdown.markdown(pygments_preprocess(content)).strip()

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


def page_from_filename(filename, base_path):
    with open(filename) as page_file:
        page_data = page_file.read()

    header, content = re.split(POST_HEADER_SEP_RE, page_data, 1)

    meta_data = yaml.load(header)
    content = markdown.markdown(pygments_preprocess(content)).strip()

    slug, __ = os.path.splitext(os.path.relpath(filename, base_path))

    match = re.match('\d{4}-\d{2}-\d{2}-(.+)', slug)
    if match:
        slug = match.group(1)

    return Page(slug, content, meta_data=meta_data)


def pages_from_path(path):
    pages = []
    for dirname, folders, filenames in os.walk(path):
        for filename in filenames:
            page_path = os.path.join(dirname, filename)
            pages.append(page_from_filename(page_path, path))
    return pages


def build():
    blog = blog_from_path(config.TITLE, config.IN_PATH)
    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(
            os.path.join(config.IN_PATH, 'templates/')))

    # Copy static files
    shutil.copytree(
        os.path.join(config.IN_PATH, 'static/'),
        config.OUT_PATH)

    # Render static pages
    pages = pages_from_path(os.path.join(config.IN_PATH, 'pages/'))
    for page in pages:
        page_template_name = page.meta_data.get('template', 'page.html')
        page_template = environment.get_template(page_template_name)
        if not os.path.isdir(os.path.dirname(page.path)):
            os.makedirs(os.path.dirname(page.path))
        with open(page.path, 'w') as out_file:
            out_file.write(page_template.render(page=page))

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


def serve():
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

    MIMETYPES = {
        '.css': 'text/css',
        '.html': 'text/html',
        '.js': 'application/javascript',
    }

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path[1:]
            path = os.path.join(config.OUT_PATH, path)
            if self.path[-1] == '/':
                path = os.path.join(path, 'index.html')
            f = open(path)
            self.send_response(200)

            __, ext = os.path.splitext(self.path)
            mimetype = MIMETYPES.get(ext, 'text/html')
            self.send_header('Content-type', mimetype)
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
            return

    PORT = 8000

    server = HTTPServer(('', PORT), Handler)
    print "Serving at port", PORT
    server.serve_forever()
