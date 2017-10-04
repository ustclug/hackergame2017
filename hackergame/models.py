from django.db.models import (
    Model,
    TextField,
    IntegerField,
    ForeignKey,
    DateTimeField,
)
from django.contrib.auth.models import User


class Problem(Model):
    pid = TextField(unique=True)
    title = TextField()
    text = TextField()
    url = TextField()
    flag = TextField()
    score = IntegerField(default=100)

    def __str__(self):
        return '{0.score} - {0.pid}: {0.title}'.format(self)

    def user_solved(self):
        return self.solved_set.count()


class Solved(Model):
    user = ForeignKey(User)
    problem = ForeignKey(Problem)
    time = DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{0.user} <Problem: {0.problem}>'.format(self)
