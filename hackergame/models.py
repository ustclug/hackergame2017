from django.db.models import (
    Model,
    TextField,
    IntegerField,
    ForeignKey,
    TimeField,
)
from django.contrib.auth.models import User


class Problem(Model):
    title = TextField()
    text = TextField()
    url = TextField()
    flag = TextField()
    score = IntegerField(default=100)

    def __str__(self):
        return '<Problem: {0.score} - {0.title}>'.format(self)


class Solved(Model):
    user = ForeignKey(User)
    problem = ForeignKey(Problem)
    time = TimeField()

    def __str__(self):
        return '<Solved: {0.user} {0.problem}>' % self
