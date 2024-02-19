<h1 align="center">Welcome to URL-Shortener 🌿</h1>

This is a small link shortener that is built on Werkzeug, Mako, Docker and Nginx. In addition, the project supports Authentication, CSRF, database and more. I hope to add tests here at some point.

<h1 align="center">Installation</h1>

**1.** Clone this repository how you like it.

**2.** Create the second required .env file with the following options **(url-shortener/url-shortener/.env)**.
```
SECRET_KEY, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
```

**3.** In addition, you can check the quality of the code if you need it.
```
$ cd blog/
$ pip3 install -r requirements.txt
$ pip3 install -r dev-requirements.txt
$ sudo chmod a+x lint.sh
$ ./lint.sh
```

**4.** Launch docker and all needed services.
```
$ docker-compose up --build
```
