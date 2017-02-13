import cgi
import os
import urllib
import time
import jinja2
import webapp2
import MySQLdb
import gzip

from google.appengine.api import users
from google.appengine.api import files
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# Define your production Cloud SQL instance information.
# _INSTANCE_NAME = 'APP-ID:DATABASE-SERVERNAME' # REFER YOUR CLOUD SQL NAME
CLOUDSQL_INSTANCE = 'viewtube-147407:us-central1:mahesh123'


class DBConnector():
    def createConnection(self):

        if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
            db = MySQLdb.connect(
                unix_socket='/cloudsql/{}'.format(
                    CLOUDSQL_INSTANCE), db='tumblrr',
                user='root')
        # When running locally, you can either connect to a local running
        # MySQL instance, or connect to your Cloud SQL instance over TCP.
        else:
            db = MySQLdb.connect(host='localhost', user='root')

        return db


class MainPage(webapp2.RequestHandler):
    def get(self):

        dbhandle = DBConnector()
        db = dbhandle.createConnection()
        cursor = db.cursor()
        nickname = "Guest"
        category = self.request.get('category')

        if category:
            cursor.execute(
                'SELECT fid, title, blob_id, filetype, upload_timestamp FROM uploads where filetype = %s order by fid desc',
                category)
        else:
            cursor.execute('SELECT fid, title, blob_id, filetype, upload_timestamp FROM uploads order by fid desc')
            category = ""


        uploaded_files = [];
        for row in cursor.fetchall():
            uploaded_files.append(dict([('fid', row[0]),
                                        ('title', row[1]),
                                        ('blob_id', row[2]),
                                        ('filetype', row[3]),
                                        ('timestamp', time.ctime(row[4]))
                                        ]))

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            user = users.get_current_user()
            nickname = user.nickname()
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        blob_upload_url = blobstore.create_upload_url("/upload")

        template_values = {

            'url': url,
            'url_linktext': url_linktext,
            'user_nickname': nickname,
            'uploaded_files': uploaded_files,
            'upload_url': blob_upload_url,
            'category': category,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class ImageEditPage(webapp2.RequestHandler):
    def get(self):

        dbhandle = DBConnector()
        db = dbhandle.createConnection()
        cursor = db.cursor()

        image_id = self.request.get('image_id')
        cursor.execute(
            'SELECT title, blob_id, filetype, upload_timestamp, fid FROM uploads where fid ="{0}"'.format(image_id))

        # Create a list of files to render with the HTML.
        uploaded_files = [];
        for row in cursor.fetchall():
            uploaded_files.append(dict([('title', row[0]),
                                        ('blob_id', row[1]),
                                        ('filetype', row[2]),
                                        ('timestamp', time.ctime(row[3]))
                                        ]))
            blob_id = row[1]

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            user = users.get_current_user()
            nickname = user.nickname()
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {

            'url': url,
            'url_linktext': url_linktext,
            'user_nickname': nickname,
            'uploaded_files': uploaded_files,
            'blob_id': blob_id,
            'image_id': image_id,
        }

        template = JINJA_ENVIRONMENT.get_template('imageedit.html')
        self.response.write(template.render(template_values))


class ImageEditsPage(webapp2.RequestHandler):
    def get(self):

        dbhandle = DBConnector()
        db = dbhandle.createConnection()
        cursor = db.cursor()

        image_id = self.request.get('image_id')
        cursor.execute(
            'SELECT title, blob_id, filetype, upload_timestamp, fid FROM uploads where fid ="{0}"'.format(image_id))

        # Create a list of files to render with the HTML.
        uploaded_files = [];
        for row in cursor.fetchall():
            uploaded_files.append(dict([('title', row[0]),
                                        ('blob_id', row[1]),
                                        ('filetype', row[2]),
                                        ('timestamp', time.ctime(row[3]))
                                        ]))
            blob_id = row[1]

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            user = users.get_current_user()
            nickname = user.nickname()
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {

            'url': url,
            'url_linktext': url_linktext,
            'user_nickname': nickname,
            'uploaded_files': uploaded_files,
            'blob_id': blob_id,
            'image_id': image_id,
        }

        template = JINJA_ENVIRONMENT.get_template('imageedits.html')
        self.response.write(template.render(template_values))


class UploadFile(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')
        blob_info = upload_files[0]

        timestamp = int(str(time.time()).split('.')[0])
        filename = self.request.get('file')
        title = self.request.get('title')
        filetype = int(self.request.get('filetype'))
        blobkey = blob_info.key()

        dbhandle = DBConnector()
        db = dbhandle.createConnection()
        cursor = db.cursor()

        # Note that the only format string supported is %s
        cursor.execute('INSERT INTO uploads (filetype, title, upload_timestamp, blob_id) VALUES (%s, %s, %s, %s)',
                       (filetype, title, timestamp, blobkey))
        db.commit()
        db.close()

        self.redirect('/')


class Thumbnailer(webapp2.RequestHandler):
    def get(self):
        blob_key = self.request.get("blob_key")
        if blob_key:
            blob_info = blobstore.get(blob_key)

            if blob_info:
                img = images.Image(blob_key=blob_key)
                img.resize(width=320, height=240)

                # img.im_feeling_lucky()
                thumbnail = img.execute_transforms(output_encoding=images.JPEG)

                self.response.headers['Content-Type'] = 'image/jpeg'
                self.response.out.write(thumbnail)
                return

        # Either "blob_key" wasn't provided, or there was no value with that ID
        # in the Blobstore.
        self.error(404)
        # self.response.out('Image Not Found')


class LargeImage(webapp2.RequestHandler):
    def get(self):
        blob_key = self.request.get("blob_key")
        if blob_key:
            blob_info = blobstore.get(blob_key)

            if blob_info:
                img = images.Image(blob_key=blob_key)
                img.resize(width=600)
                img.resize(height=400)
                # img.crop(0.3, 0.3, 0.7, 0.7)
                img.rotate(180)
                # img.im_feeling_lucky()
                thumbnail = img.execute_transforms(output_encoding=images.JPEG)

                self.response.headers['Content-Type'] = 'image/jpeg'
                self.response.out.write(thumbnail)
                return

        # Either "blob_key" wasn't provided, or there was no value with that ID
        # in the Blobstore.
        self.error(404)
        # self.response.out('Image Not Found')


class Cropper(webapp2.RequestHandler):
    def get(self):
        blob_key = self.request.get("blob_key")
        if blob_key:
            blob_info = blobstore.get(blob_key)

            if blob_info:
                img = images.Image(blob_key=blob_key)
                img.resize(width=600)
                img.resize(height=400)
                img.crop(0.1, 0.1, 0.5, 0.5)
                # img.rotate(90)
                # img.im_feeling_lucky()
                thumbnail = img.execute_transforms(output_encoding=images.JPEG)

                self.response.headers['Content-Type'] = 'image/jpeg'
                self.response.out.write(thumbnail)
                return

        # Either "blob_key" wasn't provided, or there was no value with that ID
        # in the Blobstore.
        self.error(404)
        # self.response.out('Image Not Found')


class GetRawFile(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        blob_key = self.request.get("blob_key")
        if blob_key:
            blob_info = blobstore.get(blob_key)

            if blob_info:
                self.send_blob(blob_key)
                return

        # Either "blob_key" wasn't provided, or there was no value with that ID
        # in the Blobstore.
        self.error(404)
        # self.response.out('Image Not Found')


class GetZipFile(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        blob_key = self.request.get("blob_key")
        if blob_key:
            blob_info = blobstore.get(blob_key)

            blobfile = files.blobstore.create(mime_type='application/gzip')
            with files.open(blobfile, 'a') as f:
                gz = gzip.GzipFile(fileobj=f, mode='wb')

                rowfile = GetRawFile()

                gz.write(rowfile.get(blob_key))
                gz.close()
                return

        # Either "blob_key" wasn't provided, or there was no value with that ID
        # in the Blobstore.
        self.error(404)
        # self.response.out('Image Not Found')


class DeleteFile(webapp2.RequestHandler):
    def get(self):
        blob_key = self.request.get("blob_key")
        if blob_key:
            blob_info = blobstore.get(blob_key)

            dbhandle = DBConnector()
            db = dbhandle.createConnection()
            cursor = db.cursor()

            # delete from blobstore
            blob_info.delete()

            # delete record from mySQL
            cursor.execute('DELETE FROM uploads where blob_id ="{}"'.format(blob_key))
            db.commit()

        self.redirect('/')


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/upload', UploadFile),
    ('/thumb', Thumbnailer),
    ('/delete', DeleteFile),
    ('/getrawfile', GetRawFile),
    ('/imagelarge', LargeImage),
    ('/cropper', Cropper),
    ('/imageedit', ImageEditPage),
    ('/imageedits', ImageEditsPage),
    ('/getzipfile', GetZipFile),
], debug=True)
