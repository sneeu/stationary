from fabric.api import local, run
import stationary


def clean():
    stationary.clean()


def build():
    stationary.build()


def serve():
    stationary.serve()


def deploy():
    local('git add -p && git commit && git push')
    run('git pull')
