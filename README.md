HomeControl RPC Server and Apps
===============================

Django project & apps that implement RPC services for the Home Control system.

See [my blog post](http://itamaro.com/2013/10/04/ac-control-project-bringing-it-together/) for extended description and design.


Installation
------------

As a Django project & apps, installation and deployment are not different than [other Django projects](https://docs.djangoproject.com/en/1.5/howto/deployment/).

1. Clone the repository to the computer that will run the RPC app(s).
2. Optionally, create a `local_settings.py` file in `HomeControlRPC/HomeControlRPC` to override settings from the [generic settings file](HomeControlRPC/HomeControlRPC/settings.py) (feel free to use [local_settings.py.sample](HomeControlRPC/HomeControlRPC/local_settings.py.sample) as a suggestion).
3. Run `manage.py syncdb` to initialize the DB (and create a super user).
4. Set up your web server of choice to serve the Django site.
5. Access the admin interface (e.g. at `http://you-deployed-host/admin/`) to configure the installed RPC apps (see the app-specific documentation for details on their configurations).
6. Celebrate.


Available RPC Apps
------------------

- [A/C RPC App](HomeControlRPC/AC)
- [Remote Host RPC App](HomeControl/rhost)
- [WebCam RPC App](HomeControl/cam)


Dependencies
------------

- [Django](https://www.djangoproject.com/) (developed and tested with v1.5).
- For live audio recording, the A/C RPC app depends on [PyAlsaAudio library](http://pyalsaaudio.sourceforge.net/pyalsaaudio.html) for Linux (not supported in Windows).
- For signal energy graphing, the [mic module](HomeControlRPC/AC/mic.py) depends on [matplotlib library](http://matplotlib.org/) (version >= 3.0).
- For schema management and migrations (for development) - [Django South](http://south.aeracode.org/) (developed with v0.8).
