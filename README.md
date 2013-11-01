HomeControl RPC Server and Apps
===============================

Django project & apps that implement RPC services for the Home Control system.

See [my blog post](http://itamaro.com/2013/10/04/ac-control-project-bringing-it-together/) for extended description and design.

Additional Home-Control projects:

- [HomeControl Web Front End](https://github.com/itamaro/home-control-web)
- [HomeControl Arduino A/C Controller](https://github.com/itamaro/home-control-arduino)


Requirements
------------

- [Django](https://www.djangoproject.com/) (developed and tested with v1.5).
- For live audio recording, the A/C RPC app requires [PyAlsaAudio library](http://pyalsaaudio.sourceforge.net/pyalsaaudio.html) for Linux (not supported in Windows).
- For signal energy graphing, the [mic module](HomeControlRPC/AC/mic.py) requires [matplotlib library](http://matplotlib.org/) (version >= 3.0).
- For schema management and migrations (for development) - [Django South](http://south.aeracode.org/) (developed with v0.8).


Installation
------------

As a Django project & apps, installation and deployment are not different than [other Django projects](https://docs.djangoproject.com/en/1.5/howto/deployment/).

1. Clone the repository to the computer that will run the RPC app(s).
2. Optionally, create a `local_settings.py` file in `HomeControlRPC/HomeControlRPC` to override settings from the [generic settings file](HomeControlRPC/HomeControlRPC/settings.py) (feel free to use [local_settings.py.sample](HomeControlRPC/HomeControlRPC/local_settings.py.sample) as a suggestion).
3. Run `manage.py syncdb` to initialize the DB (and create a super user).
4. Set up your web server of choice to serve the Django site.
5. Access the admin interface (e.g. at `http://your-deployed-host/admin/`) to configure the installed RPC apps (see the app-specific documentation for details on their configurations).
6. Celebrate.


Available RPC Apps
------------------

- [A/C RPC App](HomeControlRPC/AC)
- [WebCam RPC App](HomeControlRPC/cam)



Deployment Examples and Development Setup
=========================================


Web Server Agnostic Deployment on Ubuntu 12.04
----------------------------------------------

(tested with Ubuntu-Desktop-12.04.2-x64)

Install requirements:

* Python and various dependencies: `sudo apt-get install libexpat1 python-pip build-essential python-imaging python-pythonmagick python-markdown python-textile python-docutils`
 * **WARNING:** Do not install python-django via apt-get on 12.04 - the default repositories has an old version...
* Django: `sudo pip install Django`

Clone and configure the home-control-RPC project:

1. `cd ~`
2. `git clone https://github.com/itamaro/home-control-RPC.git`
3. `cd home-control-RPC/HomeControlRPC/HomeControlRPC`
4. `cp local_settings.py.sample local_settings.py`
   - Edit `local_settings.py` till happy.
5. `cd ..`
6. `python manage.py syncdb`
   - Create a super user

After setting up a web server to serve the Django site (see web-server-specific examples below),
access the Django admin interface (e.g. `http://localhost:8008/admin/`) to configure the installed apps (see [app-specific](#available-apps) README's for further details).


Nginx+Gunicorn on Ubuntu Deployment Example
-------------------------------------------

Soon


Local Development Setup in Windows
----------------------------------

(my dev-env is Windows 7 Professional SP1 x64)

1. Install Python, setuptools, pip, Git client (e.g. [Git Extensions](https://code.google.com/p/gitextensions/))
2. `pip install Django south nose django-nose mock`
3. Clone `https://github.com/itamaro/home-control-RPC.git` to your local workspace (e.g. `C:\Users\<name>\Workspaces\home-control\home-control-RPC`.
4. Copy `local_settings.py.win-dev-sample` to `local_settings.py` in the `HomeControlRPC\HomeControlRPC` directory.
   * Edit it until you're happy.
5. In command prompt, cd to `C:\Users\<name>\Workspaces\home-control\home-control-RPC\HomeControlRPC`
6. `python manage.py syncdb`
   * Create super user. 
7. `python manage.py runserver 8008`

The home-control-RPC site is now available on `http://localhost:8008/` -
access `/admin/` to configure app-settings, and hack away at the project.

You would probably also want to set up a local development environment of the [home-control-web project](https://github.com/itamaro/home-control-web/) in order to have a fully functional setup.

Please share interesting stuff you do!
