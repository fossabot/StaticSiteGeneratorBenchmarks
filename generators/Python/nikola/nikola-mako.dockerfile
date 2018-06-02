FROM codekoala/python
MAINTAINER Josh VanderLinden <codekoala@gmail.com>

RUN pacman -Sy --noconfirm --needed \
    python-pillow python-lxml python-dateutil python-pygments python-docutils \
    python-mako python-unidecode python-six python-pyinotify sqlite rsync \
    openssh
RUN pip install -U nikola webassets

ENTRYPOINT ["nikola"]
CMD []
