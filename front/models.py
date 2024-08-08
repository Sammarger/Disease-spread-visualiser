from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.forms import ModelForm
from django import forms
import pandas
import json
# Each class within models.py represents a table within the database

# Tables written in this format allow me to easily add, modify and delete records in the
# database all within python

# Table used for data collection from the web, including total cases, deaths and other
# measurable values
class deseaseDataSet(models.Model):
    country = models.CharField(max_length=100)
    total_cases = models.IntegerField(max_length=100)
    new_cases = models.CharField(max_length=100)
    total_deaths = models.IntegerField(max_length=20)
    new_deaths = models.CharField(max_length=20)
    total_recovered = models.IntegerField(max_length=20)
    new_recovered = models.CharField(max_length=20)

# Produces a list of valid postcodes that allows the program to check whether a users
# input cause errors in the database.
counties = pandas.read_json('london_postcode_geo.json')
validpostcodes = []
for i in counties['features']:
    name = i['properties']['Name']
    validpostcodes.append((name, name))

# Table for each symptom record input by a user
# Values such as user_id and date_set are automatically input when forms are submitted
# User_id requires a user to be logged in to fill
# models.CASCADE will cause the users posts to be deleted when a user is deleted
class usersymptoms(models.Model):
    date_set = models.DateField(default=timezone.now)
    temperature = models.FloatField(null=False)
    continuous_cough = models.BooleanField()
    loss_of_senses = models.BooleanField()
    infected_contact = models.BooleanField()
    postcode = models.CharField(max_length=4,choices=validpostcodes, default='N22')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    # get_absolute_url will cause the program to return to urlpattern 'front' automatically
    # when a form is submitted, returning user to the main menu
    def get_absolute_url(self):
        return reverse('front')

# Form model uses usersymptoms to create a form for the user

# When a user submits a form, server will process the data, check for errors,
# then add it to the usersymptom table
class usersymptom_form(ModelForm):
    class Meta:
        model = usersymptoms
        #Lists the required form field the user must input, the rest are automatically set
        fields = ['temperature', 'continuous_cough', 'loss_of_senses', 'infected_contact', 'postcode']


class user_covid_record(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    covid_record_postcode = models.ForeignKey(usersymptoms, related_name='usersymptoms_postcode', on_delete=models.CASCADE)
    covid_record_date = models.ForeignKey(usersymptoms, related_name='usersymptoms_date_set', on_delete=models.CASCADE)



